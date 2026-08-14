# Operação do site Braço Digital

As instruções atuais de arquitetura, desenvolvimento, variáveis, segurança, testes e proxy no Dokploy estão no [README.md](README.md).

Resumo importante: o site continua estático, mas o formulário exige o serviço separado em `api/` e uma regra externa no Dokploy para encaminhar `POST /api/diagnostico`. Configure `RESEND_API_KEY`, `CONTACT_FORM_TO_EMAIL=bvianna1@gmail.com` e `CONTACT_FORM_FROM_EMAIL` somente no ambiente da API. Não há chave no repositório.

Pendência de conteúdo: o consentimento permanece sem link porque ainda não existe política de privacidade. Revisar juridicamente o texto atual e criar e vincular a política antes de uma campanha ampla.
