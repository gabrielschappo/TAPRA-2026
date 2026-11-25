import os
from time import sleep

import mssql_python
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Dashboard ITSM | TAPRA 2026", layout="wide")

VARIAVEIS_CONEXAO = ["HOST", "DATABASE", "USER", "PASSWORD"]

COR_PRINCIPAL = "#2a78d6"
COR_ESTOURADO = "#d03b3b"

TIPOS = {
    "INCIDENT": "Incidente",
    "REQUEST": "Requisição",
    "PROBLEM": "Problema",
    "CHANGE": "Mudança",
    "TASK": "Tarefa",
}
STATUS = {
    "OPEN": "Aberto",
    "NEW": "Novo",
    "IN_PROGRESS": "Em andamento",
    "PENDING": "Pendente",
    "ON_HOLD": "Em espera",
    "WAITING": "Aguardando",
    "WAITING_CUSTOMER": "Aguardando cliente",
    "RESOLVED": "Resolvido",
    "CLOSED": "Fechado",
    "CANCELLED": "Cancelado",
    "CANCELED": "Cancelado",
}
PRIORIDADES = {"CRITICAL": "Crítica", "HIGH": "Alta", "MEDIUM": "Média", "LOW": "Baixa"}
MESES = "jan fev mar abr mai jun jul ago set out nov dez".split()

CONSULTAS = {
    "chamados": """
        SELECT c.id_chamado, c.nr_chamado, c.ds_tipo_chamado, c.ds_status_chamado,
               c.ds_prioridade, c.dt_criacao, c.dt_resolucao,
               a.nm_analista, f.nm_fila, cat.nm_categoria, co.nm_cliente_organizacao
        FROM dbo.chamado c
        LEFT JOIN dbo.analista a ON a.id_analista = c.id_analista_atual
        LEFT JOIN dbo.fila f ON f.id_fila = c.id_fila_atual
        LEFT JOIN dbo.categoria cat ON cat.id_categoria = c.id_categoria
        LEFT JOIN dbo.cliente_organizacao co
            ON co.id_cliente_organizacao = c.id_cliente_organizacao
    """,
    "sla": """
        SELECT cs.id_chamado, cs.fl_breach
        FROM dbo.chamado_sla cs
    """,
    "historico": """
        SELECT h.id_chamado, h.ds_status_chamado, h.qt_tempo_status_minutos
        FROM dbo.chamado_status_historico h
    """,
    "csat": """
        SELECT av.id_chamado, av.nr_score, a.nm_analista
        FROM dbo.csat_avaliacao av
        LEFT JOIN dbo.analista a ON a.id_analista = av.id_analista
    """,
}


def ler_configuracao(nome: str) -> str:
    try:
        if nome in st.secrets:
            return str(st.secrets[nome])
    except Exception:
        pass
    return os.environ.get(nome, "")


