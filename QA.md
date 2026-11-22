# Conferência da versão pública

- [x] Sintaxe, assets, IDs do DOM e manifesto de hospedagem (`npm run check`).
- [x] Acesso público sem conta e conferência visual no Chrome da versão publicada.
- [x] Sala real criada pela interface do navegador; quadro animado local, controles da sobreposição e chat local.
- [x] Duas sessões independentes com sinalização pública PeerJS e transporte WebRTC nativo: entrada, mídia bidirecional e chat em ambas as direções.
- [x] Transmissão de quadro animado com frames decodificados no receptor (47 frames em 1,7 segundo no teste sintético; não é benchmark de produção).
- [x] Tamanho, formato e arraste da sobreposição sincronizados no receptor.
- [x] Substituição de tracks de câmera e microfone por fontes sintéticas.
- [x] Enquete/voto, timer, desenho, reação, silenciar áudio, parar transmissão e saída sincronizados.
- [x] Texto com marcação HTML tratado como texto; nenhuma exceção da aplicação no teste de integração.
- [ ] Dispositivos físicos, redes diferentes, seis participantes, celulares e testes de carga.

O teste de integração usou Happy DOM para a interface e `@roamhq/wrtc` para conexões WebRTC reais, com vídeo e áudio sintéticos. O relatório `integration-results.json` identifica o hash exato de `app.js` testado. Não substitui um teste com amigos em redes e aparelhos diferentes.

A entrada da segunda aba no Chrome remoto não se completou, inclusive após a correção; a causa nesse navegador não foi confirmada. Os resultados de duas sessões acima são do teste nativo, não do Chrome. O teste nativo permitiu identificar e corrigir um conflito do contador de pacotes com o registro interno de eventos do PeerJS. O fechamento de uma conexão de mídia também recebeu proteção contra referência já liberada.

A arquitetura usa STUN, sem relay TURN ou SFU. Redes restritas podem impedir a conexão. A taxa de captura depende do computador, navegador e upload de cada participante.
