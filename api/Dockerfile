FROM python:3.12-alpine

WORKDIR /app
COPY server.py /app/server.py

RUN apk add --no-cache curl \
 && addgroup -S app && adduser -S -G app app
USER app

ENV PORT=8080
EXPOSE 8080
CMD ["python", "/app/server.py"]
