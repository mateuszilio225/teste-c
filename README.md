# Zyon Ezreal 0.2.1

Protótipo para Windows 10/11 x64: **Espaço segurado** ativa Q/W e esquiva dos
projéteis visuais cadastrados; **X segurado** ativa last hit por AA. **F10** desarma.
Deslocamento máximo, folga e antecipação da esquiva são configuráveis.

## Download

- [Pacote Windows](https://github.com/mateuszilio225/teste-c/releases/download/v0.2.1/zyon-ezreal-win10.zip)
- [Código-fonte ZIP](https://github.com/mateuszilio225/teste-c/archive/refs/heads/main.zip)
- [Estado da compilação Windows](https://github.com/mateuszilio225/teste-c/actions)

Extraia o pacote inteiro e abra `ZyonEzreal.exe`. Mantenha `_internal` ao lado dele.
No código-fonte, instale Python 3.11/3.12 x64 e abra `INICIAR.bat`.
`DEMO.bat` roda uma cena sintética sem enviar input ao jogo.

## Configuração necessária

Use **Calibrar automaticamente** com Ezreal de vida cheia, Q/W disponíveis e
círculo de alcance de AA visível na captura. A tentativa localiza ícones, barra,
centro e escala quando reconhecidos; propõe um recorte acima da HUD. Monitor e
resolução são detectados pelo sistema. Valores não detectados continuam pendentes.

O clique no corpo do minion, seu HP máximo e as aparências de projéteis continuam
exigindo configuração. A detecção de barra inimiga usa uma aproximação dos pés
baseada na barra do próprio campeão. Confira a prévia e ajuste manualmente quando
necessário. A precisão automática não foi medida em screenshots reais do LoL.

Abra a aba **Calibração** e siga os passos para área de jogo, círculo de alcance
do AA, sua barra, barras inimigas/minions, ícones Q/W disponíveis e projéteis.
Use câmera travada, janela sem bordas, zoom constante e conjuração rápida sem
indicador. Tire X de comandos conflitantes. Marque as funções desejadas, salve e arme.

**A esquiva não reconhece todas as skills automaticamente.** Ela depende dos recortes
visuais cadastrados para direção/skin/animação, pode confundir efeitos parecidos e
não conhece paredes. Q/W usam alcance projetado e interceptação aproximada.
Last hit exige HP máximo e armadura do tipo de minion informados manualmente.
Não há garantia de acertos, farm perfeito ou ausência de banimento.

Leia [LEIA-ME.txt](LEIA-ME.txt) para calibração, parâmetros e limites completos.
Veja [VALIDACAO.txt](VALIDACAO.txt) para o que foi testado. Não foi comprovada
eficácia em partidas reais com Windows 10/Vanguard.

## Testes

```console
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

O workflow compila o executável no Windows, testa o código e publica o ZIP na
release `v0.2.1`. O executável não é assinado.
