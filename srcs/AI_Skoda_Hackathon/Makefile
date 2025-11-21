.PHONY: help install start stop restart logs clean build seed status test-api shell-backend shell-frontend db-reset

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Default target - show help
help:
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(BLUE)║        SkillBridge AI - Docker Management Commands        ║$(RESET)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@echo "$(GREEN)Quick Start:$(RESET)"
	@echo "  $(YELLOW)make start$(RESET)        - Start all services (database, backend, frontend)"
	@echo "  $(YELLOW)make stop$(RESET)         - Stop all services"
	@echo "  $(YELLOW)make logs$(RESET)         - View all service logs"
	@echo ""
	@echo "$(GREEN)Setup Commands:$(RESET)"
	@echo "  $(YELLOW)make install$(RESET)      - Install Docker if not present"
	@echo "  $(YELLOW)make build$(RESET)        - Build Docker images"
	@echo "  $(YELLOW)make seed$(RESET)         - Import real data from Excel files"
	@echo "  $(YELLOW)make db-reset$(RESET)     - Reset database and re-import data"
	@echo ""
	@echo "$(GREEN)Management Commands:$(RESET)"
	@echo "  $(YELLOW)make restart$(RESET)      - Restart all services"
	@echo "  $(YELLOW)make status$(RESET)       - Check status of all containers"
	@echo "  $(YELLOW)make clean$(RESET)        - Stop and remove all containers + volumes"
	@echo ""
	@echo "$(GREEN)Development Commands:$(RESET)"
	@echo "  $(YELLOW)make logs-backend$(RESET) - View backend logs only"
	@echo "  $(YELLOW)make logs-frontend$(RESET) - View frontend logs only"
	@echo "  $(YELLOW)make shell-backend$(RESET) - Open shell in backend container"
	@echo "  $(YELLOW)make shell-frontend$(RESET) - Open shell in frontend container"
	@echo "  $(YELLOW)make test-api$(RESET)     - Test backend API endpoints"
	@echo ""
	@echo "$(GREEN)Access Points:$(RESET)"
	@echo "  Frontend:  $(BLUE)http://localhost:8080$(RESET)"
	@echo "  Backend:   $(BLUE)http://localhost:3000$(RESET)"
	@echo "  Login:     $(BLUE)http://localhost:8080/login$(RESET)"
	@echo ""
	@echo "$(GREEN)Login Credentials:$(RESET)"
	@echo "  Manager:   $(YELLOW)karel.vagner@skoda.cz$(RESET) / password123"
	@echo "  Employee:  $(YELLOW)martin.svoboda@skoda.cz$(RESET) / password123"
	@echo ""

# Install Docker (macOS only)
install:
	@echo "$(BLUE)📦 Installing Docker Desktop...$(RESET)"
	@if command -v brew >/dev/null 2>&1; then \
		brew install --cask docker; \
		echo "$(GREEN)✅ Docker installed! Please start Docker Desktop from Applications$(RESET)"; \
	else \
		echo "$(RED)❌ Homebrew not found. Install from: https://brew.sh$(RESET)"; \
		exit 1; \
	fi

# Start all services
start:
	@echo "$(BLUE)🚀 Starting SkillBridge AI...$(RESET)"
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)❌ Docker is not running. Please start Docker Desktop first.$(RESET)"; \
		exit 1; \
	fi
	@docker-compose up -d
	@echo ""
	@echo "$(GREEN)✅ Services started!$(RESET)"
	@echo ""
	@echo "$(YELLOW)⏳ Waiting for services to be ready...$(RESET)"
	@sleep 5
	@$(MAKE) status
	@echo ""
	@echo "$(GREEN)🌐 Access your application:$(RESET)"
	@echo "   Frontend: $(BLUE)http://localhost:8080$(RESET)"
	@echo "   Login:    $(BLUE)http://localhost:8080/login$(RESET)"
	@echo ""
	@echo "$(YELLOW)💡 Run 'make seed' to import real data from Excel files$(RESET)"
	@echo "$(YELLOW)💡 Run 'make logs' to view service logs$(RESET)"

# Build Docker images
build:
	@echo "$(BLUE)🔨 Building Docker images...$(RESET)"
	@docker-compose build
	@echo "$(GREEN)✅ Build complete!$(RESET)"

