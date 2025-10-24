# GitHub Workflows Guide

This document explains how GitHub Workflows work for the Akave Python SDK and how to use them.

## What are GitHub Workflows?

GitHub Workflows (GitHub Actions) are automated processes that run when specific events occur in your repository. They help maintain code quality, run tests automatically, and ensure your code works across different environments.

## Our Workflows

### 1. CI Workflow (`ci.yml`)

**When it runs:** Automatically on every push and pull request to `main` or `develop` branches

**What it does:**
- ✅ Runs unit tests on multiple Python versions (3.8, 3.9, 3.10, 3.11, 3.12)
- ✅ Tests on multiple operating systems (Ubuntu, macOS, Windows)
- ✅ Generates code coverage reports
- ✅ Uploads coverage to Codecov
- ✅ Runs integration tests (where applicable)

**Why it's important:** Ensures your code works across different Python versions and operating systems before merging.

**Status Badge:** Add this to your README.md to show build status:
```markdown
[![CI](https://github.com/akave-ai/akavesdk-py/actions/workflows/ci.yml/badge.svg)](https://github.com/akave-ai/akavesdk-py/actions/workflows/ci.yml)
```

### 2. Code Quality Workflow (`code-quality.yml`)

**When it runs:** Automatically on every push and pull request to `main` or `develop` branches

**What it does:**
- 🔍 **Black:** Checks Python code formatting
- 🔍 **isort:** Checks import statement ordering
- 🔍 **flake8:** Checks for Python syntax errors and style issues
- 🔍 **pylint:** Performs advanced code analysis
- 🔍 **mypy:** Checks type hints
- 🔒 **Bandit:** Scans for security vulnerabilities
- 🔒 **Safety:** Checks dependencies for known security issues
- 📦 **pip-audit:** Audits dependencies for vulnerabilities

**Why it's important:** Maintains consistent code quality and catches potential bugs or security issues early.

**Status Badge:**
```markdown
[![Code Quality](https://github.com/akave-ai/akavesdk-py/actions/workflows/code-quality.yml/badge.svg)](https://github.com/akave-ai/akavesdk-py/actions/workflows/code-quality.yml)
```

## How to Set Up GitHub Workflows (First Time)

### Step 1: Push the Workflow Files

The workflow files are already created in `.github/workflows/`. You just need to push them to GitHub:

```bash
git add .github/
git commit -m "Add GitHub workflows for CI and code quality"
git push origin main  # or develop, depending on your default branch
```

### Step 2: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click on the **"Actions"** tab
3. If prompted, click **"I understand my workflows, go ahead and enable them"**

That's it! Your workflows are now active and will run automatically.

### Step 3: (Optional) Set Up Codecov

To see coverage reports:

1. Go to [codecov.io](https://codecov.io)
2. Sign in with your GitHub account
3. Add your repository
4. Copy the Codecov token (if private repo)
5. Add it to your GitHub repository secrets:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: paste your token

## Viewing Workflow Results

### On GitHub:
1. Go to your repository
2. Click the **"Actions"** tab
3. You'll see all workflow runs with their status (✅ pass, ❌ fail, 🟡 running)
4. Click on any run to see detailed logs

### On Pull Requests:
- Workflow status appears automatically at the bottom of each PR
- Required checks must pass before merging
- Click "Details" to see what failed

## Running Checks Locally (Before Pushing)

To avoid workflow failures, run these commands locally first:

### Install code quality tools:
```bash
pip install black isort flake8 pylint mypy bandit safety pip-audit
```

### Run tests:
```bash
pytest tests/unit -v --cov=akavesdk --cov=private --cov=sdk
```

### Check formatting:
```bash
black --check akavesdk/ private/ sdk/ tests/
```

### Fix formatting automatically:
```bash
black akavesdk/ private/ sdk/ tests/
isort akavesdk/ private/ sdk/ tests/
```

### Run linters:
```bash
flake8 akavesdk/ private/ sdk/ tests/
pylint akavesdk/ private/ sdk/
```

### Security checks:
```bash
bandit -r akavesdk/ private/ sdk/
safety check
```

## Troubleshooting

### ❌ Workflow fails on push
1. Click on the failed workflow in the Actions tab
2. Expand the failed step to see error details
3. Fix the issue locally
4. Push again

### ❌ Tests pass locally but fail in CI
- **Different Python version:** CI tests on multiple versions (3.8-3.12)
- **Different OS:** CI tests on Ubuntu, macOS, Windows
- **Missing dependencies:** Check that `requirements.txt` is complete

### ❌ Code quality checks fail
```bash
# Auto-fix most issues:
black akavesdk/ private/ sdk/ tests/
isort akavesdk/ private/ sdk/ tests/

# Then re-run checks:
flake8 akavesdk/ private/ sdk/ tests/
```

## Configuration Files

We've created configuration files to customize the tools:

- **`.flake8`** - Flake8 linting rules
- **`pyproject.toml`** - Black, isort, mypy, pylint configuration
- **`pytest.ini`** - Pytest configuration (already existed)

## Workflow Triggers

Both workflows trigger on:
- `push` to `main` or `develop` branches
- `pull_request` to `main` or `develop` branches

You can modify triggers in the workflow YAML files if needed.

## Best Practices

1. ✅ **Always run tests locally** before pushing
2. ✅ **Keep workflows fast** - only run necessary tests
3. ✅ **Fix failing workflows immediately** - don't let them stay red
4. ✅ **Use branches** for new features and create PRs
5. ✅ **Review workflow results** before merging PRs

## Next Steps

Consider adding:
- **Release workflow** - Automatically publish to PyPI on new releases
- **Documentation workflow** - Build and deploy docs automatically
- **Dependency updates** - Dependabot for automatic dependency updates
- **Label management** - Auto-label PRs based on changed files

## Questions?

- Check [GitHub Actions documentation](https://docs.github.com/en/actions)
- Review the `.github/CONTRIBUTING.md` file
- Open an issue if something isn't working

Happy coding! 🚀

