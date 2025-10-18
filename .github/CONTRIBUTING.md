# Contributing to Akave Python SDK

Thank you for your interest in contributing to the Akave Python SDK! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/akave-ai/akavesdk-py.git
   cd akavesdk-py
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install black isort flake8 pylint mypy  # Code quality tools
   ```

## Code Quality Standards

We use automated checks to maintain code quality. Before submitting a PR, please ensure your code passes all checks:

### Running Tests

```bash
# Run all unit tests
pytest tests/unit -v

# Run with coverage
pytest tests/unit --cov=akavesdk --cov=private --cov=sdk --cov-report=term-missing

# Run specific test markers
pytest -m unit
pytest -m integration
```

### Code Formatting

We use **Black** for code formatting (120 character line length):

```bash
# Check formatting
black --check akavesdk/ private/ sdk/ tests/

# Auto-format code
black akavesdk/ private/ sdk/ tests/
```

### Import Sorting

We use **isort** to keep imports organized:

```bash
# Check import sorting
isort --check-only akavesdk/ private/ sdk/ tests/

# Auto-fix imports
isort akavesdk/ private/ sdk/ tests/
```

### Linting

We use **flake8** for linting:

```bash
flake8 akavesdk/ private/ sdk/ tests/
```

### Type Checking

We use **mypy** for static type checking:

```bash
mypy akavesdk/ private/ sdk/
```

### Run All Quality Checks

```bash
# Run everything at once
black --check akavesdk/ private/ sdk/ tests/ && \
isort --check-only akavesdk/ private/ sdk/ tests/ && \
flake8 akavesdk/ private/ sdk/ tests/ && \
mypy akavesdk/ private/ sdk/
```

## GitHub Workflows

We have two automated workflows that run on every push and pull request:

### 1. CI Workflow (`.github/workflows/ci.yml`)

Automatically runs on all pushes and PRs:
- **Tests** on multiple Python versions (3.8-3.12)
- **Multiple operating systems** (Ubuntu, macOS, Windows)
- **Coverage reporting** to Codecov
- **Integration tests** (where applicable)

### 2. Code Quality Workflow (`.github/workflows/code-quality.yml`)

Checks code quality:
- **Black** formatting check
- **isort** import order check
- **flake8** linting
- **pylint** code analysis
- **mypy** type checking
- **Bandit** security scanning
- **Safety** dependency vulnerability check

## Pull Request Process

1. **Fork** the repository and create a new branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit them
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

3. **Run all tests and quality checks** locally before pushing
   ```bash
   pytest tests/unit -v
   black akavesdk/ private/ sdk/ tests/
   isort akavesdk/ private/ sdk/ tests/
   flake8 akavesdk/ private/ sdk/ tests/
   ```

4. **Push to your fork** and create a pull request
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Wait for CI checks** to pass - the GitHub workflows will automatically run

6. **Address any review comments** and update your PR

## Commit Message Guidelines

- Use clear, descriptive commit messages
- Start with a verb in the present tense (e.g., "Add", "Fix", "Update")
- Reference issue numbers when applicable (e.g., "Fix #123")

Examples:
- `Add support for streaming uploads`
- `Fix connection timeout handling`
- `Update documentation for SDK initialization`

## Testing Guidelines

- Write tests for all new features
- Maintain or improve code coverage
- Use appropriate test markers (`@pytest.mark.unit`, `@pytest.mark.integration`, etc.)
- Mock external dependencies in unit tests

## Questions?

If you have questions or need help, please:
- Open an issue on GitHub
- Check existing documentation
- Review the test files for examples

Thank you for contributing! 🚀
