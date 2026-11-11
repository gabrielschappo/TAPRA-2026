import json
import logging
import os
from datetime import date, datetime, time, timezone
from time import sleep

import azure.functions as func
import pyodbc
from azure.storage.blob import BlobServiceClient, ContentSettings

app = func.FunctionApp()

# Agenda compartilhada por todas as extracoes: a cada 5 minutos, no segundo 0.
AGENDA_EXTRACAO = "0 */5 * * * *"

# Carga do banco de destino: uma vez por dia, as 06:30 UTC (03:30 em Brasilia).
AGENDA_CARGA = "0 30 6 * * *"

# Credenciais vem das variaveis de ambiente configuradas no Azure (App Settings).
# Origem: HOST, DATABASE, USER, PASSWORD | destino: as mesmas com prefixo DESTINO_
VARIAVEIS_CONEXAO = ["HOST", "DATABASE", "USER", "PASSWORD"]

# Destino no Data Lake: container bronze, organizado por fonte/entidade/data.
CONTAINER_BRONZE = "bronze"
FONTE = "itsm"

# Ordem que respeita as chaves estrangeiras do destino: maes antes das filhas.
ORDEM_CARGA = [
    "categoria",
    "cliente_organizacao",
    "fila",
    "sla",
    "analista",
    "solicitante",
    "chamado",
    "chamado_sla",
    "chamado_status_historico",
    "csat_avaliacao",
]


def obter_string_conexao(prefixo: str = "") -> str:
    variaveis = [prefixo + nome for nome in VARIAVEIS_CONEXAO]
    faltando = [nome for nome in variaveis if not os.environ.get(nome)]
    if faltando:
        raise RuntimeError(
            f"Variaveis de ambiente nao configuradas: {', '.join(faltando)}"
        )

    host, banco, usuario, senha = (os.environ[nome] for nome in variaveis)

    # Senha entre chaves para o ODBC aceitar caracteres especiais como ; = #
    senha = senha.replace("}", "}}")

    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={host};"
        f"DATABASE={banco};"
        f"UID={usuario};"
        f"PWD={{{senha}}};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )


