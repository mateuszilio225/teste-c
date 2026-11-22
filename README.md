# Rift Draft

Jogo independente inspirado em **Footlobby**. Leilão de jogadores do CBLOL com 50 moedas fictícias, cinco posições, fotos reais, drafts verificados do Worlds 2026 e séries melhor de três.

Site: https://rift-draft-br2002.wrydingo.chatgpt.site/
Código: https://github.com/mateuszilio225/teste-c/tree/rift-draft

## Leilão

- **Nenhuma carta entra automaticamente no time.** Só o maior lance confirmado compra. Lote sem lance volta ao mercado sem cobrar ninguém.
- Criador escolhe mercado exato (equipes × 5), exato +12 ou todos os 44 nomes. +12 é limitado ao catálogo; o total real aparece antes de iniciar. Cada posição tem oferta suficiente.
- Cada carta só pode ser comprada uma vez. Dez segundos por lote, extensão de 2,5 segundos para lance tardio, reserva de uma moeda por vaga restante.
- Proteção contra lance atrasado comprar outra carta. Bots fazem lances e também precisam comprar suas cinco cartas.
- Botão Mercado permite consultar cartas restantes e o criador recolocar uma carta em um lote sem lances.
- Opção de esconder overall, atributos e preço de referência no leilão, inclusive no catálogo e nos detalhes da carta.

## Campeonato e draft

- Mata-mata; pontos corridos; liga com playoffs; grupos com mata-mata. Salas para 2, 4 ou 8 equipes.
- Todos contra todos uma vez nas ligas. 3 pontos por MD3 vencida. Desempates: saldo de jogos, jogos vencidos, ordem do sorteio inicial.
- Liga + playoffs: 4 de 8 ou 2 de 4 avançam. Grupos: duas chaves; 8 equipes classificam duas por grupo com semifinais cruzadas; 4 equipes classificam uma por grupo para a final.
- **Melhor de três real:** termina em 2–0 ou 2–1, sem terceiro jogo após 2–0.
- Duas alternativas reais do Worlds 2026 por lado. Line-ups e alternativas adversárias são visíveis; a escolha exata é escondida até o início do jogo.
- Base com 50 drafts verificados e fonte por cartão. Quatro packs de oito drafts completamente disjuntos garantem quatro opções compatíveis em cada jogo da MD3. Só campeões escolhidos ficam bloqueados; alternativas não escolhidas podem voltar.
- Consequências de mental após derrotas, recuperação após vitória e reset em cada nova MD3.

## Apresentação

Tema escuro, 44 fotos de jogadores, seleção de campeões animada, alerta específico quando cobrirem seu lance, música ambiente original sintetizada e alerta de contagem regressiva sincronizados com o relógio. Música e alertas têm controles separados e só iniciam após interação do visitante; preferências ficam no navegador.

Simulações fictícias variam cronologia, ganks, invasões, lutas em rotas e selvas, larvas, dragões, Arauto, Barão, possíveis roubos, pressão lateral e Ancião em jogos longos. O mapa acompanha a região do evento e mostra placares de objetivos.

## Dados e equilíbrio

Amostras de jogadores e equipes do CBLOL 2026 Split 2, fase regular e playoffs, congeladas em 21/11/2026. CSVs em `data/`; `scripts/ratings.mjs` reproduz as notas. Percentis por posição, amostras pequenas aproximadas da média e escala comprimida 64–88.

- Micro: 80% individual +20% coletivo.
- Macro: 65% individual +35% coletivo.
- Mental: 75% consistência individual +25% coletivo.
- Forma coletiva: 45% vitórias, 25% dragões, 20% Barão, 10% ouro aos 15 minutos, comparados como percentis e ponderados por fase.
- Overall: 40% micro +40% macro +20% mental.
- Chances da simulação limitadas a 18%–82%. Mental é uma mecânica fictícia estimada, sem avaliação psicológica de pessoas reais.

Fontes e fórmulas estão em “Dados e balanceamento”, nos CSVs, em `research/worlds-sources.md` e em `data/PLAYER_PHOTOS.md`. Fotos: 42 dos rosters oficiais do LoL Esports; Shini/Luuukz usam retratos históricos identificados de 2025 via Sheep Esports/Leaguepedia. Campeões via Riot Data Dragon16.22.1. Os estilos são nossa curadoria; picks e posições dos drafts são preservados das tabelas consultadas.

## Execução e arquitetura

Node24+, sem dependências de npm:

```sh
npm run check
npm run build
npm run dev
```

No ambiente gerenciado, usar `sites-preview start /workspace/sites/rift-leilao`. O build recursivo incorpora assets, motor e API em `dist/server/index.js`. Binding D1 `DB`, migrações em `drizzle/`, empacotadas em `dist/.openai/drizzle/`.

Salas online: tokens anônimos, estado persistido em D1, polling de 1,5 segundo e controle de versão otimista. Treino é local e identificado. Links não contêm tokens. A opção adversária escolhida, resultado futuro e RNG não são expostos na fase de draft. Durante a simulação, só eventos já revelados são enviados; penalidades de rendimento pré-jogo são mantidas na visão pública para não antecipar o vencedor.

Salas expiram em24horas. Técnicos retomam pelo mesmo navegador; não há recuperação de identidade em outro aparelho. Configurações novas devem ser usadas em uma sala nova. Etapas expiradas avançam na próxima consulta; não existe cron com todas as abas fechadas. Sem dinheiro real, apostas, cadastro ou gravação de áudio.

Licenças e créditos: Riot Games / LoL Esports para imagens; DM Sans sob OFL. Sem afiliação ao Footlobby, Riot ou CBLOL.
