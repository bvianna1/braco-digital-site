# STATUS — Braço Digital

> **Status: ATIVO desde 2026-10-29** (aprovado por Bruno). Snapshot **datado** do projeto, carregado
> por referência a partir do `AGENTS.md` da raiz.
>
> **Regra deste arquivo:** só entra o que foi **verificado na data abaixo**, com comando e saída.
> **Card `done` no Kanban é histórico do que foi feito, não prova de saúde atual.** Se a data deste
> arquivo não for a de hoje, reconfira com o §4 antes de afirmar que está tudo bem.

**Data da verificação:** 2026-11-13. **Verificado por:** agente `jony` (produção consultada
read-only; este arquivo atualizado no lote `site/tokens-versao-hashes`).

---

## 1. Produção (status HTTP e paridade medidas em 2026-11-13)

| Item | Comando | Resultado |
|---|---|---|
| Home | `curl -o /dev/null -w '%{http_code}'` | **200** |
| `osc.html` | idem | **200** |
| `politica-de-privacidade.html` | idem | **200** |
| `sitemap.xml` | idem | **200** |
| `healthz` no domínio público | idem | **404** — esperado: health check é interno (D6) |
| `README.md` no domínio público | idem | **404** — documentação interna não é publicada |
| **Paridade produção × local (sitemap)** | `curl sitemap.xml \| diff - sitemap.xml` | **idêntico** |
| **Paridade de página** | sha256 do `osc.html` servido × `git show main:osc.html` | `e331e3b5…` = `e331e3b5…` — **byte a byte** |

Nota de método: a paridade de página é medida contra `main`, não contra a árvore de trabalho, porque
a árvore local pode estar à frente de `main` durante um lote. O que interessa aqui é "o que está em
`main` está no ar".

Conclusão honesta: **o que está em `main` está no ar** em 2026-11-13. Isso não garante que o deploy
automático continue funcionando amanhã — ver §3.

## 2. Repositório e testes (medido em 2026-11-13)

- Branch `main`, HEAD medido nesta data: **`9545f0c`** (versão do CSS da política + README/AGENTS
  alinhados). Lote seguinte em andamento nesta data: `site/tokens-versao-hashes`. HEAD é medição
  datada e cada merge o move — a referência viva é `git log --oneline -1` em `main`.
- `python3 -m unittest discover -s api -p 'test_*.py'` → **12 testes, OK** (0,037 s).
- **Não rastreados:** `.worktrees/` e 3 PNGs em `assets/marca/`
  (`ilustracao-braco-interface`, `lockup-braco-digital`, `selo-bd-hud`).
- **Tokens de versão, medidos por script em 2026-11-13:** o logo é servido como
  `assets/marca/logo-light.svg?v=5dd0c38`; a home usa `css/index.v2.css?v=5b64311`; a política usa
  `css/politica.v2.css?v=d9f2841`; as outras quatro usam `css/paginas.v2.css?v=seoh1` — exceção
  legada declarada no `AGENTS.md` §2, migra quando o arquivo mudar. Todo token (exceto o `seoh1`)
  confere com o sha7 do sha256 do arquivo: 16 tokens corretos, 0 divergências. As seis páginas contêm
  GA4 `G-P51CNDWHR2`.
- **Carregamento real do JS nas seis páginas, medido em Chrome sobre HTTP local em 2026-11-13:**
  `js/app.v2.js?v=2724a85` responde **200** e **executa** em `index`, `osc`, `financeiro`,
  `administrativo`, `relatorios` e `politica-de-privacidade`: em cada página o `<script>` tem `src`
  com atributo fechado valendo exatamente `js/app.v2.js?v=2724a85`, existe `a.wa-float` e o número de
  âncoras é o mesmo de `main` (33/9/6/6/6/4). Na home, `#ano` fica `2026`, `.hamb` alterna
  `body.menu-open` (true→false) e os `href` de `wa.me` do corpo recebem `?text=` — idênticos aos de
  `main`. **Correção de método em 2026-11-13:** a redação anterior dizia que "as seis páginas
  carregam" o JS, mas a medição era `grep` da string e o HTML estava inválido (faltava a aspa de
  fechamento do `src` — defeito do lote `site/tokens-versao-hashes`, reprovado na auditoria
  `t_44c2911a`); token presente na string não prova carregamento. O gate estrutural que pega esse
  modo de falha é `grep -nE '(src|href)="[^"]*$' *.html` — hoje sem saída nas seis páginas.

## 3. O que **não** está verificado / não pode ser afirmado hoje

- **Deploy automático (GitHub→Dokploy):** não inspecionei o agente de polling nem o webhook. A
  paridade de hoje prova o estado, **não** que o pipeline de deploy está saudável.
- **`/healthz` público devolve 404:** não confirmei onde ele responde internamente (rede do Dokploy).
  Se o health check for esperado pelo Dokploy, isso precisa ser verificado na configuração do serviço.
- **Eventos GA4 do formulário e do clique no Instagram:** card `t_b08ee9a8` está `ready`, ou seja,
  **não instrumentado** ainda. O GA4 presente nas páginas mede pageview, não conversão.
