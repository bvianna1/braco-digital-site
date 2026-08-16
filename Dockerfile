FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
COPY assets/ /usr/share/nginx/html/assets/
COPY robots.txt sitemap.xml politica-de-privacidade.html /usr/share/nginx/html/
EXPOSE 80
