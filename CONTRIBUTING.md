# Contributing to FlowEngine

First off, thank you for considering contributing to FlowEngine! It's people like you that make FlowEngine such a great tool.

## 🤝 Code of Conduct

By participating in this project, you are expected to uphold our code of conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## 🚀 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

**Bug Report Template:**
```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. macOS 13.0]
 - Python Version: [e.g. 3.11.6]
 - FlowEngine Version: [e.g. 1.3.0]

**Additional context**
Add any other context about the problem here.
```

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue with the following information:

**Enhancement Template:**
```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
A clear description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
```

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following our coding standards
3. **Add tests** if you've added code that should be tested
4. **Ensure the test suite passes** (`pytest tests/ -v`)
5. **Format your code** with `black` and `flake8`
6. **Write a descriptive commit message**
7. **Push to your fork** and submit a pull request

## 💻 Development Setup

### Prerequisites
- Python 3.11 or higher
- Git
- PostgreSQL (or SQLite for local development)

### Setting Up Your Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/1-Blocks.git
cd 1-Blocks

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd flowengine-app
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8 mypy

# Set up environment variables
export DATABASE_URL="sqlite:///./readiness.db"
export READINESS_API_KEY="test-key-123"

# Initialize database
python seed_readiness.py

# Run tests to verify setup
pytest tests/ -v
```

## 📝 Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:
- Line length: 120 characters (vs PEP 8's 79)
- Use `black` for automatic formatting
- Use type hints where applicable

### Code Formatting

```bash
# Format code with black
black flowengine-app/

# Check linting with flake8
flake8 flowengine-app/ --max-line-length=120

# Type checking with mypy (optional but recommended)
mypy flowengine-app/
```

### Writing Tests

- Place tests in `flowengine-app/tests/`
- Name test files as `test_*.py`
- Use descriptive test function names: `test_idea_creation_requires_api_key()`
- Use pytest fixtures for setup/teardown
- Aim for >80% code coverage

**Example Test:**
```python
def test_readiness_flow_and_wave_assignment(client):
    # Create readiness record
    readiness_payload = {
        "repo_name": "test-repo",
        "owner": "test-team",
        "training_completed": True,
        "cli_installed": True,
        "test_coverage_80": True,
        "runbook_acknowledged": True,
    }

    resp = client.post("/api/readiness", json=readiness_payload, headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json()["readiness_status"] == "ready"

    # Test wave assignment
    wave_payload = {
        "repo_name": "test-repo",
        "wave": "wave_1",
        "priority": 1
    }

    resp = client.post("/api/waves/assign", json=wave_payload, headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json()["wave"] == "wave_1"
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semi-colons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes that don't modify src or test files

**Examples:**
```bash
feat(api): Add wave export endpoint
fix(gates): Handle missing LLM API keys gracefully
docs: Update README with deployment instructions
test(api): Add tests for readiness flow
```

## 🔍 Code Review Process

1. **Automated Checks**: All PRs must pass automated checks:
   - Tests must pass (`pytest`)
   - Code must be formatted (`black`)
   - Linting must pass (`flake8`)

2. **Manual Review**: A maintainer will review your PR for:
   - Code quality and clarity
   - Test coverage
   - Documentation updates
   - Breaking changes

3. **Feedback**: Address review comments promptly
4. **Approval**: Once approved, a maintainer will merge your PR

## 📦 Project Structure

```
1-Blocks/
├── flowengine-app/          # Main application
│   ├── app.py              # FlowEngine core
│   ├── repo_readiness_api.py  # Readiness API
│   ├── gates.py            # Quality gates
│   ├── gates_llm.py        # LLM integration
│   ├── llm_orchestrator.py # Multi-LLM orchestration
│   ├── models.py           # Database models
│   ├── schemas.py          # Pydantic schemas
│   ├── database.py         # Database connection
│   ├── domain_types.py     # Enums and types
│   ├── seed_readiness.py   # Database seeding
│   ├── requirements.txt    # Python dependencies
│   └── tests/              # Test suite
│       ├── test_repo_readiness_api.py
│       └── test_llm_orchestrator.py
├── team_site/              # Frontend UI
│   ├── ops.html           # Ops Console
│   ├── index.html         # Request Hub
│   └── assets/            # CSS/JS assets
├── evidence/              # Validation evidence
├── planning/              # Planning documents
├── README.md              # Main documentation
├── CONTRIBUTING.md        # This file
├── LICENSE                # MIT License
└── .gitignore            # Git ignore rules
```

## 🏗️ Architecture Guidelines

### Adding a New Quality Gate

1. Create a new class in `gates.py` inheriting from `QualityGate`
2. Implement the `run()` method
3. Add tests in `tests/test_gates.py`
4. Update documentation

**Example:**
```python
class MyCustomGate(QualityGate):
    def __init__(self, threshold: float = 0.8):
        super().__init__("My Custom Gate", threshold)

    def run(self, code: str, context: Dict[str, Any]) -> Tuple[bool, float, str, float, float]:
        start = time.time()

        # Your gate logic here
        score = self._calculate_score(code, context)

        duration = time.time() - start
        passed = score >= self.threshold
        details = f"Custom check: {score:.0%}"
        cost = 0.0  # No API cost

        return passed, score, details, duration, cost
```

### Adding a New LLM Provider

1. Add provider integration to `llm_orchestrator.py`
2. Add API key to environment variables
3. Implement fallback logic
4. Add tests with mocked API calls
5. Update documentation

### Database Schema Changes

1. Update models in `models.py`
2. Update schemas in `schemas.py`
3. Create migration (if using Alembic)
4. Update seed data in `seed_readiness.py`
5. Update tests

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_repo_readiness_api.py -v

# Run with coverage
pytest tests/ --cov=flowengine-app --cov-report=html

# Run with debugging
pytest tests/ -vv -s
```

### Writing New Tests

- **Unit Tests**: Test individual functions/methods
- **Integration Tests**: Test API endpoints and database interactions
- **End-to-End Tests**: Test complete workflows

**Test Fixtures:**
```python
@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Create test client with in-memory database"""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    # ... setup code
    yield test_client
    # ... teardown code
```

## 📚 Documentation

### Documentation Updates Required For:

- New features or APIs
- Changed behavior
- New environment variables
- New dependencies
- Breaking changes

### Where to Update Documentation:

- `README.md` - Main documentation
- Docstrings - In-code documentation
- `EXECUTIVE_SUMMARY.md` - Business documentation
- `GETTING_STARTED.md` - Setup instructions
- API docs (auto-generated from FastAPI)

## 🎯 Areas Looking for Contributors

We especially welcome contributions in these areas:

### High Priority
- [ ] Redis caching for LLM reviews
- [ ] GitHub Actions CI/CD integration
- [ ] Real-time WebSocket updates
- [ ] Advanced analytics dashboard
- [ ] Multi-tenant support

### Medium Priority
- [ ] Slack/Teams notification integration
- [ ] Custom gate plugins system
- [ ] ML-based threshold optimization
- [ ] GraphQL API alternative
- [ ] Docker Compose setup

### Documentation
- [ ] Video tutorials
- [ ] More code examples
- [ ] Architecture decision records (ADRs)
- [ ] API usage guides
- [ ] Deployment best practices

## 🤔 Questions?

- **General Questions**: Open a [Discussion](https://github.com/m85qurashi/1-Blocks/discussions)
- **Bug Reports**: Create an [Issue](https://github.com/m85qurashi/1-Blocks/issues)
- **Security Issues**: Email [your-security-email]

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to FlowEngine! 🎉
