# Verificação

- [x] Sintaxe do cliente, API e artefato Worker.
- [x] Catálogo de 44 cartas, posições válidas e limites das notas.
- [x] Leilão completo de oito equipes: 40 cartas exclusivas, cinco posições por equipe e preservação do orçamento.
- [x] Reserva de moedas, lances inválidos e rejeição de auto incremento do líder.
- [x] Campeonato de quatro equipes até a campeã, exatamente três jogos por confronto e 30 campeões distintos por série.
- [x] Ocultação do RNG, escolha adversária e resultado futuro no estado público.
- [x] Efeito de mental após derrota e ocorrência de vitórias do azarão.
- [x] API em SQLite real: criação, entrada, sessão, sincronização de lances, reconexão, permissões e concorrência otimista.
- [x] Chrome na versão pública: home, sala online, lance e compra, transição para draft, escolha, simulação, resultado e queda de rendimento após derrota.
- [x] Banco D1 hospedado: duas sessões HTTP independentes, lances sincronizados, fechamento de line-ups, três jogos, 30 campeões sem repetição, campeã e reconexão (`reports/published-smoke.json`).
- [ ] Aparelhos físicos e carga.

A prévia gerenciada não abriu o relay da porta 4173. Não foi iniciado servidor alternativo nem instalado navegador. A publicação pública abriu sem conta em nova aba; a aba antiga reteve a tela de login em cache. A conferência visual foi feita na publicação. O teste com duas sessões usou clientes HTTP e D1 hospedado; não duas pessoas em aparelhos físicos.
