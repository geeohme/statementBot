FROM nginx:alpine

# Static frontend
COPY index.html /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/
COPY app.js     /usr/share/nginx/html/

# Site config (proxies /api/* to backend)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
