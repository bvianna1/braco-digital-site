# Braço Digital — site

Site estático de arquivo único. Não precisa de build, Node, banco nem backend.

## Conteúdo

```
index.html                    o site inteiro (HTML + CSS + JS)
assets/og-imagem.png          prévia ao compartilhar link (1200×630)
assets/favicon-180.png        ícone para iOS
assets/logo-completo.svg      logo com gradientes e estrias — usos médios/grandes
assets/logo-simples.svg       logo chapado — usos abaixo de 60px
assets/logo-completo-512.png  PNG transparente
assets/logo-completo-1024.png PNG transparente, alta resolução
assets/logo-simples-512.png   PNG transparente
assets/avatar-1000.png        quadrado com fundo escuro — perfil de Instagram/WhatsApp
```

## Antes de publicar

1. **Trocar o domínio nas meta tags.** No `<head>` do `index.html` há cinco ocorrências de
   `bracodigital.com.br`. Se o domínio for outro, substitua todas — senão a prévia do link
   no WhatsApp não carrega a imagem.
2. **Conferir o número do WhatsApp.** Aparece em três lugares: nos links `wa.me/5521988738405`
   e na constante `var ZAP` no final do arquivo, que monta a mensagem do formulário.

## Publicar

### Hostinger (hospedagem compartilhada)
Envie `index.html` e a pasta `assets/` para dentro de `public_html/`. Pronto.

### VPS com Nginx
```bash
sudo mkdir -p /var/www/bracodigital
sudo rsync -av ./ /var/www/bracodigital/ --exclude LEIA-ME.md
sudo chown -R www-data:www-data /var/www/bracodigital
```

```nginx
server {
    listen 80;
    server_name bracodigital.com.br www.bracodigital.com.br;
    root /var/www/bracodigital;
    index index.html;

    location / { try_files $uri $uri/ =404; }

    location ~* \.(png|svg|jpg|webp|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    gzip on;
    gzip_types text/html text/css application/javascript image/svg+xml;
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d bracodigital.com.br -d www.bracodigital.com.br
```

### Netlify / Vercel / Cloudflare Pages
Arraste a pasta inteira na interface. Sem configuração de build.

## Depois de publicar

Cole a URL no [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
e clique em "Scrape Again" — isso força WhatsApp e Facebook a lerem a prévia nova em vez
de uma versão em cache.

## Manutenção

- **Cores:** todas saem do bloco `:root` no topo do `<style>`. Trocar `--sinal` muda o acento
  do site inteiro.
- **Formulário:** hoje abre o WhatsApp com a mensagem pronta. Para receber por e-mail,
  troque o `form.addEventListener('submit', ...)` no fim do arquivo por um `action` de
  Formspree, Basin ou similar.
- **Calculadora:** a base de cálculo (48 semanas/ano, 1.760h por pessoa/ano) está na função
  `calcula()`.
