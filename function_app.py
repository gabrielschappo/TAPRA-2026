import json
import logging
import os
from datetime import date, datetime, time, timezone

import azure.functions as func
import pyodbc
from azure.storage.blob import BlobServiceClient, ContentSettings

app = func.FunctionApp()

# Agenda compartilhada por todas as extracoes: a cada 5 minutos, no segundo 0.
AGENDA_EXTRACAO = "0 */5 * * * *"

# Credenciais vem das variaveis de ambiente configuradas no Azure (App Settings).
VARIAVEIS_CONEXAO = ["HOST", "DATABASE", "USER", "PASSWORD"]

# Destino no Data Lake: container bronze, organizado por fonte/entidade/data.
CONTAINER_BRONZE = "bronze"
FONTE = "itsm"


def obter_string_conexao() -> str:
    faltando = [nome for nome in VARIAVEIS_CONEXAO if not os.environ.get(nome)]
    if faltando:
        raise RuntimeError(
            f"Variaveis de ambiente nao configuradas: {', '.join(faltando)}"
        )

    # Senha entre chaves para o ODBC aceitar caracteres especiais como ; = #
    senha = os.environ["PASSWORD"].replace("}", "}}")

    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.environ['HOST']};"
        f"DATABASE={os.environ['DATABASE']};"
        f"UID={os.environ['USER']};"
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


def salvar_na_bronze(tabela: str, registros: list) -> str:
    conexao_storage = os.environ.get("DATALAKE_CONNECTION_STRING")
    if not conexao_storage:
        raise RuntimeError(
            "Variavel de ambiente nao configurada: DATALAKE_CONNECTION_STRING"
        )

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
