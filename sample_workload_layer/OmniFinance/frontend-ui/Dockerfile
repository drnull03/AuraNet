FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Inject Nginx routing configuration for K8s DNS resolution
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy our polished OmniFinance dashboard
COPY index.html /usr/share/nginx/html/index.html

EXPOSE 80

# Start Nginx (Notice the strict double-quotes!)
CMD ["nginx", "-g", "daemon off;"]