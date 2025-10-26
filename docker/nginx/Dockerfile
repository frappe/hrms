# Since Coolify doesn't share volumes between containers,
# we need to build assets directly into the nginx image
FROM frappe/bench:latest as builder

WORKDIR /home/frappe

# Build a minimal frappe-bench with just the apps and assets
RUN bench init --skip-redis-config-generation frappe-bench && \
    cd frappe-bench && \
    bench get-app erpnext && \
    bench get-app hrms && \
    # Remove symlinks created by bench get-app
    rm -rf sites/assets && \
    mkdir -p sites/assets && \
    # Copy static assets from each app's public folder
    for app in frappe erpnext hrms; do \
        if [ -d "apps/$app/$app/public" ]; then \
            cp -r apps/$app/$app/public sites/assets/$app; \
        fi; \
    done && \
    # Build JS/CSS bundles
    bench build --production --hard-link --force && \
    # Ensure permissions are correct
    chmod -R 755 sites/assets

# Final nginx image with assets
FROM nginx:alpine

# Copy nginx configuration
COPY default.conf /etc/nginx/conf.d/default.conf

# Copy the built assets from builder
COPY --from=builder /home/frappe/frappe-bench/sites/assets /home/frappe/frappe-bench/sites/assets

# Create the sites directory structure and set permissions
RUN mkdir -p /home/frappe/frappe-bench/sites && \
    chmod -R 755 /home/frappe

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]