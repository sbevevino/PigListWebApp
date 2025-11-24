#!/bin/bash

echo "🔍 Verifying Piglist Dev Container Setup"
echo "========================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ALL_PASSED=true

# Function to check command
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        ALL_PASSED=false
        return 1
    fi
}

# Function to check Python package
check_python_package() {
    if python -c "import $1" 2>/dev/null; then
        VERSION=$(python -c "import $1; print(getattr($1, '__version__', 'unknown'))" 2>/dev/null)
        echo -e "${GREEN}✓${NC} $2 ($1) - version: $VERSION"
        return 0
    else
        echo -e "${RED}✗${NC} $2 ($1) is NOT installed"
        ALL_PASSED=false
        return 1
    fi
}

# Function to check service connectivity
check_service() {
    local service=$1
    local host=$2
    local port=$3
    
    if timeout 2 bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $service is accessible at $host:$port"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $service at $host:$port is not accessible (may not be running)"
        return 1
    fi
}

echo "1️⃣  System Tools"
echo "----------------"
check_command python
check_command pip
check_command git
check_command curl
check_command psql
check_command redis-cli
check_command gh
echo ""

echo "2️⃣  Python Version"
echo "----------------"
PYTHON_VERSION=$(python --version 2>&1)
echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
echo ""

echo "3️⃣  Core Python Dependencies"
echo "----------------------------"
check_python_package fastapi "FastAPI"
check_python_package uvicorn "Uvicorn"
check_python_package sqlalchemy "SQLAlchemy"
check_python_package asyncpg "AsyncPG"
check_python_package alembic "Alembic"
check_python_package redis "Redis"
check_python_package celery "Celery"
check_python_package pydantic "Pydantic"
echo ""

echo "4️⃣  Web Scraping Dependencies"
echo "-----------------------------"
check_python_package bs4 "BeautifulSoup4"
check_python_package httpx "HTTPX"
check_python_package playwright "Playwright"
check_python_package lxml "lxml"
echo ""

echo "5️⃣  Development Dependencies"
echo "----------------------------"
check_python_package pytest "Pytest"
check_python_package black "Black"
check_python_package flake8 "Flake8"
check_python_package isort "isort"
check_python_package mypy "Mypy"
echo ""

echo "6️⃣  Playwright Browsers"
echo "----------------------"
if playwright --version &> /dev/null; then
    PLAYWRIGHT_VERSION=$(playwright --version 2>&1)
    echo -e "${GREEN}✓${NC} Playwright CLI: $PLAYWRIGHT_VERSION"
    
    # Check if browsers are installed
    if python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); p.stop()" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Chromium browser is installed"
    else
        echo -e "${YELLOW}⚠${NC} Chromium browser may not be installed (run: playwright install chromium)"
    fi
else
    echo -e "${RED}✗${NC} Playwright CLI not available"
    ALL_PASSED=false
fi
echo ""

echo "7️⃣  Service Connectivity"
echo "-----------------------"
check_service "PostgreSQL" "db" "5432"
check_service "Redis" "redis" "6379"
echo ""

echo "8️⃣  Database Connection Test"
echo "---------------------------"
if PGPASSWORD=piglist_dev psql -h db -U piglist -d piglist -c "SELECT version();" &> /dev/null; then
    DB_VERSION=$(PGPASSWORD=piglist_dev psql -h db -U piglist -d piglist -t -c "SELECT version();" 2>/dev/null | head -n1 | xargs)
    echo -e "${GREEN}✓${NC} PostgreSQL connection successful"
    echo "  Version: $DB_VERSION"
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL connection failed (database may not be running)"
fi
echo ""

echo "9️⃣  Redis Connection Test"
echo "------------------------"
if redis-cli -h redis ping &> /dev/null; then
    REDIS_VERSION=$(redis-cli -h redis INFO server | grep redis_version | cut -d: -f2 | tr -d '\r')
    echo -e "${GREEN}✓${NC} Redis connection successful"
    echo "  Version: $REDIS_VERSION"
