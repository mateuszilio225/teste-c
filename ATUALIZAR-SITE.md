# Como colocar este Rift Draft atualizado no ar

O arquivo ZIP contém o projeto atualizado, os dados, os testes e o build `dist/`. O endereço público antigo **não é alterado automaticamente** ao baixar este ZIP.

## Atualizar a branch existente do GitHub

O projeto original indica o repositório `https://github.com/mateuszilio225/teste-c` e a branch `rift-draft`.

1. Faça um backup do repositório/branch atual antes de sobrescrever arquivos.
2. Instale o Git e o Node.js 22 ou superior, caso ainda não estejam disponíveis.
3. No terminal, execute:

   ```bash
   git clone -b rift-draft https://github.com/mateuszilio225/teste-c.git
   cd teste-c
   ```

4. Extraia este ZIP e **copie todo o conteúdo extraído para dentro da pasta `teste-c`**, substituindo os arquivos correspondentes. Não apague `.git` da pasta clonada.
5. Execute:

   ```bash
   npm run check
   npm run build
   git add .
   git commit -m "Atualiza Rift Draft com CBLOL, ranked e novo visual"
   git push origin rift-draft
   ```

6. Se o domínio publicado estiver integrado à branch `rift-draft`, a plataforma deverá executar o deploy configurado para esse repositório. Caso não esteja integrado, faça a publicação pelo painel da hospedagem. Nenhum deploy foi realizado por este pacote.

## Testar no computador antes de publicar

No diretório do projeto, execute:

```bash
npm run build
npm run dev
```

Abra `http://localhost:4173`. A sala online local usa um banco SQLite de pré-visualização; em produção, a aplicação depende do binding D1 `DB` já especificado no projeto original.

## Alterações importantes

- Notas personalizadas ficam **na sala**; são válidas somente para aquele campeonato.
- O dono da sala concede permissão de editor às equipes humanas autenticadas. Não é possível virar administrador apenas digitando um nickname.
- O ranking/PDL de cada nome de equipe fica **salvo localmente neste navegador**, sem conta online/global ou sincronização entre computadores. Para preservar o progresso nesse navegador, não limpe os dados locais do site.
- Salas online antigas mantêm as configurações salvas e são atualizadas de modo compatível, mas recomendamos abrir uma sala nova para experimentar o novo draft.
