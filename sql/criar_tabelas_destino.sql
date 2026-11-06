IF OBJECT_ID('dbo.analista', 'U') IS NULL
CREATE TABLE dbo.analista (
    id_analista             INT             NOT NULL,
    cd_analista             NVARCHAR(50)    NULL,
    nm_analista             NVARCHAR(200)   NULL,
    ds_email                NVARCHAR(255)   NULL,
    ds_nivel                NVARCHAR(20)    NULL,
    id_fila_atual           INT             NULL,
    fl_ativo                BIT             NULL,
    dt_inclusao             DATETIME2       NULL,
    dt_atualizacao          DATETIME2       NULL,
    nm_sistema_origem       NVARCHAR(50)    NULL,
    cd_registro_origem      NVARCHAR(100)   NULL,
    CONSTRAINT pk_analista PRIMARY KEY (id_analista)
);

IF OBJECT_ID('dbo.categoria', 'U') IS NULL
CREATE TABLE dbo.categoria (
    id_categoria            INT             NOT NULL,
    cd_categoria            NVARCHAR(50)    NULL,
    nm_categoria            NVARCHAR(200)   NULL,
    ds_descricao            NVARCHAR(500)   NULL,
    fl_ativo                BIT             NULL,
    dt_inclusao             DATETIME2       NULL,
    dt_atualizacao          DATETIME2       NULL,
    nm_sistema_origem       NVARCHAR(50)    NULL,
    cd_registro_origem      NVARCHAR(100)   NULL,
    CONSTRAINT pk_categoria PRIMARY KEY (id_categoria)
);

IF OBJECT_ID('dbo.chamado', 'U') IS NULL
CREATE TABLE dbo.chamado (
    id_chamado              INT             NOT NULL,
    nr_chamado              NVARCHAR(30)    NULL,
    ds_tipo_chamado         NVARCHAR(30)    NULL,
    ds_status_chamado       NVARCHAR(30)    NULL,
    ds_prioridade           NVARCHAR(30)    NULL,
    dt_criacao              DATETIME2       NULL,
    dt_resolucao            DATETIME2       NULL,
    dt_ultima_atualizacao   DATETIME2       NULL,
    id_analista_atual       INT             NULL,
    id_reporter             INT             NULL,
    id_categoria            INT             NULL,
    id_cliente_organizacao  INT             NULL,
    id_fila_atual           INT             NULL,
    ds_titulo               NVARCHAR(500)   NULL,
    ds_descricao            NVARCHAR(MAX)   NULL,
    dt_inclusao             DATETIME2       NULL,
    dt_atualizacao          DATETIME2       NULL,
    nm_sistema_origem       NVARCHAR(50)    NULL,
    cd_registro_origem      NVARCHAR(100)   NULL,
    CONSTRAINT pk_chamado PRIMARY KEY (id_chamado)
);

IF OBJECT_ID('dbo.chamado_sla', 'U') IS NULL
CREATE TABLE dbo.chamado_sla (
    id_chamado_sla              INT             NOT NULL,
    id_chamado                  INT             NULL,
    id_sla                      INT             NULL,
    fl_breach                   BIT             NULL,
    qt_tempo_restante_minutos   INT             NULL,
    qt_tempo_decorrido_minutos  INT             NULL,
    qt_meta_minutos             INT             NULL,
    dt_referencia               DATETIME2       NULL,
    dt_inclusao                 DATETIME2       NULL,
    dt_atualizacao              DATETIME2       NULL,
    nm_sistema_origem           NVARCHAR(50)    NULL,
    cd_registro_origem          NVARCHAR(100)   NULL,
    CONSTRAINT pk_chamado_sla PRIMARY KEY (id_chamado_sla)
);

IF OBJECT_ID('dbo.chamado_status_historico', 'U') IS NULL
CREATE TABLE dbo.chamado_status_historico (
    id_chamado_status_historico INT             NOT NULL,
    id_chamado                  INT             NULL,
    ds_status_chamado           NVARCHAR(30)    NULL,
    dt_inicio_status            DATETIME2       NULL,
    dt_fim_status               DATETIME2       NULL,
    qt_tempo_status_minutos     INT             NULL,
    id_analista_responsavel     INT             NULL,
    id_fila                     INT             NULL,
    dt_inclusao                 DATETIME2       NULL,
    dt_atualizacao              DATETIME2       NULL,
    nm_sistema_origem           NVARCHAR(50)    NULL,
    cd_registro_origem          NVARCHAR(100)   NULL,
    CONSTRAINT pk_chamado_status_historico PRIMARY KEY (id_chamado_status_historico)
);

