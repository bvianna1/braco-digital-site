# PROJECT — Braço Digital

> **Status: ATIVO desde 2026-10-29** (aprovado por Bruno). Documento de contexto do projeto.
> Complementa `README.md` (referência técnica) e é carregado por referência a partir do `AGENTS.md`
> da raiz.
> Última revisão: **2026-10-29**.

## 1. O que é

Site institucional **estático** com uma **API separada** de captação de leads: o formulário de
diagnóstico da home envia os dados para `POST /api/diagnostico`, que valida e encaminha por e-mail
(Resend).

- **Cliente / operador:** Braço Digital (dono: Bruno Vianna).
- **Domínio:** `https://bracodigital.com.br` (apex, com e sem `www`).
- **Repositório canônico:** `~/workspace/braco-digital-site` — `origin` GitHub
  `bvianna1/braco-digital-site`, produção na branch **`main`**.
- **Máquina de deploy:** VPS via **Dokploy** (dois serviços: site Nginx e API Python).

## 2. Objetivo

Gerar **pedido de diagnóstico** qualificado — não é vitrine. A home explica a oferta, o visitante
conta o problema e o lead cai no e-mail. Páginas internas existem para sustentar a mesma oferta em
três frentes já em produção: **financeiro/back-office**, **administrativo** e **relatórios**. A
página `osc.html` é a versão piloto do padrão de página interna (fase 1 do portal).

## 3. Escopo

**Páginas publicadas (6):** `index.html` (home), `osc.html`, `financeiro.html`,
`administrativo.html`, `relatorios.html`, `politica-de-privacidade.html`.

**API:** `POST /api/diagnostico` — JSON até 16 KB, honeypot, consentimento obrigatório, CORS por
lista de origens, rate limit de **5 requisições por IP de conexão em 10 minutos**, persistido em
arquivo e recalculado no servidor. `GET /healthz` existe para health check **interno**
(não é exposto no domínio público).

**Fora de escopo hoje:** blog (card `t_495654df`, bloqueado), e-commerce, banco de dados,
login/área de cliente. Páginas de "soluções reais" (clipping, QGD, pagamentos) estão em card
`t_6f1ffee8`, ainda não publicadas.

## 4. Arquitetura

```
visitante ── HTTPS (Cloudflare) ── Tunnel ── Dokploy
                                             ├── nginx:alpine  → serve os 6 HTML + assets
                                             └── api Python    → POST /api/diagnostico (16 KB, 5/600s)
                                                                  └── Resend → e-mail do Bruno
```

- **Site = arquivos estáticos.** Sem Node, sem framework, sem build de front. Cada página é um
  `HTML` com CSS/JS externos em `css/*.v2.css` e `js/app.v2.js` (as seis páginas referenciam os v2).
- **API = Python stdlib**, imagem separada, sem dependência externa e sem estado além do arquivo de
  rate limit em `/var/lib/braco-digital-api/rate-limit.json` (volume nomeado no Dokploy).
- **Proxy:** o site chama `/api/diagnostico` no mesmo domínio; o Dokploy roteia esse caminho para a
  API mantendo todo o resto no Nginx estático.
- **Segurança:** CSP sem `unsafe-inline` (GA4 e Google Fonts liberados explicitamente), headers de
  permissão, cache agressivo por bloco.
- **Analytics:** GA4 `G-P51CNDWHR2` nas seis páginas.

## 5. Cadência

Não há job agendado. O site muda **por demanda**, via card:

1. card no board `site` → 2. implementação (Codex) → 3. auditoria read-only (`paulo`) →
4. merge em `main` → 5. deploy automático → 6. verificação em produção (§5 do `AGENTS.md`).

## 6. Agentes e papéis

| Agente | Papel |
|---|---|
| **Codex** (CLI, `gpt-5.6-sol`) | implementa código/página/API |
| **Jony** | especifica, orquestra, revisa e faz merge/push/deploy |
| **Paulo** | auditoria **somente leitura**, antes do merge ou logo após o lote |
| **Beth** | executou a fase 2 (versão B das internas) |
| **Orquestrador (`default`)** | arquitetura, decisões, cards, infra |
| **Bruno** | aprova visual e conteúdo; decide o que vai ao ar |

## 7. Riscos conhecidos

- **Conteúdo sem prova** (dado inventado) destrói credibilidade mais rápido que um bug de layout.
- **Deploy presumido**: merge sem verificação em produção deixa a mudança "feita mas não no ar".
- **Clones paralelos** do repositório já produziram divergência; o canônico é um só.
- **README desatualizado** induz erro de quem chega novo — ver `STATUS.md` §3.