def obter_string_conexao() -> str:
    valores = {nome: ler_configuracao("DESTINO_" + nome) for nome in VARIAVEIS_CONEXAO}
    faltando = ["DESTINO_" + nome for nome, valor in valores.items() if not valor]
    if faltando:
        raise RuntimeError(f"Configuracao ausente: {', '.join(faltando)}")

    senha = valores["PASSWORD"].replace("}", "}}")
    return (
        f"Server={valores['HOST']};"
        f"Database={valores['DATABASE']};"
        f"UID={valores['USER']};"
        f"PWD={{{senha}}};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )


def conectar(tentativas: int = 5, espera: int = 20):
    string_conexao = obter_string_conexao()
    for tentativa in range(1, tentativas + 1):
        try:
            return mssql_python.connect(string_conexao, timeout=30)
        except mssql_python.Error:
            if tentativa == tentativas:
                raise
            sleep(espera)


def consultar(conexao, sql: str) -> pd.DataFrame:
    cursor = conexao.cursor()
    cursor.execute(sql)
    colunas = [coluna[0] for coluna in cursor.description]
    return pd.DataFrame.from_records(
        [tuple(linha) for linha in cursor], columns=colunas
    )


@st.cache_data(ttl=3600, show_spinner="Consultando o banco de destino...")
def carregar_dados() -> dict:
    conexao = conectar()
    try:
        return {nome: consultar(conexao, sql) for nome, sql in CONSULTAS.items()}
    finally:
        conexao.close()


def traduzir(serie: pd.Series, traducoes: dict) -> pd.Series:
    texto = serie.fillna("Não informado").astype(str)
    return texto.str.upper().map(traducoes).fillna(texto)


def preparar_chamados(chamados: pd.DataFrame) -> pd.DataFrame:
    chamados = chamados.copy()
    chamados["dt_criacao"] = pd.to_datetime(chamados["dt_criacao"])
    chamados["dt_resolucao"] = pd.to_datetime(chamados["dt_resolucao"])
    chamados["tipo"] = traduzir(chamados["ds_tipo_chamado"], TIPOS)
    chamados["status"] = traduzir(chamados["ds_status_chamado"], STATUS)
    chamados["prioridade"] = traduzir(chamados["ds_prioridade"], PRIORIDADES)
    chamados["analista"] = chamados["nm_analista"].fillna("Sem analista")
    chamados["fila"] = chamados["nm_fila"].fillna("Sem fila")
    chamados["categoria"] = chamados["nm_categoria"].fillna("Sem categoria")
    chamados["cliente"] = chamados["nm_cliente_organizacao"].fillna("Sem cliente")
    return chamados


def formatar_numero(valor: float, casas: int = 0) -> str:
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def ordem_prioridade(prioridades) -> list:
    conhecidas = [p for p in PRIORIDADES.values() if p in set(prioridades)]
    return conhecidas + sorted(set(prioridades) - set(conhecidas))


def estilizar(figura: go.Figure, altura: int) -> go.Figure:
    figura.update_layout(
        height=altura,
        margin=dict(l=8, r=24, t=8, b=8),
        separators=",.",
        bargap=0.35,
        showlegend=False,
    )
    figura.update_xaxes(showgrid=False)
    return figura


def mostrar(figura: go.Figure, altura: int) -> None:
    st.plotly_chart(
        estilizar(figura, altura), width="stretch", config={"displayModeBar": False}
    )


def barras_horizontais(
    serie: pd.Series, rotulo: str, casas: int = 0, ordenar: bool = True
) -> None:
    if ordenar:
        serie = serie.sort_values()
    formato = f"%{{x:,.{casas}f}}"
    figura = go.Figure(
        go.Bar(
            x=serie.values,
            y=serie.index,
            orientation="h",
            marker=dict(color=COR_PRINCIPAL, cornerradius=4),
            texttemplate=formato,
            textposition="outside",
            cliponaxis=False,
            hovertemplate=f"%{{y}}<br>{rotulo}: {formato}<extra></extra>",
        )
    )
    figura.update_xaxes(visible=False, range=[0, max(serie.max(), 1) * 1.15])
    figura.update_yaxes(title=None)
    mostrar(figura, 60 + 30 * len(serie))


def barras_verticais(serie: pd.Series, rotulo: str) -> None:
    figura = go.Figure(
        go.Bar(
            x=serie.index,
            y=serie.values,
            marker=dict(color=COR_PRINCIPAL, cornerradius=4),
            texttemplate="%{y}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=f"%{{x}}<br>{rotulo}: %{{y}}<extra></extra>",
        )
    )
    figura.update_xaxes(type="category", title=None)
    figura.update_yaxes(visible=False, range=[0, max(serie.max(), 1) * 1.15])
    mostrar(figura, 320)


def titulo(numero: int, texto: str) -> None:
    st.markdown(f"**{numero} · {texto}**")


# Cabecalho e carga dos dados
st.title("Dashboard de Chamados (ITSM)")
st.caption(
    "TAPRA 2026 - Gabriel Heidemann Schappo, Lucas Borges do Amaral e "
    "Vitor Tasca da Costa - Fonte: banco db-tapra-destino, atualizado "
    "diariamente pela Azure Function carga_destino"
)

try:
    dados = carregar_dados()
except Exception as erro:
    st.error(f"Não foi possível consultar o banco de destino: {erro}")
    st.info(
        "Confira se as variáveis DESTINO_HOST, DESTINO_DATABASE, DESTINO_USER e "
        "DESTINO_PASSWORD estão no .streamlit/secrets.toml e se o seu IP está "
        "liberado no firewall do servidor SQL (portal do Azure > servidor > Rede)."
    )
    st.stop()

chamados = preparar_chamados(dados["chamados"])

# Filtros
col_periodo, col_tipo, col_prioridade, col_cliente, col_botao = st.columns(
    [2, 2, 2, 2, 1], vertical_alignment="bottom"
)
inicio_dados = chamados["dt_criacao"].min().date()
fim_dados = chamados["dt_criacao"].max().date()
periodo = col_periodo.date_input(
    "Período de abertura",
    value=(inicio_dados, fim_dados),
    min_value=inicio_dados,
    max_value=fim_dados,
    format="DD/MM/YYYY",
)
tipos = col_tipo.multiselect(
    "Tipo", sorted(chamados["tipo"].unique()), placeholder="Todos"
)
prioridades = col_prioridade.multiselect(
    "Prioridade", ordem_prioridade(chamados["prioridade"]), placeholder="Todas"
)
clientes = col_cliente.multiselect(
    "Cliente", sorted(chamados["cliente"].unique()), placeholder="Todos"
)
if col_botao.button("Atualizar dados", width="stretch"):
    carregar_dados.clear()
    st.rerun()

filtro = pd.Series(True, index=chamados.index)
if len(periodo) == 2:
    data_criacao = chamados["dt_criacao"].dt.date
    filtro &= data_criacao.between(periodo[0], periodo[1])
if tipos:
    filtro &= chamados["tipo"].isin(tipos)
if prioridades:
    filtro &= chamados["prioridade"].isin(prioridades)
if clientes:
    filtro &= chamados["cliente"].isin(clientes)
chamados = chamados[filtro]

if chamados.empty:
    st.warning("Nenhum chamado encontrado com esses filtros.")
    st.stop()

ids = set(chamados["id_chamado"])
sla = dados["sla"][dados["sla"]["id_chamado"].isin(ids)]
historico = dados["historico"][dados["historico"]["id_chamado"].isin(ids)]
csat = dados["csat"][dados["csat"]["id_chamado"].isin(ids)]

# Indicadores principais
resolvidos = chamados.dropna(subset=["dt_resolucao"])
horas_resolucao = (
    resolvidos["dt_resolucao"] - resolvidos["dt_criacao"]
).dt.total_seconds() / 3600
estourou = sla["fl_breach"].fillna(False).astype(bool)

kpi1, kpi8, kpi11, kpi13, kpi15 = st.columns(5, border=True)
kpi1.metric("1 · Total de chamados", formatar_numero(len(chamados)))
kpi8.metric(
    "8 · Backlog (em aberto)",
    formatar_numero(chamados["dt_resolucao"].isna().sum()),
    help="Chamados sem data de resolução",
)
kpi11.metric(
    "11 · Tempo médio de resolução",
    (
        f"{formatar_numero(horas_resolucao.mean(), 1)} h"
        if len(horas_resolucao)
        else "-"
    ),
    help="Média de dt_resolucao - dt_criacao dos chamados resolvidos",
)
kpi13.metric(
    "13 · Dentro do SLA",
    f"{formatar_numero(100 * (~estourou).mean(), 1)}%" if len(sla) else "-",
    help="Chamados com fl_breach = 0",
)
kpi15.metric(
    "15 · Nota média de satisfação",
    f"{formatar_numero(csat['nr_score'].mean(), 2)} / 5" if len(csat) else "-",
    help=f"Média de {len(csat)} avaliações (escala de 1 a 5)",
)

aba_volume, aba_atendimento, aba_sla, aba_csat = st.tabs(
    ["Volume", "Atendimento", "SLA", "Satisfação"]
)

# Volume de chamados (2 a 7)
with aba_volume:
    titulo(2, "Chamados abertos por mês")
    mes = chamados["dt_criacao"].dt.to_period("M")
    por_mes = mes.value_counts().reindex(
        pd.period_range(mes.min(), mes.max(), freq="M"), fill_value=0
    )
    por_mes.index = [f"{MESES[p.month - 1]}/{p.year % 100:02d}" for p in por_mes.index]
    barras_verticais(por_mes, "Chamados")

    esquerda, direita = st.columns(2)
    with esquerda:
        titulo(3, "Chamados por tipo")
        barras_horizontais(chamados["tipo"].value_counts(), "Chamados")
        titulo(5, "Chamados por prioridade")
        por_prioridade = chamados["prioridade"].value_counts()
        ordem = ordem_prioridade(por_prioridade.index)
        barras_horizontais(
            por_prioridade.reindex(ordem[::-1]), "Chamados", ordenar=False
        )
    with direita:
        titulo(4, "Chamados por status")
        barras_horizontais(chamados["status"].value_counts(), "Chamados")

    esquerda, direita = st.columns(2)
    with esquerda:
        titulo(6, "Chamados por categoria")
        barras_horizontais(chamados["categoria"].value_counts(), "Chamados")
    with direita:
        titulo(7, "Chamados por cliente")
        barras_horizontais(chamados["cliente"].value_counts(), "Chamados")

# Atendimento e analistas (9, 10 e 12)
with aba_atendimento:
    esquerda, direita = st.columns(2)
    with esquerda:
        titulo(9, "Chamados × Analista")
        barras_horizontais(chamados["analista"].value_counts(), "Chamados")
    with direita:
        titulo(10, "Chamados por fila")
        barras_horizontais(chamados["fila"].value_counts(), "Chamados")
        titulo(12, "Tempo médio em cada status (horas)")
        if historico.empty:
            st.caption("Sem histórico de status para os filtros escolhidos.")
        else:
            horas_status = (
                historico.assign(
                    status=traduzir(historico["ds_status_chamado"], STATUS),
                    horas=historico["qt_tempo_status_minutos"] / 60,
                )
                .groupby("status")["horas"]
                .mean()
            )
            barras_horizontais(horas_status, "Horas", casas=1)

# SLA (13 e 14)
with aba_sla:
    titulo(14, "SLA estourado por prioridade")
    if sla.empty:
        st.caption("Sem registros de SLA para os filtros escolhidos.")
    else:
        sla_prioridade = (
            sla.assign(situacao=estourou.map({True: "Estourado", False: "Dentro"}))
            .merge(chamados[["id_chamado", "prioridade"]], on="id_chamado")
            .groupby(["prioridade", "situacao"])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=["Dentro", "Estourado"], fill_value=0)
        )
        sla_prioridade = sla_prioridade.reindex(ordem_prioridade(sla_prioridade.index))
        figura = go.Figure()
        for situacao, cor in [("Dentro", COR_PRINCIPAL), ("Estourado", COR_ESTOURADO)]:
            figura.add_bar(
                name=f"{situacao} do SLA" if situacao == "Dentro" else situacao,
                x=sla_prioridade.index,
                y=sla_prioridade[situacao],
                marker=dict(color=cor),
                texttemplate="%{y}",
                textposition="inside",
                hovertemplate=f"%{{x}}<br>{situacao}: %{{y}}<extra></extra>",
            )
        estilizar(figura, 360)
        figura.update_layout(
            barmode="stack",
            showlegend=True,
            legend=dict(orientation="h", y=1.08, x=0, traceorder="normal"),
            uniformtext=dict(minsize=10, mode="hide"),
        )
        figura.update_xaxes(type="category")
        figura.update_yaxes(visible=False)
        st.plotly_chart(figura, width="stretch", config={"displayModeBar": False})

        total = sla_prioridade.sum(axis=1)
        tabela = pd.DataFrame(
            {
                "Dentro do SLA": sla_prioridade["Dentro"],
                "Estourado": sla_prioridade["Estourado"],
                "Total": total,
                "% estourado": [
                    f"{formatar_numero(valor, 1)}%"
                    for valor in 100 * sla_prioridade["Estourado"] / total
                ],
            }
        ).rename_axis("Prioridade")
        st.dataframe(tabela, width="stretch")

# Satisfacao - CSAT (15 e 16)
with aba_csat:
    if csat.empty:
        st.caption("Sem avaliações de satisfação para os filtros escolhidos.")
    else:
        esquerda, direita = st.columns(2)
        with esquerda:
            titulo(15, "Distribuição das notas (1 a 5)")
            notas = (
                csat["nr_score"]
                .value_counts()
                .reindex(range(1, 6), fill_value=0)
                .rename(index=lambda nota: f"Nota {nota}")
            )
            barras_verticais(notas, "Avaliações")
        with direita:
            titulo(16, "Satisfação média por analista")
            por_analista = csat.assign(
                analista=csat["nm_analista"].fillna("Sem analista")
            ).groupby("analista")["nr_score"]
            barras_horizontais(por_analista.mean(), "Nota média", casas=1)
            st.caption(
                "Analistas com poucas avaliações podem ter médias extremas: "
                f"são {len(csat)} avaliações no total."
            )

with st.expander("Ver chamados filtrados"):
    st.dataframe(
        chamados[
            [
                "nr_chamado",
                "tipo",
                "status",
                "prioridade",
                "dt_criacao",
                "dt_resolucao",
                "analista",
                "fila",
                "categoria",
                "cliente",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
