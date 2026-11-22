# Drafts verificados — Worlds 2026

Consulta: 21/11/2026 (data do cliente). O último Worlds concluído é o Worlds 2026, cuja final foi disputada em 14/11/2026.

## Conteúdo de `data/worlds-drafts.json`

50 composições completas, uma por equipe/partida, com as cinco posições conforme as colunas do placar publicado. Os 50 conjuntos são distintos e contêm 80 campeões diferentes. Não foram alterados campeões nem corrigidas flex picks para posições “mais comuns”: por exemplo, Cassiopeia e Taliyah na bot lane e Camille no suporte são escolhas verificadas nos placares.

| Série | Registros | Campeões distintos na série | Fonte |
| --- | ---: | ---: | --- |
| GEN × BLG, final | 8 | 40 | https://lol2llm.com/en/esports/worlds-2026-final-results |
| BLG × T1, semifinal | 8 | 40 | https://lol2llm.com/en/esports/worlds-2026-knockout-stage-results |
| GEN × IG, semifinal | 6 | 30 | mesma página de mata-mata |
| T1 × KC, quartas | 8 | 40 | mesma página de mata-mata |
| BLG × DK, quartas | 6 | 30 | mesma página de mata-mata |
| GEN × LYON, quartas | 6 | 30 | mesma página de mata-mata |
| IG × TES, quartas | 8 | 40 | mesma página de mata-mata |

As páginas identificam a origem como dados oficiais de partidas do LoL Esports e cotejo com os placares da Leaguepedia. Os links primários citados são:

- https://lol.fandom.com/wiki/2026_Season_World_Championship/Main_Event/Scoreboards/Semifinals_and_Finals
- https://lol.fandom.com/wiki/2026_Season_World_Championship/Main_Event/Scoreboards/Quarterfinals

A consulta direta à Leaguepedia foi bloqueada nesta sessão; a transcrição usa as tabelas de picks da reportagem, não sua análise de IA. A final também foi cotejada com https://lolnow.gg/worlds-2026-final-blg-beat-gen-g/ .

O campo `style` é curadoria para o jogo (iniciação, controle, pickoff ou escalamento), não uma classificação oficial da partida. `champions` e posições são os picks reais da equipe indicada, e `source` mantém o link público correspondente.

## Assets oficiais

IDs dos 80 campeões foram conferidos contra o JSON oficial:

https://ddragon.leagueoflegends.com/cdn/16.22.1/data/en_US/champion.json

Resultado: todos os 80 IDs existem. Essa versão é necessária para campeões recentes, incluindo Locke, Yunara e Mel; o CDN 15.1.1 da primeira versão do jogo não cobre todos eles. Os IDs respeitam Data Dragon: `MonkeyKing`, `Chogath`, `KSante`, `JarvanIV`, `Kaisa`, `Renata`, `TwistedFate` etc.

## Garantia para duas alternativas por equipe em uma MD3

As séries `worlds-2026-final`, `worlds-2026-sf2`, `worlds-2026-qf4` e `worlds-2026-qf1` fornecem, cada uma, oito templates cujos conjuntos de campeões são pairwise disjuntos (40 campeões por série).

Algoritmo seguro: sortear um desses packs de oito templates para o confronto; oferecer quatro templates distintos por jogo, dois por técnico; bloquear apenas os dois templates selecionados quando o jogo começar. Sobram 8, 6 e 4 templates antes dos jogos 1, 2 e 3. Assim qualquer combinação das duas escolhas continua permitindo quatro alternativas no terceiro jogo, e nenhum campeão escolhido reaparece. Alternativas recusadas podem voltar porque não foram jogadas. Não misturar packs sem verificar compatibilidade por busca/backtracking.

As séries de três jogos têm somente seis templates e não garantem, sozinhas, quatro alternativas no terceiro jogo. São úteis para ampliar o catálogo com um seletor que faça backtracking e preserve o restante da MD3.