IF OBJECT_ID('dbo.cliente_organizacao', 'U') IS NULL
CREATE TABLE dbo.cliente_organizacao (
    id_cliente_organizacao  INT             NOT NULL,
    cd_cliente_organizacao  NVARCHAR(50)    NULL,
    nm_cliente_organizacao  NVARCHAR(200)   NULL,
    nr_cnpj                 NVARCHAR(14)    NULL,
    fl_ativo                BIT             NULL,
    dt_inclusao             DATETIME2       NULL,
    dt_atualizacao          DATETIME2       NULL,
    nm_sistema_origem       NVARCHAR(50)    NULL,
    cd_registro_origem      NVARCHAR(100)   NULL,
    CONSTRAINT pk_cliente_organizacao PRIMARY KEY (id_cliente_organizacao)
);

IF OBJECT_ID('dbo.csat_avaliacao', 'U') IS NULL
CREATE TABLE dbo.csat_avaliacao (
    id_csat_avaliacao       INT             NOT NULL,
    id_chamado              INT             NULL,
    id_analista             INT             NULL,
    nr_score                INT             NULL,
    ds_comentario           NVARCHAR(1000)  NULL,
    dt_avaliacao            DATETIME2       NULL,
    dt_inclusao             DATETIME2       NULL,
    dt_atualizacao          DATETIME2       NULL,
    nm_sistema_origem       NVARCHAR(50)    NULL,
    cd_registro_origem      NVARCHAR(100)   NULL,
    CONSTRAINT pk_csat_avaliacao PRIMARY KEY (id_csat_avaliacao)
);

IF OBJECT_ID('dbo.fila', 'U') IS NULL
CREATE TABLE dbo.fila (
    id_fila                 INT             NOT NULL,
    cd_fila                 NVARCHAR(50)    NULL,
    nm_fila                 NVARCHAR(200)   NULL,
    ds_descricao            NVARCHAR(500)   NULL,
    fl_ativo                BIT             NULL,
    dt_inclusao             DATETIME2       NULL,
    dt_atualizacao          DATETIME2       NULL,
    nm_sistema_origem       NVARCHAR(50)    NULL,
    cd_registro_origem      NVARCHAR(100)   NULL,
    CONSTRAINT pk_fila PRIMARY KEY (id_fila)
);

IF OBJECT_ID('dbo.sla', 'U') IS NULL
CREATE TABLE dbo.sla (
    id_sla                  INT             NOT NULL,
    cd_sla                  NVARCHAR(50)    NULL,
    nm_sla                  NVARCHAR(200)   NULL,
    qt_meta_minutos         INT             NULL,
    ds_descricao            NVARCHAR(500)   NULL,
    fl_ativo                BIT             NULL,
    dt_inclusao             DATETIME2       NULL,
    dt_atualizacao          DATETIME2       NULL,
    nm_sistema_origem       NVARCHAR(50)    NULL,
    cd_registro_origem      NVARCHAR(100)   NULL,
    CONSTRAINT pk_sla PRIMARY KEY (id_sla)
);

IF OBJECT_ID('dbo.solicitante', 'U') IS NULL
CREATE TABLE dbo.solicitante (
    id_solicitante          INT             NOT NULL,
    cd_solicitante          NVARCHAR(50)    NULL,
    id_cliente_organizacao  INT             NULL,
    nm_solicitante          NVARCHAR(200)   NULL,
    ds_email                NVARCHAR(255)   NULL,
    ds_telefone             NVARCHAR(20)    NULL,
    fl_ativo                BIT             NULL,
    dt_inclusao             DATETIME2       NULL,
    dt_atualizacao          DATETIME2       NULL,
    nm_sistema_origem       NVARCHAR(50)    NULL,
    cd_registro_origem      NVARCHAR(100)   NULL,
    CONSTRAINT pk_solicitante PRIMARY KEY (id_solicitante)
);

SELECT t.TABLE_NAME AS tabela, COUNT(c.COLUMN_NAME) AS qt_colunas
FROM INFORMATION_SCHEMA.TABLES t
JOIN INFORMATION_SCHEMA.COLUMNS c
    ON c.TABLE_SCHEMA = t.TABLE_SCHEMA AND c.TABLE_NAME = t.TABLE_NAME
WHERE t.TABLE_SCHEMA = 'dbo' AND t.TABLE_TYPE = 'BASE TABLE'
GROUP BY t.TABLE_NAME
ORDER BY t.TABLE_NAME;
