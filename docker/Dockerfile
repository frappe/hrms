FROM frappe/bench:latest

WORKDIR /home/frappe

# Pre-create the bench structure with apps
RUN bench init --skip-redis-config-generation frappe-bench && \
    cd frappe-bench && \
    bench set-mariadb-host mariadb && \
    bench set-redis-cache-host redis://redis:6379 && \
    bench set-redis-queue-host redis://redis:6379 && \
    bench set-redis-socketio-host redis://redis:6379 && \
    sed -i '/redis/d' ./Procfile && \
    sed -i '/watch/d' ./Procfile && \
    bench get-app erpnext && \
    bench get-app hrms

# Build production assets and bake them into the image
RUN cd frappe-bench && \
    echo "Building comprehensive production assets..." && \
    # Remove any existing symlinks first
    rm -rf sites/assets && \
    mkdir -p sites/assets && \
    # Copy static assets from each app's public folder
    for app in frappe erpnext hrms; do \
        if [ -d "apps/$app/$app/public" ]; then \
            echo "Copying $app static assets..." && \
            cp -r apps/$app/$app/public sites/assets/$app; \
        fi; \
    done && \
    # Build JS/CSS bundles
    bench build --production --hard-link --force && \
    chmod -R 755 sites/assets && \
    find sites/assets -type f -exec chmod 644 {} \; && \
    echo "Assets built and permissions set!"

# Copy init script with executable permissions
COPY --chmod=755 init.sh /home/frappe/init.sh

# Set default command
CMD ["/home/frappe/init.sh"]