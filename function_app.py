import logging

import datetime
import azure.functions as func
import os
import pyodbc

app = func.FunctionApp()

@app.timer_trigger(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def extract_chamado(myTimer: func.TimerRequest) -> None:

    #capturar variaveis de ambiente
    host_sql = os.getenv("HOST")
    database_sql = os.getenv("DATABASE")
    user_sql = os.getenv("USER")
    pass_sql = os.getenv("PASSWORD")

    #como montar uma string de conexao com PYODBC  AZURE DATABASE SQL
    conn_str_source = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={host_sql};"
            f"DATABASE={database_sql};"
            f"UID={user_sql};"
            f"PWD={pass_sql};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )

    # Abrir a conexão 
    # fazer uma select em qualquer tabela ex: itsm.chamado
    # imprimir usando logging

    conn = None
    try:
        conn = pyodbc.connect(conn_str_source)
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 10 * FROM itsm.chamado")

        colunas = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            logging.info(dict(zip(colunas, row)))

        logging.info("Consulta finalizada com sucesso.")
    except pyodbc.Error as e:
        logging.error(f"Erro ao consultar o banco: {e}")
        raise
    finally:
        if conn:
            conn.close()