# Braço Digital — Fase 1 de conversão

Site institucional estático com uma API Python separada para receber pedidos de diagnóstico e enviá-los por e-mail via Resend. Não há Node, framework, banco de dados ou chave no código.

## Estrutura

- `index.html`: home completa, CSS e JavaScript inline.
- `assets/`: logos, favicon e imagem de compartilhamento.
- `Dockerfile`: imagem Nginx do site estático.
- `api/server.py`: `POST /api/diagnostico`, somente com Python stdlib.
- `api/Dockerfile`: imagem separada da API.
- `api/.env.example`: nomes e exemplos das variáveis, sem segredo real.
- `robots.txt` e `sitemap.xml`: arquivos de indexação.

## Desenvolvimento local

Site estático:

```bash
python3 -m http.server 8000
```

API, em outro terminal (a origem local precisa ser explicitamente liberada):

```bash
cd api
CONTACT_FORM_ALLOWED_ORIGINS=http://localhost:8000 \
CONTACT_FORM_TO_EMAIL=bvianna1@gmail.com \
CONTACT_FORM_FROM_EMAIL='Braço Digital <remetente@dominio-verificado.example>' \
RESEND_API_KEY='sua-chave-local' \
python3 server.py
```

O site chama `/api/diagnostico` no mesmo domínio. Para testar os dois juntos localmente, use um proxy reverso que encaminhe `/api/` à porta 8080; abrir apenas o servidor estático não encaminha a API.

## Variáveis da API

| Variável | Obrigatória | Uso |
|---|---:|---|
| `RESEND_API_KEY` | sim | Chave secreta do Resend, configurada fora do repositório. |
| `CONTACT_FORM_TO_EMAIL` | sim | Destino dos leads. Em produção: `bvianna1@gmail.com`. |
| `CONTACT_FORM_FROM_EMAIL` | sim | Remetente em domínio previamente verificado no Resend. |
| `CONTACT_FORM_ALLOWED_ORIGINS` | não | Lista separada por vírgulas. Padrão: domínio com e sem `www`. |
| `PORT` | não | Porta HTTP da API. Padrão: `8080`. |
| `HOST` | não | Interface da API. Padrão: `0.0.0.0`. |

Não use um e-mail arbitrário em `CONTACT_FORM_FROM_EMAIL`: o domínio precisa estar autorizado no Resend. O e-mail preenchido pelo visitante é aplicado apenas como `Reply-To`.

## Deploy no Dokploy — configuração externa pendente

O repositório entrega duas imagens independentes e **não contém a configuração do proxy do Dokploy**. No Dokploy:

1. mantenha o serviço web construído pelo `Dockerfile` da raiz;
2. crie um segundo serviço usando `api/Dockerfile` e configure nele as três variáveis obrigatórias;
3. mantenha a API apenas na rede interna, ouvindo na porta `8080`;
4. no domínio do site, crie uma regra de maior prioridade que encaminhe exatamente `/api/diagnostico` (e opcionalmente `/healthz` apenas para health check interno) ao serviço da API;
5. preserve todos os demais caminhos no serviço Nginx estático;
6. confirme que o proxy preserva o cabeçalho `Origin` e limita o corpo da requisição a 16 KB ou menos.

Como o rate limiting é simples e em memória, ele reinicia junto com o contêiner e funciona por instância. Em múltiplas réplicas, configure também limite no proxy. A API usa o IP da conexão com o proxy; não confia automaticamente em `X-Forwarded-For`, evitando spoofing. Para limite por visitante atrás do proxy, faça o rate limiting no próprio Dokploy/Traefik.

## Segurança e dados

A API aceita JSON de até 16 KB, valida e limita campos, remove caracteres de controle, usa honeypot, exige consentimento, restringe CORS e aplica até 5 tentativas por IP de conexão em 10 minutos. Os resultados da calculadora são recalculados no servidor. Logs operacionais não contêm IP, nome, e-mail, caminho ou conteúdo enviado.

Ainda não existe política de privacidade no repositório. Por isso o consentimento permanece sem link e usa o texto: “Ao enviar este formulário, você concorda com o uso das informações fornecidas exclusivamente para análise e contato sobre sua solicitação.” Pendência: revisar o consentimento juridicamente e criar e vincular uma política antes de uma campanha ampla.

## Validação

```bash
python3 -m unittest discover -s api -p 'test_*.py'
python3 -m py_compile api/server.py api/test_server.py
docker build -t braco-digital-site:test .
docker build -t braco-digital-api:test api
git diff --check
```

Nenhum passo deste README publica, faz push ou merge.
