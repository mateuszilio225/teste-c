# Rift Draft

Jogo de leilão de cartas do CBLOL, com identidade visual própria. Cinco posições, 50 moedas fictícias e campeonato para 2, 4 ou 8 equipes. Sem apostas, compras reais ou prêmios financeiros.

## O que foi implementado

- Sala online com convite por código, autenticação anônima por token e estado persistido em Cloudflare D1.
- Polling de 1,5 segundo; lances validados no servidor com controle de versão otimista para concorrência.
- Treino local com bots, identificado na interface e separado das salas online.
- Carta exclusiva por jogador, cinco posições obrigatórias, reserva de orçamento, dez segundos por lote e extensão de 2,5 segundos para lances tardios.
- Preenchimento de lotes sem lance por uma moeda entre equipes elegíveis, garantindo que todos os elencos fechem.
- Mata-mata com exatamente três jogos por confronto, incluindo o terceiro após 2 a 0.
- Duas opções de composição por equipe/jogo; escolhas ocultas até a confirmação. Nenhum campeão usado por qualquer lado reaparece na mesma série.
- Micro/macro/mental, estilos com pesos diferentes, vantagem entre estilos, sorteio probabilístico e penalidades de rendimento após derrotas.
- Sala de espera, catálogo com busca/filtros, detalhes de cartas e fontes, animação de partida, resultados, chave e campeã.
- Salvamento de sessão no navegador e retomada. Salas expiram após 24 horas; não há recuperação de token em outro aparelho.

## Dados e critério

44 jogadores que atuaram no CBLOL 2026 Split 2. Dados de fase regular e playoffs congelados em 21/11/2026. Os arquivos CSV preservam os valores consultados e o script `scripts/ratings.mjs` gera as notas, com percentis por posição e redução do efeito de amostras pequenas.

Fontes:

- https://gol.gg/players/list/season-ALL/split-ALL/tournament-CBLOL%202026%20Split%202/
- https://gol.gg/players/list/season-ALL/split-ALL/tournament-CBLOL%202026%20Split%202%20Playoffs/
- https://maisesports.com.br/cblol-2026-veja-o-que-mudou-nas-escalacoes-dos-times-para-o-2-split
- https://liquipedia.net/leagueoflegends/CBLOL/2026/Split_2/Player_Stats (corroboração de Shini e posições)

Os atributos são estimativas de jogo, não notas oficiais. Mental é uma aproximação de consistência via mortes/KDA e não uma avaliação psicológica. As médias da fonte são arredondadas. A metodologia completa aparece no jogo. Cada campeão que combina com o arquétipo escolhido soma 0,6 ponto de coesão (até +3). Os grupos são curadoria para a simulação, não notas oficiais; não há força de patch ou proficiência individual. O estilo também muda os pesos dos atributos e interage com o estilo adversário.

## Desenvolvimento

Node 24+ para testes e prévia (usa `node:sqlite`), sem dependências de npm.

```sh
npm run check
npm run build
npm run dev
```

No ambiente gerenciado, iniciar a prévia exclusivamente com `sites-preview start /workspace/sites/rift-leilao`. O build incorpora assets, motor e API em `dist/server/index.js`. O servidor usa o binding `DB`. As tabelas estão em `drizzle/0000_rooms.sql`.

O modo treino roda localmente. O online usa o mesmo motor no servidor; tokens e estado futuro não são enviados a outros técnicos. O navegador nunca fornece a própria pontuação ou resultado de partida.

## Limites

- Salas de 2, 4 ou 8 equipes, uma sessão de técnico por navegador. Abas do mesmo navegador reaproveitam a identidade daquela sala.
- Não é WebSocket: a atualização é por consultas curtas; relógio visual usa o desvio em relação ao servidor.
- Etapas expiradas são processadas na próxima consulta. Não há cron ou avanço contínuo de todas as fases com todas as abas fechadas.
- Sem login, chat, liga persistente entre campeonatos ou troca de jogadores comprados.
- A escolha automática evita travar o draft se alguém se desconectar. O criador pode encerrar lotes, pular animações e avançar resultados para agilizar.
- Interface responsiva, mas aparelhos físicos e carga de muitos campeonatos simultâneos não foram testados.

## Créditos

Projeto de fã independente de Riot Games, CBLOL e 100pracada. Mecânica inspirada no leilão da referência, com código, textos e visual próprios. League of Legends e campeões pertencem à Riot Games; imagens via Data Dragon. DM Sans com licença OFL em `public/OFL-dm-sans.txt`.
