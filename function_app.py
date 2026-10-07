import logging
import os

import azure.functions as func
import pyodbc

app = func.FunctionApp()

# Agenda compartilhada por todas as extracoes: todo minuto, no segundo 0.
AGENDA_EXTRACAO = "0 * * * * *"

# Credenciais vem das variaveis de ambiente configuradas no Azure (App Settings).
VARIAVEIS_CONEXAO = ["HOST", "DATABASE", "USER", "PASSWORD"]


def obter_string_conexao() -> str:
    faltando = [nome for nome in VARIAVEIS_CONEXAO if not os.environ.get(nome)]
    if faltando:
        raise RuntimeError(f"Variaveis de ambiente nao configuradas: {', '.join(faltando)}")

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
    logging.info('[extract_%s] Iniciando extracao de itsm.%s', tabela, tabela)

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
        logging.error('[extract_%s] Erro ao extrair itsm.%s: %s', tabela, tabela, erro)
        raise

    logging.info('[extract_%s] %d registros extraidos de itsm.%s | colunas: %s',
                 tabela, len(registros), tabela, ', '.join(colunas))
    for registro in registros[:3]:
        logging.info('[extract_%s] amostra: %s', tabela, registro)

    return registros


@app.timer_trigger(schedule=AGENDA_EXTRACAO, arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def extract_analista(myTimer: func.TimerRequest) -> None:
    extrair_tabela("analista")


@app.timer_trigger(schedule=AGENDA_EXTRACAO, arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def extract_categoria(myTimer: func.TimerRequest) -> None:
    extrair_tabela("categoria")


@app.timer_trigger(schedule=AGENDA_EXTRACAO, arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def extract_chamado(myTimer: func.TimerRequest) -> None:
    extrair_tabela("chamado")


@app.timer_trigger(schedule=AGENDA_EXTRACAO, arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def extract_chamado_sla(myTimer: func.TimerRequest) -> None:
    extrair_tabela("chamado_sla")


@app.timer_trigger(schedule=AGENDA_EXTRACAO, arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def extract_chamado_status_historico(myTimer: func.TimerRequest) -> None:
    extrair_tabela("chamado_status_historico")


@app.timer_trigger(schedule=AGENDA_EXTRACAO, arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def extract_cliente_organizacao(myTimer: func.TimerRequest) -> None:
    extrair_tabela("cliente_organizacao")


@app.timer_trigger(schedule=AGENDA_EXTRACAO, arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def extract_csat_avaliacao(myTimer: func.TimerRequest) -> None:
    extrair_tabela("csat_avaliacao")


@app.timer_trigger(schedule=AGENDA_EXTRACAO, arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def extract_fila(myTimer: func.TimerRequest) -> None:
    extrair_tabela("fila")
