# Piglist - Family Gift Sharing Application

A modern web application for coordinating family gift-giving while maintaining the surprise element. Built with FastAPI, PostgreSQL, Redis, and featuring real-time presence indicators.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Local Development](#local-development-without-containers)
- [Project Structure](#project-structure)
- [Development Commands](#development-commands)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [API Documentation](#api-documentation)
- [License](#license)

## Features

- 🎁 **Gift Management**: Add gifts via URL scraping or manual entry
- 👥 **Group Coordination**: Create family groups with invite codes
- 📊 **Category Budgets**: Set spending limits per category
- 👀 **Real-time Presence**: See when someone is viewing a gift
- 🔒 **Lock Dates**: Prevent changes after a specified date
- 🔐 **Secure Authentication**: JWT-based auth with bcrypt password hashing

## Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery
- **Web Scraping**: BeautifulSoup4, Playwright
- **Real-time**: Socket.IO

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [VS Code](https://code.visualstudio.com/)
- [Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- Git

### Setup with Dev Containers (Recommended)

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/piglist.git
   cd piglist
   ```

2. **Open in VS Code**:

   ```bash
   code .
   ```

3. **Reopen in Container**:

   - VS Code will detect the `.devcontainer` folder
   - Click "Reopen in Container" when prompted
   - Or press `F1` → "Dev Containers: Reopen in Container"

4. **Wait for setup** (first time takes 5-10 minutes):

   - Docker builds the images
   - Dependencies are installed
   - Database and Redis start automatically
   - Setup script runs automatically

5. **Verify installation**:

   ```bash
   # Check Python version
   python --version

   # Check database connection
   psql -h db -U piglist -d piglist_dev
   # Type \q to exit

   # Check Redis connection
   redis-cli -h redis ping
   # Should return: PONG
   ```

6. **Start the application**:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Or use the VS Code debugger (F5)

7. **Access the application**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Celery Flower: http://localhost:5555

---

## Local Development (Without Containers)

### Prerequisites

- Python 3.11+
- PostgreSQL 15
- Redis 7
- Git

### Installation Steps

#### 1. Install System Dependencies

**macOS**:

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 postgresql@15 redis
```

**Ubuntu/Debian**:

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql-15 redis-server
```

**Windows**:

- Install Python 3.11 from [python.org](https://www.python.org/downloads/)
- Install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
- Install Redis from [redis.io](https://redis.io/download) or use WSL

#### 2. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/piglist.git
cd piglist

# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Update DATABASE_URL, REDIS_URL, SECRET_KEY
```

#### 4. Initialize Database

```bash
# Create database
createdb piglist_dev

# Run migrations (once Alembic is set up)
alembic upgrade head
```

#### 5. Start Services

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start FastAPI
uvicorn app.main:app --reload

# Terminal 3: Start Celery (optional)
celery -A app.celery worker --loglevel=info
```

---

## Project Structure

```
piglist/
├── .devcontainer/          # Dev container configuration
│   ├── devcontainer.json   # VS Code dev container config
│   ├── docker-compose.yml  # Multi-service orchestration
│   ├── Dockerfile          # Custom Python environment
│   └── postCreateCommand.sh # Setup script
├── .vscode/                # VS Code settings
│   ├── launch.json         # Debug configurations
│   ├── settings.json       # Workspace settings
│   └── extensions.json     # Recommended extensions
├── app/                    # Application code
│   ├── api/               # API routes
│   ├── core/              # Core configuration
│   │   ├── config.py      # Settings management
│   │   └── security.py    # Auth utilities
│   ├── db/                # Database configuration
│   │   └── base.py        # SQLAlchemy setup
│   ├── models/            # SQLAlchemy models
│   ├── services/          # Business logic
│   └── main.py            # FastAPI application
├── tests/                 # Test suite
│   ├── __init__.py
│   └── test_main.py       # Basic tests
├── alembic/              # Database migrations (to be initialized)
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── requirements.txt      # Python dependencies
├── requirements-dev.txt  # Development dependencies
├── pyproject.toml        # Python project config
├── PiglistArchitecture.md # Architecture documentation
└── README.md             # This file
```

---

## Development Commands

### Running the Application

```bash
# Development server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use VS Code debugger (F5)
```

### Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Run with verbose output
pytest -v

# Run with VS Code Test Explorer (Testing sidebar)
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy app/

# Run all quality checks
black . && isort . && flake8 . && mypy app/
```

### Celery Tasks

```bash
# Start Celery worker
celery -A app.celery worker --loglevel=info

# Monitor with Flower
celery -A app.celery flower --port=5555
# Visit http://localhost:5555
```

### Database Access

```bash
# Connect to PostgreSQL
psql -h db -U piglist -d piglist_dev  # In container
psql -h localhost -U piglist -d piglist_dev  # Local

# Or use VS Code SQLTools extension
# Ctrl+Shift+P → "SQLTools: Connect"
```

---

## Contributing

We welcome contributions! Here's how to get started:

### Development Workflow

#### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming conventions**:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

#### 2. Make Changes

- Write clear, concise code
- Follow the project's coding standards
- Add tests for new functionality
- Update documentation as needed

#### 3. Code Quality Checks

Before committing, ensure your code passes all checks:

```bash
# Format code
black .
isort .

# Lint
flake8 .

# Type check
mypy app/

# Run tests
pytest
```

#### 4. Commit Changes

Write clear commit messages following conventional commits:

```bash
git commit -m "feat: add gift scraping service"
git commit -m "fix: resolve authentication bug"
git commit -m "docs: update API documentation"
```

**Commit message format**:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code restructuring
- `test:` - Tests
- `chore:` - Maintenance

#### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:

- Clear description of changes
- Link to related issues
- Screenshots (if UI changes)
- Test results

### Coding Standards

#### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (Black default)
- Use docstrings for functions and classes

**Example**:

```python
def create_gift(
    title: str,
    price: float,
    category_id: int
) -> Gift:
    """
    Create a new gift item.

    Args:
        title: Gift title
        price: Gift price
        category_id: Category identifier

    Returns:
        Created gift object

    Raises:
        ValueError: If price is negative
    """
    if price < 0:
        raise ValueError("Price cannot be negative")

    return Gift(title=title, price=price, category_id=category_id)
```

#### FastAPI Routes

- Use clear, RESTful endpoint names
- Include response models
- Add proper status codes
- Document with docstrings

**Example**:

```python
@router.post("/gifts", response_model=GiftResponse, status_code=201)
async def create_gift(
    gift: GiftCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new gift item.

    Requires authentication.
    """
    return await gift_service.create(db, gift, current_user.id)
```

#### Testing Guidelines

- Write tests for new features
- Maintain test coverage above 80%
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

**Example**:

```python
def test_create_gift_success():
    """Test successful gift creation"""
    # Arrange
    gift_data = {"title": "Test Gift", "price": 29.99}

    # Act
    response = client.post("/api/gifts", json=gift_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["title"] == "Test Gift"
```

### Pull Request Checklist

Before submitting:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Commit messages are clear

### Database Migrations

When making database changes:

1. Create migration:

   ```bash
   alembic revision --autogenerate -m "Description"
   ```

2. Review generated migration
3. Test migration:

   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

4. Include migration in PR

---

## Troubleshooting

### Dev Container Issues

**Container won't start**:

```bash
# Check Docker is running
docker ps

# View logs
docker-compose -f .devcontainer/docker-compose.yml logs

# Rebuild container
# In VS Code: F1 → "Dev Containers: Rebuild Container"
```

**Port already in use**:

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in docker-compose.yml
```

**Database connection failed**:

```bash
# Check PostgreSQL is running
docker-compose -f .devcontainer/docker-compose.yml ps

# Check database logs
docker-compose -f .devcontainer/docker-compose.yml logs db

# Restart database
docker-compose -f .devcontainer/docker-compose.yml restart db
```

**Slow performance on Windows**:

- Ensure WSL 2 is enabled (not WSL 1)
- Store project files in WSL filesystem, not Windows filesystem
- Increase Docker Desktop memory allocation (Settings → Resources)

### Local Setup Issues

**Python version mismatch**:

```bash
# Check Python version
python --version

# Use specific version
python3.11 -m venv .venv
```

**PostgreSQL connection error**:

```bash
# Check PostgreSQL is running
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Start if needed
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux
```

**Redis connection error**:

```bash
# Check Redis is running
redis-cli ping

# Start if needed
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

**Import errors**:

```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Environment Variables

See `.env.example` for all available configuration options.

**Key variables**:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key (change in production!)
- `ENVIRONMENT`: development/staging/production
- `DEBUG`: Enable debug mode
- `ALLOWED_ORIGINS`: CORS allowed origins

---

## API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## Architecture

For detailed architecture information, see [PiglistArchitecture.md](PiglistArchitecture.md).

Key architectural decisions:

- **FastAPI** for modern async Python web framework
- **PostgreSQL** for robust relational data storage
- **Redis** for caching and real-time features
- **Celery** for background task processing
- **Socket.IO** for real-time presence indicators
- **Dev Containers** for consistent development environment

---

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues and questions:

- Open an issue on GitHub
- Check existing documentation
- Review [PiglistArchitecture.md](PiglistArchitecture.md)

---

Built with ❤️ for family gift coordination