# Stop all services
stop:
	@echo "$(BLUE)🛑 Stopping services...$(RESET)"
	@docker-compose down
	@echo "$(GREEN)✅ All services stopped$(RESET)"

# Restart all services
restart:
	@echo "$(BLUE)🔄 Restarting services...$(RESET)"
	@docker-compose restart
	@echo "$(GREEN)✅ Services restarted$(RESET)"

# View logs
logs:
	@docker-compose logs -f

logs-backend:
	@docker-compose logs -f backend

logs-frontend:
	@docker-compose logs -f frontend

logs-postgres:
	@docker-compose logs -f postgres

# Clean everything (remove containers and volumes)
clean:
	@echo "$(RED)🧹 Cleaning up Docker containers and volumes...$(RESET)"
	@docker-compose down -v
	@echo "$(GREEN)✅ Cleanup complete$(RESET)"

# Import real data from Excel files
seed:
	@echo "$(BLUE)📊 Importing real dataset from Excel files...$(RESET)"
	@docker-compose exec -T backend npm run db:seed:real
	@echo ""
	@echo "$(GREEN)✅ Data import complete!$(RESET)"
	@echo ""
	@echo "$(GREEN)🔐 Login credentials:$(RESET)"
	@echo "   Manager:  $(YELLOW)karel.vagner@skoda.cz$(RESET) / password123"
	@echo "   Employee: $(YELLOW)martin.svoboda@skoda.cz$(RESET) / password123"

# Reset database and re-import data
db-reset:
	@echo "$(YELLOW)🔄 Resetting database...$(RESET)"
	@docker-compose exec -T backend npx prisma migrate reset --force
	@$(MAKE) seed

# Check status of containers
status:
	@echo "$(BLUE)📊 Container Status:$(RESET)"
	@docker-compose ps

# Test API endpoints
test-api:
	@echo "$(BLUE)🧪 Testing Backend API...$(RESET)"
	@echo ""
	@echo "$(YELLOW)Testing Manager Login:$(RESET)"
	@curl -s -X POST http://localhost:3000/api/auth/login \
		-H "Content-Type: application/json" \
		-d '{"email":"karel.vagner@skoda.cz","password":"password123"}' | \
		grep -o '"token":"[^"]*"' && echo " $(GREEN)✅$(RESET)" || echo " $(RED)❌$(RESET)"
	@echo ""
	@echo "$(YELLOW)Testing Employee Login:$(RESET)"
	@curl -s -X POST http://localhost:3000/api/auth/login \
		-H "Content-Type: application/json" \
		-d '{"email":"martin.svoboda@skoda.cz","password":"password123"}' | \
		grep -o '"token":"[^"]*"' && echo " $(GREEN)✅$(RESET)" || echo " $(RED)❌$(RESET)"
	@echo ""

# Run full CI tests (like in GitHub Actions)
test-ci:
	@echo "$(BLUE)🧪 Running CI Test Suite...$(RESET)"
	@./test-ci.sh

# Open shell in backend container
shell-backend:
	@docker-compose exec backend sh

# Open shell in frontend container
shell-frontend:
	@docker-compose exec frontend sh

# Open Prisma Studio
prisma-studio:
	@echo "$(BLUE)🎨 Opening Prisma Studio...$(RESET)"
	@docker-compose exec backend npx prisma studio

# Check database users
db-users:
	@echo "$(BLUE)👥 Users in database:$(RESET)"
	@docker-compose exec -T backend node -e "const { PrismaClient } = require('@prisma/client'); const prisma = new PrismaClient(); prisma.user.findMany({ select: { email: true, firstName: true, lastName: true, role: true }, take: 15 }).then(users => { console.log('\nTotal users:', users.length); users.forEach(u => console.log('  📧', u.email, '(' + u.role + ')')); prisma.\$$disconnect(); });"

# Full setup from scratch
setup: clean build start seed
	@echo ""
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(GREEN)║          🎉 Setup Complete! Ready to use! 🎉              ║$(RESET)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@echo "$(GREEN)🌐 Open in browser:$(RESET) $(BLUE)http://localhost:8080/login$(RESET)"
	@echo ""
	@echo "$(GREEN)🔐 Login credentials:$(RESET)"
	@echo "   Manager:  $(YELLOW)karel.vagner@skoda.cz$(RESET) / password123"
	@echo "   Employee: $(YELLOW)martin.svoboda@skoda.cz$(RESET) / password123"
	@echo ""
