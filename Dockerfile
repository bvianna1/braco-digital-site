FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
COPY assets/ /usr/share/nginx/html/assets/
COPY css/ /usr/share/nginx/html/css/
COPY robots.txt sitemap.xml politica-de-privacidade.html /usr/share/nginx/html/
COPY financeiro.html /usr/share/nginx/html/
COPY administrativo.html /usr/share/nginx/html/
COPY relatorios.html /usr/share/nginx/html/
EXPOSE 80