def extrair_tabela(tabela: str) -> list:
    logging.info("[extract_%s] Iniciando extracao de itsm.%s", tabela, tabela)

    try:
        conexao = pyodbc.connect(obter_string_conexao())
        try:
            cursor = conexao.cursor()
            cursor.execute(f"SELECT * FROM itsm.{tabela}")

            colunas = [coluna[0] for coluna in cursor.description]
            registros = [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
        finally:
            conexao.close()

    except Exception as erro:
        logging.error("[extract_%s] Erro ao extrair itsm.%s: %s", tabela, tabela, erro)
        raise

    logging.info(
        "[extract_%s] %d registros extraidos de itsm.%s | colunas: %s",
        tabela,
        len(registros),
        tabela,
        ", ".join(colunas),
    )
    for registro in registros[:3]:
        logging.info("[extract_%s] amostra: %s", tabela, registro)

    return registros


# O JSON nao sabe representar datas nem Decimal: datas viram texto ISO 8601
# (ex: 2026-05-11T22:29:16) e o resto vira texto, sem perder precisao.
def serializar_valor(valor):
    if isinstance(valor, (date, time)):
        return valor.isoformat()
    return str(valor)


# itsm/<tabela>/ano=AAAA/mes=MM/dia=DD/<tabela>_AAAAMMDDTHHMMSSZ.json, sempre em UTC
def montar_caminho_bronze(tabela: str, momento: datetime) -> str:
    return (
        f"{FONTE}/{tabela}/"
        f"ano={momento:%Y}/mes={momento:%m}/dia={momento:%d}/"
        f"{tabela}_{momento:%Y%m%dT%H%M%SZ}.json"
    )


def obter_conexao_storage() -> str:
    conexao_storage = os.environ.get("DATALAKE_CONNECTION_STRING")
    if not conexao_storage:
        raise RuntimeError(
            "Variavel de ambiente nao configurada: DATALAKE_CONNECTION_STRING"
        )
    return conexao_storage


def salvar_na_bronze(tabela: str, registros: list) -> str:
    conexao_storage = obter_conexao_storage()

    caminho = montar_caminho_bronze(tabela, datetime.now(timezone.utc))
    conteudo = json.dumps(
        registros, default=serializar_valor, ensure_ascii=False, indent=2
    )

    try:
        servico = BlobServiceClient.from_connection_string(conexao_storage)
        arquivo = servico.get_blob_client(container=CONTAINER_BRONZE, blob=caminho)
        arquivo.upload_blob(
            conteudo.encode("utf-8"),
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json"),
        )
    except Exception as erro:
        logging.error("[extract_%s] Erro ao salvar na bronze: %s", tabela, erro)
        raise

    logging.info(
        "[extract_%s] %d registros salvos em %s/%s",
        tabela,
        len(registros),
        CONTAINER_BRONZE,
        caminho,
    )
    return caminho


# Pipeline de cada tabela: extrai do banco de origem e grava o JSON na bronze.
def extrair_e_salvar(tabela: str) -> None:
    registros = extrair_tabela(tabela)
    salvar_na_bronze(tabela, registros)


# O banco de destino e serverless: pausado, ele leva ~1 min para voltar e recusa as
# primeiras conexoes. Por isso tenta algumas vezes antes de desistir.
def conectar_com_retentativa(
    string_conexao: str, tentativas: int = 5, espera: int = 20
):
    for tentativa in range(1, tentativas + 1):
        try:
            return pyodbc.connect(string_conexao)
        except pyodbc.Error as erro:
            if tentativa == tentativas:
                raise
            logging.warning(
                "[carga_destino] Banco indisponivel (tentativa %d/%d), "
                "tentando de novo em %ds: %s",
                tentativa,
                tentativas,
                espera,
                erro,
            )
            sleep(espera)


# Le o arquivo mais recente da tabela na pasta de hoje da bronze. O nome termina com
# o horario (AAAAMMDDTHHMMSSZ), entao o maior nome e o mais recente.
def ler_ultimo_arquivo_bronze(container, tabela: str, dia: datetime) -> list:
    prefixo = f"{FONTE}/{tabela}/ano={dia:%Y}/mes={dia:%m}/dia={dia:%d}/"
    arquivos = [blob.name for blob in container.list_blobs(name_starts_with=prefixo)]
    if not arquivos:
        raise RuntimeError(f"Nenhum arquivo em {CONTAINER_BRONZE}/{prefixo}")

    ultimo = max(arquivos)
    logging.info("[carga_destino] %s <- %s/%s", tabela, CONTAINER_BRONZE, ultimo)
    return json.loads(container.download_blob(ultimo).readall())


# Insere em lotes de varias linhas por comando: o SQL Server aceita no maximo 2100
# parametros por comando, entao cada lote fica abaixo de 2000.
def inserir_registros(cursor, tabela: str, registros: list) -> None:
    if not registros:
        return

    colunas = list(registros[0])
    linha = "(" + ", ".join(["?"] * len(colunas)) + ")"
    linhas_por_lote = 2000 // len(colunas)

    for inicio in range(0, len(registros), linhas_por_lote):
        lote = registros[inicio : inicio + linhas_por_lote]
        comando = (
            f"INSERT INTO dbo.{tabela} ({', '.join(colunas)}) "
            f"VALUES {', '.join([linha] * len(lote))}"
        )
        cursor.execute(comando, [registro[col] for registro in lote for col in colunas])


# Recarga completa do destino numa unica transacao: apaga tudo (filhas antes das
# maes) e insere de novo (maes antes das filhas). Se qualquer passo falhar, o
# rollback desfaz tudo e o destino continua como estava, sem dados pela metade.
def carregar_banco_destino() -> None:
    servico = BlobServiceClient.from_connection_string(obter_conexao_storage())
    container = servico.get_container_client(CONTAINER_BRONZE)
    hoje = datetime.now(timezone.utc)
    dados = {
        tabela: ler_ultimo_arquivo_bronze(container, tabela, hoje)
        for tabela in ORDEM_CARGA
    }

    conexao = conectar_com_retentativa(obter_string_conexao("DESTINO_"))
    try:
        cursor = conexao.cursor()
        for tabela in reversed(ORDEM_CARGA):
            cursor.execute(f"DELETE FROM dbo.{tabela}")

        for tabela in ORDEM_CARGA:
            inserir_registros(cursor, tabela, dados[tabela])
            logging.info(
                "[carga_destino] %d registros carregados em dbo.%s",
                len(dados[tabela]),
                tabela,
            )

        conexao.commit()
    except Exception as erro:
        conexao.rollback()
        logging.error("[carga_destino] Carga desfeita (rollback): %s", erro)
        raise
    finally:
        conexao.close()

    total = sum(len(registros) for registros in dados.values())
    logging.info("[carga_destino] Carga concluida: %d registros em 10 tabelas", total)


@app.timer_trigger(
    schedule=AGENDA_EXTRACAO,
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_analista(myTimer: func.TimerRequest) -> None:
    extrair_e_salvar("analista")


@app.timer_trigger(
    schedule=AGENDA_EXTRACAO,
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_categoria(myTimer: func.TimerRequest) -> None:
    extrair_e_salvar("categoria")


@app.timer_trigger(
    schedule=AGENDA_EXTRACAO,
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_chamado(myTimer: func.TimerRequest) -> None:
    extrair_e_salvar("chamado")


@app.timer_trigger(
    schedule=AGENDA_EXTRACAO,
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_chamado_sla(myTimer: func.TimerRequest) -> None:
    extrair_e_salvar("chamado_sla")


@app.timer_trigger(
    schedule=AGENDA_EXTRACAO,
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_chamado_status_historico(myTimer: func.TimerRequest) -> None:
    extrair_e_salvar("chamado_status_historico")


@app.timer_trigger(
    schedule=AGENDA_EXTRACAO,
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_cliente_organizacao(myTimer: func.TimerRequest) -> None:
    extrair_e_salvar("cliente_organizacao")


@app.timer_trigger(
    schedule=AGENDA_EXTRACAO,
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_csat_avaliacao(myTimer: func.TimerRequest) -> None:
    extrair_e_salvar("csat_avaliacao")


@app.timer_trigger(
    schedule=AGENDA_EXTRACAO,
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_fila(myTimer: func.TimerRequest) -> None:
    extrair_e_salvar("fila")


@app.timer_trigger(
    schedule=AGENDA_EXTRACAO,
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_sla(myTimer: func.TimerRequest) -> None:
    extrair_e_salvar("sla")


@app.timer_trigger(
    schedule=AGENDA_EXTRACAO,
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_solicitante(myTimer: func.TimerRequest) -> None:
    extrair_e_salvar("solicitante")


# Carga diaria do banco de destino. use_monitor=True guarda a agenda no storage: se o
# app estiver fora do ar no horario, a carga roda assim que ele voltar.
@app.timer_trigger(
    schedule=AGENDA_CARGA,
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=True,
)
def carga_destino(myTimer: func.TimerRequest) -> None:
    carregar_banco_destino()
