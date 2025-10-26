# Simple nginx proxy - all assets served from frappe container
FROM nginx:alpine

# Copy nginx configuration
COPY default.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]