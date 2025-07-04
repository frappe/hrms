# Docker Setup for Local Development

This setup allows you to run HRMS locally without relying on GitHub repositories.

## Files Created

- `docker-compose.local.yml` - Docker compose configuration for local development
- `init-local.sh` - Initialization script that uses local repositories

## Prerequisites

1. Ensure you have the following directory structure:
   ```
   parent-directory/
   ├── hrms/           # This repository
   ├── erpnext/        # ERPNext repository (optional - will fallback to GitHub)
   └── frappe/         # Frappe framework (optional)
   ```

2. Make sure ERPNext is cloned locally if you want to avoid GitHub:
   ```bash
   git clone https://github.com/frappe/erpnext.git ../erpnext
   ```

## Usage

### For Local Development (Recommended)
```bash
cd docker
docker-compose -f docker-compose.local.yml up
```

### For Original Setup (Uses GitHub)
```bash
cd docker
docker-compose up
```

## What's Different

- **Local Setup**: Uses local repositories mounted as volumes
- **Original Setup**: Downloads apps from GitHub during initialization

## Access

- HRMS: http://localhost:8000
- Database: localhost:3306 (user: root, password: 123)
- Redis: localhost:6379

## Troubleshooting

1. **Permission Issues**: Make sure `init-local.sh` is executable:
   ```bash
   chmod +x docker/init-local.sh
   ```

2. **ERPNext Not Found**: If ERPNext is not found locally, the script will fallback to GitHub installation.

3. **Database Issues**: Clear volumes if you need a fresh start:
   ```bash
   docker-compose -f docker-compose.local.yml down -v
   ```
