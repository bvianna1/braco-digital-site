# LEIA-ME — contexto de projeto (Braço Digital)

**ATIVADO em 2026-10-29** (aprovado por Bruno).

O `AGENTS.md` está na **raiz** do repositório e é injetado pelo Hermes em toda sessão de agente com
cwd aqui. Verificado com o carregador real do Hermes (`discover_context_files`) em 2026-10-29:
`agents_md | AGENTS.md | 5642 chars`. Os três documentos de apoio ficam neste diretório.

| Arquivo | Papel |
|---|---|
| `AGENTS.md` (na raiz) | regras para qualquer agente que trabalhe no repositório |
| `PROJECT.md` | o que é o produto, escopo, arquitetura, riscos |
| `STATUS.md` | snapshot **datado**, com evidência ao vivo |
| `DECISIONS.md` | decisões comprovadas, com evidência e o que está em aberto |

## Por que o `AGENTS.md` fica na raiz

O Hermes injeta o `AGENTS.md` do **diretório de trabalho**. Neste repositório, é a raiz que as sessões
de agente usam como cwd. Por isso a proposta ficou inerte com sufixo `.proposta` até a aprovação —
bastava um `cp` para o documento passar a valer.

## Segurança da publicação

O `Dockerfile` da raiz copia arquivos **explicitamente** (não usa `COPY . .`). Portanto `AGENTS.md` e
`documentos/` **não** entram na imagem Nginx e **não** ficam públicos. Reconferir se o `Dockerfile`
mudar: um `COPY . .` publicaria estes arquivos internos.

## Manutenção

- **`STATUS.md`**: atualizar por lote relevante ou incidente — nunca com base em card `done`. Toda
  linha precisa de comando reexecutável; o que não foi reconferido vai para "não verificado".
- **`DECISIONS.md`**: só entra decisão comprovada (código, medição, card com resultado) ou decisão de
  produto do Bruno. Discussão em aberto fica marcada como `em aberto`.
- **`AGENTS.md`**: só regra transversal. Regra de conteúdo/execução mora na fonte canônica (§3) — não
  duplicar aqui.
- **O Kanban continua sendo a fonte das tarefas** (board `site`).

## Histórico da adoção

1. **29/10/2026** — Bruno autorizou aplicar ao site o padrão já ativado no clipping.
2. **29/10/2026** — quatro documentos escritos como `.proposta.md`, inertes.
3. **29/10/2026** — teste de passagem de bastão em sessão sem histórico, lendo **apenas** os quatro
   documentos: passou nos cinco itens e declarou as lacunas. As duas mais úteis foram fechadas com
   medição: estado dos clones paralelos (todos **atrás** de `origin/main`, nenhum à frente) e o
   ponteiro para o plano de deploy automático, que vive **fora** deste repositório.
4. **29/10/2026** — **ativados**: `AGENTS.md` promovido para a raiz, os três renomeados neste
   diretório, carregador do Hermes confirmando a injeção.

## O que este padrão não faz

- Não altera página, cor, texto, CSS, API, `nginx.conf`, Dokploy ou Cloudflare.
- Não substitui o `README.md` (referência técnica) nem o código.
- Não dispensa evidência: card `done` continua não sendo prova de deploy nem de saúde atual.
