# CI/CD Documentation

## Overview

This project uses **GitHub Actions** for Continuous Integration (CI). The workflows automatically test and build the application on every push and pull request, ensuring code quality and catching bugs early.

> **Note:** We focus on CI (testing) rather than CD (deployment) since the project runs locally with Docker. See `FREE_HOSTING_OPTIONS.md` if you want to deploy later.

## 📋 Workflows

### 1. CI Pipeline (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs:**

#### Backend Tests
- ✅ Sets up PostgreSQL test database
- ✅ Installs dependencies
- ✅ Runs Prisma migrations
- ✅ TypeScript compilation check
- ✅ Runs backend tests
- ✅ Code formatting and linting

#### Frontend Tests
- ✅ Installs dependencies
- ✅ TypeScript compilation check
- ✅ ESLint checks
- ✅ Runs frontend tests
- ✅ Production build verification

#### Docker Build Tests
- ✅ Builds backend Docker image
- ✅ Builds frontend Docker image
- ✅ Uses GitHub Actions cache for faster builds

#### Integration Tests
- ✅ Starts all services with docker-compose
- ✅ Runs database seed
- ✅ Tests API endpoints (health, login)
- ✅ Verifies service connectivity

#### Code Quality & Security
- ✅ Dependency vulnerability scanning
- ✅ Secret detection with TruffleHog

#### Deployment Readiness
- ✅ Verifies all required files exist
- ✅ Confirms project is ready for deployment (if needed later)

### 2. Pull Request Checks (`pr-checks.yml`)

**Triggers:**
- Pull request opened, synchronized, or reopened

**Jobs:**
- 📝 Validates PR title format (semantic versioning)
- 📊 Detects changed files (backend/frontend/docker)
- 💬 Posts analysis comment on PR
- 📏 Checks PR size and warns if too large

## 🚀 Setup Instructions

### Step 1: Enable GitHub Actions

1. Go to your repository settings
2. Navigate to **Actions** → **General**
3. Enable "Allow all actions and reusable workflows"

### Step 2: First Push (No Secrets Needed!)

Your workflows are already active! Just push:

```bash
git push origin main
```

### Step 3: Monitor Workflows

1. Go to **Actions** tab in your repository
2. Watch the workflows run
3. Check for any failures and fix them

## 📊 Workflow Status Badges

Add these badges to your README.md:

```markdown
![CI Pipeline](https://github.com/ayermeko/AI_Skoda_Hackathon/workflows/CI%2FCD%20Pipeline/badge.svg)
![Deployment](https://github.com/ayermeko/AI_Skoda_Hackathon/workflows/Deploy%20to%20Production/badge.svg)
```

## 🔧 Local Testing

Test your workflows locally before pushing:

### Test backend build:
```bash
cd backend
npm install
npm run build
npm run lint
```

### Test frontend build:
```bash
cd skillbridge-ai
npm install
npm run build
npm run lint
```

### Test Docker builds:
```bash
# Backend
docker build -t skillbridge-backend:test ./backend

# Frontend
docker build -t skillbridge-frontend:test ./skillbridge-ai
```

### Test integration:
```bash
make setup    # Builds and starts all services
make test-api # Tests API endpoints
make stop     # Stops services
```

## 📝 Commit Message Format

For PR title validation, use conventional commit format:

```
feat: add new feature
fix: fix bug
docs: update documentation
style: code formatting
refactor: code refactoring
perf: performance improvement
test: add tests
build: build system changes
ci: CI/CD changes
chore: other changes
```

## 🐛 Troubleshooting

### Workflow fails on backend-test

**Issue:** Database connection errors
**Solution:** Check PostgreSQL service configuration in `ci.yml`

### Workflow fails on docker-build

**Issue:** Docker build context errors
**Solution:** Verify Dockerfiles have correct paths

### Integration tests fail

**Issue:** Services not starting properly
**Solution:** Increase sleep time in integration-test job or add better health checks

### Deployment fails

**Issue:** Missing secrets
**Solution:** Add required secrets in repository settings

## 🎯 Best Practices

1. **Always run tests locally first** before pushing
2. **Keep workflows fast** - use caching and parallel jobs
3. **Monitor workflow runs** regularly for failures
4. **Update dependencies** in workflows when package versions change
5. **Use protected branches** - require CI to pass before merging
6. **Review security alerts** from dependency scanning

## 📈 Workflow Optimization

### Current optimizations:
- ✅ GitHub Actions cache for npm packages
- ✅ Docker layer caching
- ✅ Parallel job execution
- ✅ Conditional job execution

### Future improvements:
- 🔄 Add E2E tests with Playwright
- 🔄 Add performance testing
- 🔄 Add code coverage reporting
- 🔄 Add automatic changelog generation

## 🔐 Security

- **Secrets:** Never commit secrets to repository
- **Dependencies:** Regular vulnerability scanning
- **Secret Detection:** TruffleHog scans for exposed secrets
- **Branch Protection:** Enable on main branch

## 📞 Support

For issues with CI/CD:
1. Check workflow logs in Actions tab
2. Review this documentation
3. Check GitHub Actions documentation: https://docs.github.com/actions

---

**Last Updated:** November 2025
**Maintained by:** Development Team
