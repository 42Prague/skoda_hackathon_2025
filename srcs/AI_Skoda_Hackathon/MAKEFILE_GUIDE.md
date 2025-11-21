# Makefile Commands Reference

## Quick Reference

| Command | Description |
|---------|-------------|
| `make help` | Show all commands |
| `make setup` | Complete setup (clean + build + start + seed) |
| `make start` | Start all services |
| `make stop` | Stop all services |
| `make restart` | Restart services |
| `make logs` | View all logs |
| `make seed` | Import data from Excel files |
| `make status` | Check container status |
| `make clean` | Remove all containers and data |
| `make test-api` | Test backend API |
| `make db-users` | Show database users |

---

## Common Workflows

### First Time Setup
```bash
make setup
```

### Daily Start
```bash
make start
```

### View Logs
```bash
make logs
# Press Ctrl+C to exit
```

### Fresh Restart
```bash
make clean
make setup
```

### Troubleshooting
```bash
make status      # Check what's running
make logs        # See errors
make test-api    # Test backend
make clean       # Nuclear option
```

---

## Individual Service Logs

```bash
make logs-backend    # Backend only
make logs-frontend   # Frontend only
make logs-postgres   # Database only
```

---

## Development

```bash
make shell-backend   # Open terminal in backend container
make shell-frontend  # Open terminal in frontend container
make prisma-studio   # Open Prisma Studio (database GUI)
```

---

## Database

```bash
make seed         # Import real data
make db-reset     # Reset and re-import
make db-users     # List all users
```

---

## Examples

### Morning Routine
```bash
make start
make logs  # Check everything is running
# Ctrl+C to exit logs
open http://localhost:8080/login
```

### After Code Changes
```bash
make restart
```

### Clean Start
```bash
make clean && make setup
```

---

**Full help:** Run `make` or `make help`
