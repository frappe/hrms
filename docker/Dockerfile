FROM frappe/bench:v5.22.8

# Switch to the frappe user to avoid permission errors
USER frappe
WORKDIR /home/frappe

# Set Node path
ENV PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"

RUN bench init --skip-redis-config-generation --frappe-branch v15.95.0 frappe-bench

# Set the working directory to the new bench
WORKDIR /home/frappe/frappe-bench

# Use HRMS's latest v15 version
RUN bench get-app --branch v15.95.0 erpnext
RUN bench get-app --branch v15.55.0 hrms

# Use containers instead of localhost
RUN bench set-mariadb-host mariadb && \
    bench set-redis-cache-host redis:6379 && \
    bench set-redis-queue-host redis:6379 && \
    bench set-redis-socketio-host redis:6379

# Remove redis and watch from Procfile
RUN sed -i '/redis/d' ./Procfile && sed -i '/watch/d' ./Procfile

# COPY DEMO Data
COPY --chown=frappe:frappe ./hrms/demo_data/. /home/frappe/frappe-bench/apps/hrms/hrms/demo_data/

COPY --chown=frappe:frappe docker/entrypoint.sh /home/frappe/entrypoint.sh
RUN chmod +x /home/frappe/entrypoint.sh

ENTRYPOINT ["/home/frappe/entrypoint.sh"]
