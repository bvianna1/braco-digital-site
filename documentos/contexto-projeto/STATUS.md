# STATUS — Braço Digital

> **Status: ATIVO desde 2026-10-29** (aprovado por Bruno). Snapshot **datado** do projeto, carregado
> por referência a partir do `AGENTS.md` da raiz.
>
> **Regra deste arquivo:** só entra o que foi **verificado na data abaixo**, com comando e saída.
> **Card `done` no Kanban é histórico do que foi feito, não prova de saúde atual.** Se a data deste
> arquivo não for a de hoje, reconfira com o §4 antes de afirmar que está tudo bem.

**Data da verificação:** 2026-10-29. **Verificado por:** orquestrador (read-only, sem alterar nada).

---

## 1. Produção (verificado hoje)

| Item | Comando | Resultado |
|---|---|---|
| Home | `curl -o /dev/null -w '%{http_code}'` | **200** |
| `osc.html` | idem | **200** |
| `sitemap.xml` | idem | **200** |
| `healthz` no domínio público | idem | **404** — esperado: health check é interno (D6) |
| **Paridade produção × local** | `curl sitemap.xml \| diff - sitemap.xml` | **idêntico** |
| **Paridade de página** | sha256 do `osc.html` servido × local | `e331e3b5…` = `e331e3b5…` — **byte a byte** |

Conclusão honesta: **o que está em `main` está no ar** hoje (29/10). Isso não garante que o deploy
automático continue funcionando amanhã — ver §3.

## 2. Repositório e testes (verificado hoje)

- Branch `main`, HEAD **`0a3abf0`** (merge do `lastmod` da home no sitemap).
- `python3 -m unittest discover -s api -p 'test_*.py'` → **12 testes, OK** (0,05 s).
- **Não rastreados:** `.worktrees/` e 3 PNGs em `assets/marca/`
  (`ilustracao-braco-interface`, `lockup-braco-digital`, `selo-bd-hud`).
- As seis páginas referenciam `css/*.v2.css` e `js/app.v2.js`; as seis contêm GA4 `G-P51CNDWHR2`.

## 3. O que **não** está verificado / não pode ser afirmado hoje

- **Deploy automático (GitHub→Dokploy):** não inspecionei o agente de polling nem o webhook. A
  paridade de hoje prova o estado, **não** que o pipeline de deploy está saudável.
- **`/healthz` público devolve 404:** não confirmei onde ele responde internamente (rede do Dokploy).
  Se o health check for esperado pelo Dokploy, isso precisa ser verificado na configuração do serviço.
- **Eventos GA4 do formulário e do clique no Instagram:** card `t_b08ee9a8` está `ready`, ou seja,
  **não instrumentado** ainda. O GA4 presente nas páginas mede pageview, não conversão.
- **Rate limit em produção:** só há evidência em teste local/CI (12 casos). Teste de carga em
  produção é **proibido** (D3) — a afirmação fica limitada ao teste.
- **`README.md` está desatualizado** (medido): cita só `index.html`; diz "CSS e JavaScript inline"
  quando as seis páginas usam `css/*.v2.css` + `js/app.v2.js`; e diz que "ainda não existe política
  de privacidade" quando `politica-de-privacidade.html` existe e está no sitemap. Corrigir o README é
  trabalho novo, ainda não feito.
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
