# Rift Draft

Jogo independente inspirado em **Footlobby**. Leilão de jogadores do CBLOL com 50 moedas fictícias, cinco posições, 43 fotos de jogadores, 86 drafts reais (Worlds 2026 + CBLOL 2026 Split 2) e séries melhor de três.

Site: https://rift-draft-br2002.wrydingo.chatgpt.site/
Código: https://github.com/mateuszilio225/teste-c/tree/rift-draft


## Novidades de 22/11/2026

### Ranking progressivo

- O cabeçalho mostra `vitórias - derrotas`, divisão atual, PDL e total de campeonatos ganhos.
- A progressão começa em **Bronze IV**, segue Ferro → Bronze → Prata → Ouro → Platina → Esmeralda → Diamante → Mestre → Grão-Mestre → Desafiante, com IV a I e 100 PDL por divisão para as primeiras sete ligas.
- Vitórias dão **18/22/25 PDL** em campeonatos de 2/4/8. Vice perde apenas **5 PDL** nos de 4/8; eliminações nas fases iniciais perdem mais. Em 1x1 o vice perde 12.
- A recompensa aparece na tela ao encerrar o campeonato e os resultados são registrados apenas uma vez por sala. Histórico, recorde e divisão permanecem no **localStorage** deste navegador, vinculados ao nome da equipe. **Não** há conta autenticada nem sincronização entre navegadores e aparelhos.

### Administração segura das notas

- Na sala (lobby ou leilão), o **criador** abre o botão `⚙ Ajustar OVR`, altera a nota de qualquer jogador de 40 a 99 e pode conceder/revogar a função de editor a qualquer equipe **humana já conectada à sala**.
- O servidor verifica a identidade do membro pelo token secreto da sala: **conhecer ou digitar o nickname de outro técnico não basta para obter permissão**.
- Notas customizadas são persistidas no **estado daquela sala**; afetam micro/macro/mental, preço de referência e força da equipe nesta sala. Após o leilão os valores travam. **Não** altera o banco oficial nem outras salas.

### Composições reais da CBLOL

Incluímos quatro séries de playoffs do Split 2, com os cinco campeões por função e link de fonte original:

- Final LØS x FURIA de 10/10/2026 — 10 drafts (5 mapas).
- LØS x FURIA de 12/09/2026 — 8 drafts (4 mapas).
- LOUD x paiN de 13/09/2026 — 8 drafts (4 mapas).
- FURIA x RED de 26/09/2026 — 10 drafts (5 mapas).

Os picks e a função vêm de scoreboards publicados. Os arquétipos de composição (`engage`, `control`, `pick`, `scale`) são estimativas editoriais e não classificações oficiais da Riot. Fontes em `research/cblol-2026-sources.md`.

## Leilão

- **Nenhuma carta entra automaticamente no time.** Só o maior lance confirmado compra. Lote sem lance volta ao mercado sem cobrar ninguém.
- Criador escolhe mercado exato (equipes × 5), exato +12 ou todos os 43 nomes. +12 é limitado ao catálogo; o total real aparece antes de iniciar. Cada posição tem oferta suficiente.
- Cada carta só pode ser comprada uma vez. Dez segundos por lote inicial e exatamente 3 segundos **novos** após qualquer lance, reserva de uma moeda por vaga restante.
- Proteção contra lance atrasado comprar outra carta. Bots fazem lances e também precisam comprar suas cinco cartas.
- Durante o leilão, o painel da concorrência revela as 5 posições e as cartas contratadas por cada equipe.
- Botão Mercado permite consultar cartas restantes e o criador recolocar uma carta em um lote sem lances.
- Opção de esconder overall, atributos e preço de referência no leilão, inclusive no catálogo e nos detalhes da carta.

## Campeonato e draft

- Mata-mata; pontos corridos; liga com playoffs; grupos com mata-mata. Salas para 2, 4 ou 8 equipes.
- Todos contra todos uma vez nas ligas. 3 pontos por MD3 vencida. Desempates: saldo de jogos, jogos vencidos, ordem do sorteio inicial.
- Liga + playoffs: 4 de 8 ou 2 de 4 avançam. Grupos: duas chaves; 8 equipes classificam duas por grupo com semifinais cruzadas; 4 equipes classificam uma por grupo para a final.
- **Melhor de três real:** termina em 2–0 ou 2–1, sem terceiro jogo após 2–0.
- Na configuração da sala há três origens de composição: **CBLOL 2026**, **Worlds 2026** ou **misto**. Em cada MD3 o servidor sorteia um pack Fearless compatível da seleção; há duas alternativas reais por lado e **10 segundos** para cada técnico escolher. Line-ups e alternativas adversárias são visíveis; a escolha exata é escondida até o início do jogo.
- Base com 50 drafts Worlds e 36 drafts CBLOL, com fonte por cartão. Oito packs de 8 a 10 drafts disjuntos garantem quatro opções compatíveis em cada jogo da MD3. Só campeões escolhidos ficam bloqueados; alternativas não escolhidas podem voltar.
- Consequências de mental após derrotas, recuperação após vitória e reset em cada nova MD3.

## Dois modos de partida

Escolha **Automático** ou **Mecânico** no formulário de criação ou no lobby. Salas antigas continuam no Automático.

O Automático preserva a simulação com probabilidades. O Mecânico é um jogo tático pausado, com regras próprias, sem sorteio do vencedor:

