# Rift Draft Online — clone independente

Esta branch é a versão independente e atualizada do jogo, pronta para uma hospedagem Cloudflare Workers. Não muda o domínio nem o banco D1 do site anterior.

## Publicar como site novo

1. Entre em https://dash.cloudflare.com/ e faça login (plano Free pode ser suficiente para partidas de baixo tráfego).
2. Vá em **Workers & Pages** > **Create application** > **Import a repository** / **Connect to GitHub**.
3. Autorize o GitHub, escolha `mateuszilio225/teste-c` e a branch de produção `rift-draft-online`, com diretório raiz `/`.
4. Configure o nome do Worker `rift-draft-online` e verifique se o binding D1 `DB` aponta para uma base nova. Não reutilize o D1 do site anterior.
5. Comandos: **Build** `npm run build`; **Deploy** `npm run deploy` (aplica migrações D1 e publica). Se a importação não provisionar a D1 automaticamente, crie uma database `rift-draft-online` em Cloudflare D1 e substitua no `wrangler.jsonc` o `database_id` de exemplo pelo ID real.
6. Confirme o deploy. Cloudflare mostra uma URL pública `workers.dev` para o novo jogo; não invente o URL antes da plataforma gerar.
7. Abra em outro aparelho e valide: `Criar sala com amigos` > copiar código > `Entrar` > fazer lance; jogar uma MD3 com dois navegadores.

## Requisitos

- Node.js 22+
- Deploy do Worker e banco D1 inicializado (`drizzle/0000_rooms.sql`). Sem D1 o treino local funciona, mas salas online não.
- As salas são criadas por código, sem matchmaking, para 2, 4 ou 8 equipes; slots vazios podem ser preenchidos por bots.
- Salas expiram após 24 horas; é um clone independente, então contas, nomes, salas e ranking não são transferidos do site antigo.
- O ranking é local ao navegador, não há ranking global.

## Teste local

```bash
npm run check
npm run build
npm run dev
```

Abra `http://localhost:4173`.

## Novidades v3 e senha de administrador

A branch `rift-draft-online` já possui o ID correto do D1 `rift-draft-online`; o comando de deploy aplicará também `drizzle/0001_profiles_presets.sql`. Para que o botão **⚙ Admin global** salve valores para todas as salas futuras, entre na Cloudflare > Workers & Pages > `rift-draft-online` > Settings > Variables and Secrets e configure um Secret `ADMIN_PASSWORD` com no mínimo 12 caracteres. Nunca compartilhe essa senha no chat. Depois use o menu Admin global no site.

O deploy do GitHub é automático apenas se o vínculo Cloudflare continuar ativo e o build terminar em Ready. O endereço público exato aparece no botão Visit do seu painel, não é inferido a partir do nome.