- **Rate limit em produção:** só há evidência em teste local/CI (12 casos). Teste de carga em
  produção é **proibido** (D3) — a afirmação fica limitada ao teste.
- ~~`README.md` desatualizado~~ — **corrigido em 2026-11-13** em duas etapas: passou a listar as 6
  páginas, os assets externos com token de versão e a existência da política publicada e linkada no
  consentimento; e a frase sobre o token deixou de ser falsa quando os tokens foram normalizados para
  o sha7 real de cada arquivo (lote `site/tokens-versao-hashes`). Publicação segue o fluxo normal (D1).
- **Versionamento de asset: existia, mas era irregular — normalizado em 2026-11-13.** Medição
  anterior: home em `css/index.v2.css?v=f4e66e1`, quatro páginas em `css/paginas.v2.css?v=seoh1`, e a
  política sem token (corrigida no lote anterior para `?v=d9f2841`). Situação agora: todo `?v=` de
  CSS, JS e logo é o sha7 do sha256 do arquivo, **exceto** `?v=seoh1` em `paginas.v2.css`, exceção
  legada que o `AGENTS.md` §2 manda migrar quando o arquivo mudar. Os antigos `f4e66e1` (index.v2.css)
  e `a886879` (logo) nunca corresponderam ao conteúdo do arquivo — não eram sha7, md5 nem blob sha1.
- **Revisão jurídica da política de privacidade: pendente.** O texto está no ar desde 16/08/2026
  (commit `67904dd`) sem parecer de advogado; a política cita a ANPD genericamente (prazo de 15 dias
  para responder solicitações) e não declara base normativa específica. Ver README §Segurança e dados.
- **Aviso de medição:** a primeira leitura deste repositório (2026-10-29) afirmou "nenhum asset usa
  `?v=`" — era **falso**, produzido por uma regex que exigia dígitos após `v=`. Os tokens reais são
  hexadecimais (`f4e66e1`) e alfanuméricos (`seoh1`). Corrigido aqui e em `DECISIONS.md` D11.
- **Clones paralelos do repositório — medidos hoje.** Cinco diretórios irmãos
  (`braco-digital-{api-ratelimit,fix-sobre,ratelimit-volume,security,seo-osc}`) estão em branches
  próprias, **todas atrás** de `origin/main` (34, 46, 36, 43 e 11 commits atrás) e **nenhuma à
  frente** (`git rev-list --left-right --count origin/main...HEAD` → `N 0` em todas). Ou seja: **não
  há trabalho perdido** ali — são cópias velhas de branches já mescladas. O risco é trabalhar na
  pasta errada. Sempre partir de `~/workspace/braco-digital-site`. Existe também `.worktrees/` não
  rastreado dentro do repo canônico (worktrees dos cards).
- **Runbook de rollback não localizado por nome.** O plano do deploy automático (opções, fluxo,
  rollback) está em `~/workspace/braco-digital-operacao/proposta-deploy-automatico-sem-porta-3000.md`,
  **fora do repositório**, e não há um runbook operacional único e curto ("como reverter um deploy
  quebrado, passo a passo"). O card `t_d55ce48c` registra a intenção de documentar. Quem precisar
  reverter hoje depende desse plano + conhecimento do Dokploy.

## 4. Como reconferir (sem depender deste arquivo)

```bash
cd ~/workspace/braco-digital-site
git log --oneline -1 && git status --porcelain
python3 -m unittest discover -s api -p 'test_*.py'

curl -sS -o /dev/null -w '%{http_code}\n' https://bracodigital.com.br/
curl -sS https://bracodigital.com.br/sitemap.xml | diff - sitemap.xml     # paridade
curl -sS https://bracodigital.com.br/osc.html | sha256sum; sha256sum osc.html
```

## 5. Kanban (fonte das tarefas)

Board **`site`**. Em 2026-10-29, **abertos**:

- `t_6f1ffee8` — páginas de soluções reais (clipping, QGD, pagamentos) — `ready`, sem responsável.
- `t_b08ee9a8` — instrumentar GA4 (evento do formulário + clique no Instagram) — `ready`.
- `t_495654df` — blog estático (cases anônimos) — `blocked`.

Histórico recente que explica o estado atual: higiene SEO (`t_c38236ed` → auditoria `t_9e0bd7f1` →
merge `t_32975b86` → folga `t_712ac97e`), `lastmod` da home (`t_f0fa6345`), versão B das internas
(`t_ce07aa71`, `t_3aca6439`), CSP (`t_45a5be7f`), rate limit persistido (`t_45a345e1`,
`t_d2d0b5cd`), deploy automático (`t_e5fbd70c` e filhos), Cloudflare Tunnel (`t_11f27bc5`).

## 6. Manutenção deste arquivo

- Atualizar **por lote relevante ou incidente** — não a cada deploy.
- Lote relevante = mudou comportamento público (página, header, contrato da API, deploy) ou houve
  incidente.
- Toda linha precisa de comando reexecutável; sem isso, vai para o §3.
