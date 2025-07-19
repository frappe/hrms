FROM frappe/bench:latest

# Copy init script with executable permissions
COPY --chmod=755 init.sh /home/frappe/init.sh

# Set working directory
WORKDIR /home/frappe

# Set default command
CMD ["/home/frappe/init.sh"]