# BR2002 Call

Uma sala de voz, câmera e compartilhamento de tela para até **6 pessoas**, no navegador. Projeto independente, sem vínculo com o Discord.

## Funciona de verdade

- Criar sala e convidar pelo link, sem cadastro.
- Voz e câmera entre participantes usando **WebRTC**; sinalização pelo serviço público do **PeerJS**.
- Compartilhar aba, janela ou tela, com áudio do sistema quando o navegador oferece.
- Câmera sobreposta à transmissão: arrastar, alterar tamanho, formato e espelhamento. A posição do apresentador é enviada aos demais participantes.
- Tela e câmera enviadas separadamente. A sobreposição acontece na interface de quem assiste, sem recompor cada quadro do vídeo em canvas.
- Perfis de captura: 1080p/30, 720p/60 e 1080p/60 como metas. Ajuste do bitrate por conexão quando o RTT indica congestionamento.
- Chat efêmero, reações, enquetes, dados D20, sorteio de participantes, foco coletivo de 25 minutos e efeitos sonoros sintetizados, com consentimento de quem ouve.
- Laser e desenhos compartilhados em coordenadas da imagem transmitida.
- Modo foco, tela cheia, atalhos de teclado, temas e movimento reduzido.
- Prévia local claramente identificada e quadro de teste animado que pode ser transmitido para outra sessão, sem capturar a tela do usuário.

## Rodar

Sem dependências de build. Node 22+ é suficiente:

```sh
npm run build
npm run check
```

Sirva a raiz ou `dist/` por HTTPS. Para desenvolvimento, `localhost` também é considerado um contexto seguro pelos navegadores. Arquivos abertos por `file://` não são uma forma suportada de compartilhar convites.

O GitHub Pages serve diretamente os arquivos da raiz. O Sites usa `dist/`, conforme `.openai/hosting.json`.

## Como usar

1. Crie uma sala e escolha um apelido. É possível desmarcar o microfone para entrar sem acesso a dispositivos.
2. Copie o convite e envie para até cinco amigos.
3. Clique em compartilhar tela. Para testar sem captura, abra **Ajustes → Transmissão → Enviar quadro de teste**.
4. Ative a câmera. Arraste a janela por cima da transmissão, mude o tamanho ou use o formato circular.
5. Clique no participante que compartilha para escolher a tela que você quer assistir.

Atalhos: `M` microfone, `V` câmera, `S` compartilhamento, `F` foco e `D` áudio recebido. Eles ficam suspensos ao digitar ou com um diálogo aberto.

## Limites importantes da arquitetura

Esta versão usa uma malha direta entre navegadores, com STUN público do Google e da Cloudflare. **Não inclui TURN nem SFU.** Algumas redes corporativas, operadoras ou NATs restritos podem impedir conexões; redes e computadores mais fracos podem reduzir a fluidez. Para um serviço comercial, é necessário configurar TURN e adotar SFU para salas maiores. 60 fps é uma meta de captura, não uma promessa.

O criador mantém a aba aberta para permitir novas entradas. Se ele sair, as conexões já estabelecidas entre os demais podem continuar; para convidar novas pessoas, crie uma nova sala.

Captura de tela é uma função de navegadores compatíveis no computador. Em celulares sem `getDisplayMedia`, o app continua permitindo câmera, voz e assistir; o compartilhamento exibe uma orientação em vez de simular uma captura.

A sobreposição é feita em HTML sobre o vídeo. O arquivo de vídeo transmitido isoladamente e o Picture-in-Picture nativo não incluem essa composição. Tela cheia e modo foco do app preservam a sobreposição.

## Dados e privacidade

- Não há banco de dados de mensagens, gravação automática nem upload de arquivos.
- Mensagens, enquetes e estado da sala ficam na memória das abas; o criador repassa os últimos eventos aos novos participantes.
- Apelido, avatar e preferências de interface ficam no armazenamento local do navegador.
- Links têm um código aleatório de 80 bits. Quem tiver o convite pode entrar: ele não substitui autenticação, moderação ou uma lista de convidados.
- O serviço público PeerJS participa da sinalização. O áudio e vídeo usam os transportes criptografados do WebRTC.
- Os efeitos remotos só são reproduzidos por quem ativa “Ouvir efeitos”.

## Terceiros

PeerJS 1.5.5 está incluído em `vendor/`, com licença MIT. DM Sans e Space Grotesk estão incluídas em `fonts/`, com suas licenças OFL. Os efeitos do soundboard são sintetizados pelo app.

## Verificação

`npm run check` verifica sintaxe, referências do DOM, presença dos assets e identidade do manifesto. A prévia interna gerenciada apresentou falha de relay; os resultados de teste da publicação são registrados em `QA.md` após a conferência.
