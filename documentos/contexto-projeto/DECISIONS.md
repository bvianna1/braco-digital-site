# DECISIONS — Braço Digital

> **Status: ATIVO desde 2026-10-29** (aprovado por Bruno). Registro de **decisões já tomadas**, cada
> uma com a evidência que a sustenta. Carregado por referência a partir do `AGENTS.md` da raiz.
>
> **Regra deste arquivo:** só entra decisão **comprovada** (código, medição, card com resultado) ou
> decisão de produto do Bruno. O que ainda está em discussão entra marcado como `em aberto` — nunca
> como se já valesse. Não é changelog: é o que um agente precisa saber para **não redecidir**.
>
> Legenda: **adotada** (vale hoje) · **em aberto** (falta decisão do Bruno).

---

## D1 — Produção é `origin/main`, e o deploy é automático · adotada

**Decisão:** a branch `main` do `origin` é o que está no ar. Merge em `main` dispara deploy; não
existe etapa manual de publicação no caminho normal.

**Evidência:** cards `t_e5fbd70c` (+ `t_75ce2653`, `t_e08d4445`, `t_f5799a44`, `t_d55ce48c`) —
"Restaurar deploy automático sem abrir porta 3000 (agente local pull-based)": agente de polling,
serviço systemd endurecido com usuário dedicado, teste ponta-a-ponta e runbook de rollback.
Verificação de hoje: sitemap servido **idêntico** ao local e `osc.html` com o **mesmo sha256**
(`e331e3b5…`).

**Consequência:** commit em `main` é ato de publicação. Não commitar "só para guardar".

## D2 — Cloudflare Tunnel na frente do site · adotada

**Decisão:** o domínio passa por Cloudflare Tunnel; o IP de origem não é exposto e o painel do
Dokploy não fica público.

**Evidência:** card `t_11f27bc5` ("Colocar site no Cloudflare Tunnel (ocultar IP origem, proteger
painel Dokploy)"), concluído. O domínio responde 200 em `https://bracodigital.com.br/` (medido hoje).

**Consequência:** não existe caminho "direto ao IP" para teste; qualquer verificação é pelo domínio.

## D3 — Auditoria read-only antes do merge; executor ≠ auditor · adotada

**Decisão:** quem implementa não aprova. Toda mudança de site/API passa por auditoria **somente
leitura** do perfil `paulo` antes do merge — ou logo após o lote, quando o Bruno autorizar o inverso.
A auditoria aponta; não edita.

**Evidência:** card `t_9e0bd7f1` (paulo, "Auditoria read-only da higiene SEO antes do merge") →
`t_32975b86` (jony, "Merge… push (deploy) e verificação em produção"); mesmo par em `t_517e9402` →
`t_712ac97e`. Histórico do board mostra o padrão repetido.

## D4 — CSP endurecida, sem `unsafe-inline` · adotada

**Decisão:** `nginx.conf` serve CSP explícita com origens nomeadas e **nenhum** `unsafe-inline` /
`unsafe-eval`. GA4 e Google Fonts são liberados por origem, não por permissão ampla.

**Evidência:** `grep -c 'unsafe-inline' nginx.conf` → **0**; a política nomeia
`https://www.googletagmanager.com`, `https://www.google-analytics.com`, `https://fonts.googleapis.com`,
`https://fonts.gstatic.com`; inclui `object-src 'none'` e `frame-ancestors 'self'`. Cards:
`t_45a5be7f` (endurecer CSP pós-PASS) e histórico de correção de `connect-src` para GA4.

**Consequência:** script/estilo inline novo quebra em produção. Se precisar, o ajuste é na política e
precisa de auditoria — nunca relaxar para `*`.

## D5 — Rate limit fixo, persistido em arquivo, por IP de conexão · adotada

**Decisão:** 5 requisições por IP de conexão em 10 minutos, contador persistido em
`/var/lib/braco-digital-api/rate-limit.json` (volume nomeado no Dokploy), usando o IP da conexão com
o proxy e **sem confiar** em `X-Forwarded-For`.

**Evidência:** `README.md` §Deploy e §Volume persistente; `api/server.py`; cards `t_45a345e1`
("rate limit além da memória") e `t_d2d0b5cd` ("volume persistente do rate-limit em runtime").
Teste: 12 casos em `api/test_server.py`, verdes hoje.

**Consequência:** em múltiplas réplicas cada instância teria seu próprio contador — hoje é 1
instância. Se escalar, o limite também precisa existir no proxy.

## D6 — API separada, Python stdlib, sem banco · adotada

**Decisão:** a API é um serviço próprio (imagem `api/Dockerfile`), só com biblioteca padrão, sem
banco e sem estado além do arquivo de rate limit. O site continua estático.

**Evidência:** `api/server.py` + `api/Dockerfile` + `README.md` §Estrutura; o site chama
`/api/diagnostico` no mesmo domínio e o Dokploy roteia apenas esse caminho para a API.
`GET /healthz` é interno — no domínio público devolve **404** (medido hoje).

**Consequência:** não introduzir framework/DB sem decisão nova; a simplicidade é o que mantém o
deploy previsível.

## D7 — Nunca testar carga contra produção · adotada

**Decisão:** o rate limit é validado só em teste local/CI. Carga contra o domínio público ou contra a
API no ar está fora de escopo.