else
    echo -e "${YELLOW}⚠${NC} Redis connection failed (Redis may not be running)"
fi
echo ""

echo "🔟 VSCode Extensions (Expected)"
echo "-------------------------------"
echo "The following extensions should be installed:"
echo "  • ms-python.python (Python)"
echo "  • ms-python.vscode-pylance (Pylance)"
echo "  • ms-python.black-formatter (Black Formatter)"
echo "  • ms-python.flake8 (Flake8)"
echo "  • ms-python.isort (isort)"
echo "  • charliermarsh.ruff (Ruff)"
echo "  • ms-azuretools.vscode-docker (Docker)"
echo "  • mtxr.sqltools (SQLTools)"
echo "  • mtxr.sqltools-driver-pg (PostgreSQL Driver)"
echo "  • cweijan.vscode-redis-client (Redis Client)"
echo "  • tamasfe.even-better-toml (TOML)"
echo "  • redhat.vscode-yaml (YAML)"
echo "  • usernamehw.errorlens (Error Lens)"
echo "  • eamodio.gitlens (GitLens)"
echo "  • github.copilot (GitHub Copilot)"
echo ""
echo -e "${YELLOW}ℹ${NC}  Check VSCode Extensions panel to verify these are installed"
echo ""

echo "1️⃣1️⃣  Port Forwarding Configuration"
echo "----------------------------------"
echo "Expected forwarded ports:"
echo "  • 8000 - FastAPI"
echo "  • 5432 - PostgreSQL"
echo "  • 6379 - Redis"
echo "  • 5555 - Celery Flower"
echo ""
echo -e "${YELLOW}ℹ${NC}  Check VSCode Ports panel to verify these are forwarded"
echo ""

echo "1️⃣2️⃣  Project Structure"
echo "---------------------"
if [ -f "pyproject.toml" ]; then
    echo -e "${GREEN}✓${NC} pyproject.toml exists"
else
    echo -e "${RED}✗${NC} pyproject.toml missing"
    ALL_PASSED=false
fi

if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}✓${NC} requirements.txt exists"
else
    echo -e "${RED}✗${NC} requirements.txt missing"
    ALL_PASSED=false
fi

if [ -f "requirements-dev.txt" ]; then
    echo -e "${GREEN}✓${NC} requirements-dev.txt exists"
else
    echo -e "${RED}✗${NC} requirements-dev.txt missing"
    ALL_PASSED=false
fi

if [ -d "app" ]; then
    echo -e "${GREEN}✓${NC} app/ directory exists"
else
    echo -e "${RED}✗${NC} app/ directory missing"
    ALL_PASSED=false
fi

if [ -d "tests" ]; then
    echo -e "${GREEN}✓${NC} tests/ directory exists"
else
    echo -e "${RED}✗${NC} tests/ directory missing"
    ALL_PASSED=false
fi
echo ""

echo "1️⃣3️⃣  Quick Test Run"
echo "------------------"
if pytest --version &> /dev/null; then
    echo -e "${GREEN}✓${NC} Running pytest..."
    if pytest tests/ -v 2>&1 | head -20; then
        echo -e "${GREEN}✓${NC} Tests executed (check output above for results)"
    else
        echo -e "${YELLOW}⚠${NC} Test execution completed with warnings/errors"
    fi
else
    echo -e "${RED}✗${NC} pytest not available"
    ALL_PASSED=false
fi
echo ""

echo "========================================"
if [ "$ALL_PASSED" = true ]; then
    echo -e "${GREEN}✅ All critical checks passed!${NC}"
    echo ""
    echo "Your dev container is properly configured. You can now:"
    echo "  1. Start the FastAPI server: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo "  2. Run tests: pytest"
    echo "  3. Access API docs: http://localhost:8000/docs"
else
    echo -e "${RED}❌ Some checks failed${NC}"
    echo ""
    echo "Please review the errors above and:"
    echo "  1. Ensure all services are running (docker-compose up)"
    echo "  2. Rebuild the container if needed"
    echo "  3. Check the .devcontainer configuration"
fi
echo "========================================"