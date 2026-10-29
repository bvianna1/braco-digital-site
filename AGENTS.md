# Braço Digital — regras para agentes que trabalham neste repositório

> **Status: ATIVO desde 2026-10-29** (aprovado por Bruno). Este é o `AGENTS.md` do diretório de
> trabalho: o Hermes o injeta em toda sessão com cwd neste repositório. Os documentos de apoio vivem
> em `documentos/contexto-projeto/` (`PROJECT.md`, `STATUS.md`, `DECISIONS.md`). Histórico da adoção:
> `documentos/contexto-projeto/LEIA-ME.md`.

Produto: **site institucional da Braço Digital** (`https://bracodigital.com.br`) + **API de captação
de diagnóstico**. Repositório canônico: `~/workspace/braco-digital-site`, `origin` =
`github.com/bvianna1/braco-digital-site`, branch de produção **`main`**.

Escopo destas regras: qualquer sessão de agente com cwd neste diretório. Regra específica de
conteúdo, visual ou contrato de API **não** mora aqui: mora na fonte canônica (§3).

## 1. Antes de agir

1. **O Kanban é a fonte das tarefas.** Board `site`. Card aberto é o que autoriza mexer; trabalho
   novo nasce como card, não como improviso.
2. **Uma mudança por card, um card por repositório.** Clones paralelos do mesmo site já causaram
   divergência — não abrir segunda cópia do repo para "testar".
3. **Produção é `origin/main`.** Merge em `main` dispara deploy automático. Não existe "só no meu
   diretório": se está em `main`, está no ar.
4. **Modelo mais barato primeiro.** Modelo caro exige justificativa técnica escrita. Tarefa mecânica
   (build, grep, validação) é script, não LLM.

## 2. Invariantes (nunca violar)

- **Executor ≠ auditor.** Quem implementa não audita. Toda mudança de site/API passa por auditoria
  **read-only** (perfil `paulo`) **antes do merge** — ou imediatamente após o lote, quando o Bruno
  autorizar o inverso. A auditoria não edita: ela reporta.
- **Sem load test em produção.** Rate limit é validado só em teste local/CI. Nunca disparar carga
  contra o domínio público nem contra a API no ar.
- **Segredo não entra no repositório.** `RESEND_API_KEY` e afins vivem na configuração do Dokploy.
  `api/.env.example` só tem nomes e exemplos, nunca valor real.
- **Sem dado inventado no conteúdo.** Nenhum CNPJ, número, nome de cliente, depoimento, link de
  LinkedIn ou foto que não exista. Conteúdo institucional sem prova vira promessa falsa.
- **Nada de PII em log.** A API não registra IP, nome, e-mail nem corpo enviado.
- **Não afrouxar a CSP para "fazer funcionar".** `nginx.conf` mantém a política sem `unsafe-inline`;
  se um script novo precisa de origem, o ajuste é explícito na política e auditado — nunca relaxar
  para `*` ou `unsafe-*` por conveniência.
- **Página nova entra em três lugares, sempre os três:** `Dockerfile` (COPY explícito), `sitemap.xml`
  (com `lastmod` correto) e os links internos/`og:`. Página sem COPY não é publicada; página fora do
  sitemap não é indexada.
- **`lastmod` do sitemap = data do último commit de conteúdo daquela página**, não a data do dia.
- **Não reescrever página publicada sem preview aprovado.** Mudança visual/frase de conversão se
  mostra no preview (Tailscale/desktop) e o Bruno aprova antes do merge.

## 3. Fontes canônicas (não duplicar aqui)

| Assunto | Fonte canônica |
|---|---|
| Rotas, contrato, validação, honeypot, CORS, rate limit, variáveis de ambiente | `api/server.py` (código) + `README.md` §Variáveis e §Segurança |
| Headers de segurança, CSP, cache por bloco, roteamento do proxy | `nginx.conf` |
| Deploy, imagens, volume do rate limit, steps do Dokploy | `README.md` §Deploy + `LEIA-ME.md` |
| Deploy automático: opções avaliadas, fluxo e rollback | `~/workspace/braco-digital-operacao/proposta-deploy-automatico-sem-porta-3000.md` (fora do repo) |
| O que é o produto, escopo e arquitetura | `documentos/contexto-projeto/PROJECT.md` |
| Decisões já tomadas, com a medição que as sustenta | `documentos/contexto-projeto/DECISIONS.md` |
| Estado datado, com evidência ao vivo | `documentos/contexto-projeto/STATUS.md` |
| Tom de voz, oferta e regras de conteúdo | `DECISIONS.md` D9 + aprovação do Bruno |

**Aviso de fonte fora de uso:** o `README.md` está **desatualizado** (ver `STATUS.md` §3) — descreve
só `index.html` e "CSS e JS inline", e diz que não existe política de privacidade. O código e os
arquivos são a verdade; o README é referência técnica parcial até ser corrigido.

## 4. Validação obrigatória antes de qualquer merge

```bash
python3 -m unittest discover -s api -p 'test_*.py'   # 12 casos hoje
python3 -m py_compile api/server.py api/test_server.py
git diff --check                                     # espaço em branco/quebra de linha
docker build -t braco-digital-site:test .             # página/asset novo: o COPY precisa existir
docker build -t braco-digital-api:test api
```

Página nova ou CSS/JS novo exige o `docker build` da raiz: é o build que prova que o `COPY` foi
adicionado. `unittest` verde não prova nada sobre a publicação.

## 5. Depois do merge (verificação real, não presumida)

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://bracodigital.com.br/
curl -sS https://bracodigital.com.br/sitemap.xml | diff - sitemap.xml    # paridade produção×local
curl -sS https://bracodigital.com.br/<pagina>.html | sha256sum; sha256sum <pagina>.html
```

Deploy "feito" só é feito quando a página nova responde 200 **e** o conteúdo servido bate com o
local. Card `done` não é prova de deploy.

## 6. Onde não mexer sem card e backup

`nginx.conf`, `Dockerfile` (ambos), `api/server.py` no que toca rate limit/CORS/limites, configuração
do Dokploy e do Cloudflare Tunnel. Esses pontos derrubam o site ou a captação de lead; antes:
backup do arquivo, card aberto, e conferência depois com os comandos do §5.