**Evidência:** `README.md` §Validação ("carga pública fica fora do escopo desta API"), endossado pelo
commit `dc0d534` do repo `braco-digital-api-ratelimit`: "carga pública fica fora do escopo (rate
limit só em teste local/CI)".

## D8 — `lastmod` do sitemap = data do último commit de conteúdo da página · adotada

**Decisão:** o `lastmod` de cada URL reflete quando aquele conteúdo mudou — não a data do deploy nem
a data de hoje.

**Evidência:** commits `ddbf82b` e `af87fd2` ("lastmod do sitemap para 2026-10-18" citando o último
commit de conteúdo de cada página, ex.: `d43a006` para a home); card `t_f0fa6345` abriu exatamente
porque o `lastmod` da home estava em 2026-08-31 com conteúdo de 2026-09-03.

## D9 — Conteúdo sem prova e regras editoriais do Bruno · adotada

**Decisão:** nenhum dado inventado (CNPJ, número, cliente, depoimento, LinkedIn, foto). Rodapé usa
**"Soluções"** (não "Ofertas"); **terceiro setor** aparece nas áreas, não no menu. Copy em PT-BR,
escaneável no celular, sem promessa de "grátis".

**Evidência:** decisões de produto do Bruno registradas nas sessões de construção do site; o card
`t_6f1ffee8` ("páginas de soluções reais — clipping, QGD, pagamentos") segue a mesma linha de não
inventar oferta.

**Consequência:** proposta de conteúdo sem fonte verificável não entra, mesmo que soe melhor.

## D10 — Versão B das páginas internas, no padrão do piloto `osc.html` · adotada

**Decisão:** as internas (`financeiro`, `administrativo`, `relatorios`) seguem o padrão de estrutura
e conversão validado no piloto `osc.html` — mesma arquitetura de seção, `og:description` alinhada ao
lead da página.

**Evidência:** cards `t_ce07aa71` (versão B das três internas) e `t_3aca6439` (correção do
`og:description` do financeiro + merge/push); merges `3c20cfa` e `af87fd2` no `main`.

## D11 — Versionamento de asset contra cache do Cloudflare · adotada (medida em 2026-11-13)

**Decisão:** o endereço do CSS/JS leva token de versão (`?v=<7 primeiros caracteres do sha256 do
arquivo>`), porque o Nginx serve esses arquivos com `cache-control: max-age=31536000, immutable` —
sem trocar o endereço, o visitante que já visitou não recebe a versão nova.

**Estado medido (2026-11-13):** home em `css/index.v2.css?v=f4e66e1`; `osc`, `financeiro`,
`administrativo` e `relatorios` em `css/paginas.v2.css?v=seoh1`; `politica-de-privacidade.html`
estava **sem** token e foi corrigido para `?v=d9f2841`. O token `seoh1` é artesanal — migrar para o
padrão de hash quando aquele arquivo mudar de novo.

**Estado após normalização (2026-11-13, lote `site/tokens-versao-hashes`):** `js/app.v2.js?v=2724a85`
e `assets/marca/logo-light.svg?v=5dd0c38` nas seis páginas, `css/index.v2.css?v=5b64311` na home —
todos iguais ao sha7 do sha256 do arquivo. Única exceção: `?v=seoh1` nas quatro páginas que usam
`paginas.v2.css`. Os tokens `f4e66e1` e `a886879` nunca foram hash do arquivo que acompanhavam: o
`f4e66e1` nasceu em commit posterior à última mudança de conteúdo do CSS, ou seja, o endereço nunca
apontou para o conteúdo servido — o cache imutável de um ano podia servir CSS velho.

**Correção de registro:** a versão anterior desta decisão dizia que "nenhuma das seis páginas usa
query de versão" e trazia `grep → 0 ocorrências`. **Era falso**: a regex de medição exigia dígitos
após `v=` e não reconheceu tokens hexadecimais/alfanuméricos. Fica o aprendizado: ao afirmar
ausência, testar o padrão contra um exemplo positivo antes de concluir.

**Consequência:** a regra de troca de token está no `AGENTS.md` §2. Quem editar CSS/JS e esquecer de
trocar o token publica uma página que parece quebrada para quem tem cache.

## D12 — `README.md` desatualizado · resolvida em 2026-11-13

**Situação anterior:** o README descrevia um site de uma página com CSS/JS inline e afirmava que não
existia política de privacidade. A realidade medida em 2026-10-29: 6 páginas, assets externos `v2`,
`politica-de-privacidade.html` publicada e no sitemap.

**Resolução (2026-11-13):** o README passou a listar as 6 páginas, os assets externos com token de
versão e a política existente e linkada no consentimento. Mantém-se como referência técnica
(API/deploy); regra transversal continua no `AGENTS.md` e o estado datado no `STATUS.md`.

**Complemento (2026-11-13, lote `site/tokens-versao-hashes`):** a frase do README sobre "token de
versão (`?v=<hash>`)" ainda era falsa quando foi escrita, porque `js/app.v2.js` não tinha token e dois
tokens não eram hash. Passou a ser verdadeira na normalização descrita em D11; a exceção `seoh1` está
declarada no próprio README. A citação "Resolução ANPD 2/2022", sem fonte no repositório, foi
substituída pela data e pelo commit que comprovam o texto (`67904dd`); a revisão jurídica pendente
continua declarada.
