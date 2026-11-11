IF OBJECT_ID('dbo.fk_analista_fila', 'F') IS NULL
    ALTER TABLE dbo.analista ADD CONSTRAINT fk_analista_fila
        FOREIGN KEY (id_fila_atual) REFERENCES dbo.fila (id_fila);

IF OBJECT_ID('dbo.fk_solicitante_cliente_organizacao', 'F') IS NULL
    ALTER TABLE dbo.solicitante ADD CONSTRAINT fk_solicitante_cliente_organizacao
        FOREIGN KEY (id_cliente_organizacao) REFERENCES dbo.cliente_organizacao (id_cliente_organizacao);

IF OBJECT_ID('dbo.fk_chamado_analista', 'F') IS NULL
    ALTER TABLE dbo.chamado ADD CONSTRAINT fk_chamado_analista
        FOREIGN KEY (id_analista_atual) REFERENCES dbo.analista (id_analista);

IF OBJECT_ID('dbo.fk_chamado_solicitante', 'F') IS NULL
    ALTER TABLE dbo.chamado ADD CONSTRAINT fk_chamado_solicitante
        FOREIGN KEY (id_reporter) REFERENCES dbo.solicitante (id_solicitante);

IF OBJECT_ID('dbo.fk_chamado_categoria', 'F') IS NULL
    ALTER TABLE dbo.chamado ADD CONSTRAINT fk_chamado_categoria
        FOREIGN KEY (id_categoria) REFERENCES dbo.categoria (id_categoria);

IF OBJECT_ID('dbo.fk_chamado_cliente_organizacao', 'F') IS NULL
    ALTER TABLE dbo.chamado ADD CONSTRAINT fk_chamado_cliente_organizacao
        FOREIGN KEY (id_cliente_organizacao) REFERENCES dbo.cliente_organizacao (id_cliente_organizacao);

IF OBJECT_ID('dbo.fk_chamado_fila', 'F') IS NULL
    ALTER TABLE dbo.chamado ADD CONSTRAINT fk_chamado_fila
        FOREIGN KEY (id_fila_atual) REFERENCES dbo.fila (id_fila);

IF OBJECT_ID('dbo.fk_chamado_sla_chamado', 'F') IS NULL
    ALTER TABLE dbo.chamado_sla ADD CONSTRAINT fk_chamado_sla_chamado
        FOREIGN KEY (id_chamado) REFERENCES dbo.chamado (id_chamado);

IF OBJECT_ID('dbo.fk_chamado_sla_sla', 'F') IS NULL
    ALTER TABLE dbo.chamado_sla ADD CONSTRAINT fk_chamado_sla_sla
        FOREIGN KEY (id_sla) REFERENCES dbo.sla (id_sla);

IF OBJECT_ID('dbo.fk_chamado_status_historico_chamado', 'F') IS NULL
    ALTER TABLE dbo.chamado_status_historico ADD CONSTRAINT fk_chamado_status_historico_chamado
        FOREIGN KEY (id_chamado) REFERENCES dbo.chamado (id_chamado);

IF OBJECT_ID('dbo.fk_chamado_status_historico_analista', 'F') IS NULL
    ALTER TABLE dbo.chamado_status_historico ADD CONSTRAINT fk_chamado_status_historico_analista
        FOREIGN KEY (id_analista_responsavel) REFERENCES dbo.analista (id_analista);

IF OBJECT_ID('dbo.fk_chamado_status_historico_fila', 'F') IS NULL
    ALTER TABLE dbo.chamado_status_historico ADD CONSTRAINT fk_chamado_status_historico_fila
        FOREIGN KEY (id_fila) REFERENCES dbo.fila (id_fila);

IF OBJECT_ID('dbo.fk_csat_avaliacao_chamado', 'F') IS NULL
    ALTER TABLE dbo.csat_avaliacao ADD CONSTRAINT fk_csat_avaliacao_chamado
        FOREIGN KEY (id_chamado) REFERENCES dbo.chamado (id_chamado);

IF OBJECT_ID('dbo.fk_csat_avaliacao_analista', 'F') IS NULL
    ALTER TABLE dbo.csat_avaliacao ADD CONSTRAINT fk_csat_avaliacao_analista
        FOREIGN KEY (id_analista) REFERENCES dbo.analista (id_analista);

-- Conferencia: as 14 chaves estrangeiras criadas
SELECT
    fk.name                                   AS chave,
    OBJECT_NAME(fk.parent_object_id)          AS tabela_filha,
    OBJECT_NAME(fk.referenced_object_id)      AS tabela_mae
FROM sys.foreign_keys fk
ORDER BY tabela_filha, chave;
