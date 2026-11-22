# Verificação da revisão 3 — modos de jogo

## Testes automatizados atuais

- [x] 44 cartas, fotos reais locais e proveniência por identidade.
- [x] Mercados exato, exato +12 e completo para 2/4/8 equipes, sem duplicatas e com todas as posições disponíveis.
- [x] Lote sem lance não contrata, não cobra e permite nova oferta.
- [x] Apenas vencedor do leilão recebe carta; reserva de orçamento e proteção de lote expirado.
- [x] Oito equipes compram40cartas exclusivas sem orçamento negativo.
- [x] MD3 para em dois triunfos; séries2–0 não têm terceiro jogo.
- [x] Drafts reais e packs Fearless completos, sem repetição dos campeões escolhidos.
- [x] Duas alternativas adversárias públicas, índice da escolha adversária oculto.
- [x] Liga, liga+playoffs e grupos+playoffs completos com campeão, calendário único e tabela coerente.
- [x] Eventos variados, cronologia ordenada, regiões diferentes, larvas/dragões/Barão e Ancião em jogos longos.
- [x] API em SQLite real: sessão, compra, sincronização e concorrência.

## Mecânico: regras e sincronização

- [x] 25 testes automatizados passaram, incluindo regressão do Automático.
- [x] Ordens escondidas por técnico; confirmação simultânea com resultado independente da ordem de envio.
- [x] API com duas sessões reais, persistência em SQLite/D1 compatível e conflito de versão resolvido sem dupla execução.
- [x] Validação de coordenadas, cinco posições, ouro, itens, alvo visível e alcance de sentinela.
- [x] Viagem limitada; proteção e fogo cruzado alteram dano e independem da ordem das unidades.
- [x] Névoa e última visão; espectador não recebe posições secretas durante o planejamento.
- [x] Replay só entrega os frames já alcançados; resultado e placar futuro ficam ocultos.
- [x] Captura contestada bloqueada; quórum de objetivos e pressão de torres aplicados.
- [x] Nexus destruído tem prioridade; empate exato abre rodada extra.
- [x] MD3 Mecânica completa com campeão, resultados específicos e Fearless preservado.
- [x] Chrome público: criação de treino Mecânico, leilão, escolha de draft, compra de botas, chamada para dragão, execução e nova rodada com item pago uma vez.

- [x] Duas sessões no D1 publicado completaram MD3 Mecânica com 20 rodadas, ordens privadas, replay progressivo, objetivos reais do estado, fim em dois triunfos, Fearless e reconexão. Relatório: `reports/published-mechanical-smoke.json`.

## Publicação e interface

- [x] Teste HTTP de duas sessões no D1 hospedado da revisão2: sala, configurações, lote sem lance sem cobrança, compras sincronizadas, alternativas adversárias públicas com escolha oculta, MD3 até dois triunfos, Fearless e reconexão.
- [x] Chrome público: tema escuro, fotos, escolha do mercado e formato, overall oculto, compras até fechar line-up, duas opções adversárias, consulta às duas line-ups e simulação com objetivos.
- [ ] Reprodução de sons em dispositivo físico e conferência móvel física.
- [ ] Carga de muitos campeonatos simultâneos.

Relatório da publicação anterior foi arquivado como `reports/published-smoke-v1.json`. A revisão2 foi validada online e está registrada em `reports/published-smoke.json`. A regressão automática foi repetida no servidor público após a publicação do Mecânico. O teste mecânico hospedado tem relatório próprio em `reports/published-mechanical-smoke.json`. O preview gerenciado não abriu a porta 4173; a conferência visual foi feita no site publicado.
