-- Antes da V6, a tabela rating_presets podia conter notas antigas que substituíam
-- os 32 overalls oficiais. Elas continuam preservadas para auditoria, mas
-- ficam inativas até o administrador salvar novamente na revisão atual.
ALTER TABLE rating_presets ADD COLUMN revision INTEGER NOT NULL DEFAULT 0;