- Cinco unidades, destinos no mapa por clique/toque ou botões acessíveis, posturas de farm, iniciar, poke, proteger e recuar. Chamadas rápidas movem o time para objetivos ou dividem as rotas.
- 60 segundos de planejamento; ambas as ordens privadas executam simultaneamente em seis passos. Replays de 6,5 segundos mostram posições e vida progressivamente, sem entregar o futuro.
- Viagem base de 25,8 unidades por rodada. Alcance, superioridade numérica, fogo cruzado (+15%) e proteção próxima (−25%) influenciam o combate. Ataques e movimentos são determinísticos.
- Visão limitada, últimas posições conhecidas e uma sentinela por rodada. Bots consultam a mesma visão e não leem planos inimigos.
- Quatro de ouro por campeão no início. Farm, abates e objetivos financiam seis tipos de item; três espaços permanentes, compras validadas no servidor. Armadura e resistência mágica têm respostas distintas.
- Larvas/dragão exigem dois aliados, Barão (R7+) e Ancião (R13+) três. Inimigo vivo no covil bloqueia captura. Rotas acumulam pressão para torres. Objetivos e torres geram pontos e abrem dano ao Nexus.
- Vence ao destruir o Nexus; caso contrário, por pontos na R16. Desempate por Nexus e vida; igualdade exata abre mais uma rodada, sem sorteio ou vantagem de lado.
- Micro influencia dano em até ±3%; macro, visão em até ±1; efeito de derrotas/mental limitado a 2% no dano. Ninguém falha uma ordem por sorte.
- Relato e histórico explicam capturas, contestação, ausência de aliados, abates, proteção e fogo cruzado. MD3 e Fearless valem nos dois modos.

É uma abstração tática de LoL: os campeões do draft usam perfis por função e bônus do estilo da composição, sem reproduzir todos os kits e números do patch. Equilíbrio competitivo ainda depende de partidas e ajustes com jogadores reais.

## Apresentação

Novo tema escuro em violeta, azul-noite, ciano, dourado e coral, 43 fotos de jogadores e seleção de campeões animada. **Sem música**: apenas efeitos sintetizados de lance, lance rival, lance coberto, venda, escolha de draft, objetivos, campeão e aviso de contagem regressiva. Os sons começam após interação e podem ser desativados.

Simulações fictícias variam cronologia, ganks, invasões, disputas de visão, contraganks, teleporte, iscas no Barão, recompensas, lutas em rotas e selvas, larvas, dragões, Arauto, Barão, roubos, pressão lateral e Ancião em jogos longos. O mapa acompanha a região do evento e mostra placares de objetivos.

## Dados e equilíbrio

Amostras de jogadores e equipes do CBLOL 2026 Split 2, fase regular e playoffs, congeladas em 21/11/2026. CSVs em `data/`; `scripts/ratings.mjs` reproduz as notas. Percentis por posição, amostras pequenas aproximadas da média e escala comprimida 64–88.

- Micro: 80% individual +20% coletivo.
- Macro: 65% individual +35% coletivo.
- Mental: 75% consistência individual +25% coletivo.
- Forma coletiva: 45% vitórias, 25% dragões, 20% Barão, 10% ouro aos 15 minutos, comparados como percentis e ponderados por fase.
- Overall: 40% micro +40% macro +20% mental.
- Chances da simulação limitadas a 18%–82%. Mental é uma mecânica fictícia estimada, sem avaliação psicológica de pessoas reais.

Fontes e fórmulas estão em “Dados e balanceamento”, nos CSVs, em `research/worlds-sources.md` e em `data/PLAYER_PHOTOS.md`. Fotos: 42 dos rosters oficiais do LoL Esports; Shini usa retrato histórico identificado de 2025 via Sheep Esports/Leaguepedia. Campeões via Riot Data Dragon16.22.1. Os estilos são nossa curadoria; picks e posições dos drafts são preservados das tabelas consultadas.

## Execução e arquitetura

Node.js 22+, sem dependências externas de npm:

```sh
npm run check
npm run build
npm run dev
```

No ambiente gerenciado, usar `sites-preview start /workspace/sites/rift-leilao`. O build recursivo incorpora assets, motor e API em `dist/server/index.js`. Binding D1 `DB`, migrações em `drizzle/`, empacotadas em `dist/.openai/drizzle/`.

Salas online: tokens anônimos, estado persistido em D1, polling de 1,5 segundo e controle de versão otimista. Treino é local e identificado. Links não contêm tokens. A opção adversária escolhida, resultado futuro e RNG não são expostos na fase de draft. Durante a simulação, só eventos já revelados são enviados; penalidades de rendimento pré-jogo são mantidas na visão pública para não antecipar o vencedor.

Salas expiram em 24 horas. Técnicos retomam pelo mesmo navegador; não há recuperação de identidade em outro aparelho. Configurações novas devem ser usadas em uma sala nova. Etapas expiradas avançam na próxima consulta; não existe cron com todas as abas fechadas. Sem dinheiro real, apostas, cadastro ou gravação de áudio. O histórico ranqueado é local por navegador e nome da equipe, não uma classificação online global.

Licenças e créditos: Riot Games / LoL Esports para imagens; DM Sans sob OFL. Sem afiliação ao Footlobby, Riot ou CBLOL.
