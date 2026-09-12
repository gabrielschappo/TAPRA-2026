import logging
import os

import azure.functions as func
import requests

app = func.FunctionApp()

# URL base usada pelo timer para chamar a HTTP function.
# O runtime define WEBSITE_HOSTNAME nos dois cenarios: no Azure vem o dominio do app
# (ex: meu-app.azurewebsites.net, via https) e no func start vem localhost:7071 (http).
def obter_base_url() -> str:
    if os.environ.get("FUNCTION_BASE_URL"):
        return os.environ["FUNCTION_BASE_URL"]

    hostname = os.environ.get("WEBSITE_HOSTNAME", "localhost:7071")
    esquema = "http" if hostname.startswith("localhost") else "https"

    return f"{esquema}://{hostname}"


# 1) Timer trigger - imprime apenas um log no terminal.
@app.timer_trigger(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def timer_log(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('[timer_log] O timer esta atrasado!')

    logging.info('[timer_log] Timer executado com sucesso - equipe TAPRA-2026.')


# 2) HTTP trigger - recebe um parametro via URL (GET) e imprime esse parametro na tela.
@app.route(route="parametro", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def http_parametro(req: func.HttpRequest) -> func.HttpResponse:
    parametro = req.params.get('parametro')

    if not parametro:
        logging.warning('[http_parametro] Nenhum parametro informado na URL.')
        return func.HttpResponse(
            "Informe um parametro na URL. Exemplo: /api/parametro?parametro=TAPRA",
            status_code=400
        )

    logging.info('[http_parametro] Parametro recebido: %s', parametro)
    return func.HttpResponse(f"Parametro recebido: {parametro}", status_code=200)


# 3) HTTP trigger chamado pelo timer - devolve a informacao recebida mais um texto que identifica quem respondeu.
@app.route(route="eco", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def http_eco(req: func.HttpRequest) -> func.HttpResponse:
    mensagem = req.params.get('mensagem', 'sem mensagem')

    logging.info('[http_eco] Mensagem recebida: %s', mensagem)
    return func.HttpResponse(
        f"[http_eco respondeu] Recebi a mensagem: '{mensagem}' - Equipe TAPRA-2026",
        status_code=200
    )


# 4) Timer trigger - faz uma chamada HTTP para a function http_eco e loga a resposta.
@app.timer_trigger(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def timer_chama_http(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('[timer_chama_http] O timer esta atrasado!')

    url = f"{obter_base_url()}/api/eco"
    mensagem = "chamada disparada pelo timer_chama_http"

    logging.info('[timer_chama_http] Chamando %s', url)

    try:
        resposta = requests.get(url, params={"mensagem": mensagem}, timeout=10)
        logging.info('[timer_chama_http] Status: %s | Resposta: %s',
                     resposta.status_code, resposta.text)
    except requests.RequestException as erro:
        logging.error('[timer_chama_http] Falha ao chamar a function: %s', erro)
