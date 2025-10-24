# GitHub Workflows Setup - Complete Guide

This document provides a complete overview of the GitHub Workflows setup for Akave Python SDK.

## 📁 Files Created

### Workflow Files
```
.github/
├── workflows/
│   ├── ci.yml              # Continuous Integration workflow
│   └── code-quality.yml    # Code quality checks workflow
├── CONTRIBUTING.md         # Contribution guidelines
└── WORKFLOWS.md           # Detailed workflow documentation
```

### Configuration Files
```
akavesdk-py/
├── pyproject.toml         # Configuration for Black, isort, mypy, pylint, pytest
├── .flake8               # Flake8 linting configuration
├── .gitignore            # Updated to allow pyproject.toml
├── dev-setup.sh          # Development environment setup script
└── run-checks.sh         # Script to run all quality checks locally
```

## 🎯 What Each Workflow Does

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Purpose:** Ensures code works correctly across different environments

**Features:**
- ✅ Tests on Python 3.8, 3.9, 3.10, 3.11, 3.12
- ✅ Tests on Ubuntu, macOS, and Windows
- ✅ Runs unit tests with coverage
- ✅ Runs integration tests
- ✅ Uploads coverage reports to Codecov
- ✅ Provides detailed test results

**When it runs:**
- On every push to `main` or `develop` branches
- On every pull request to `main` or `develop` branches

### 2. Code Quality Workflow (`.github/workflows/code-quality.yml`)

**Purpose:** Maintains code quality and security standards

**Features:**
- 🎨 **Black:** Checks code formatting (120 char line length)
- 📦 **isort:** Checks import statement ordering
- 🔍 **flake8:** Lints for syntax errors and style issues
- 🔬 **pylint:** Advanced code analysis
- 🔎 **mypy:** Static type checking
- 🔒 **Bandit:** Security vulnerability scanning
- 🛡️ **Safety:** Dependency vulnerability checks
- 📊 **pip-audit:** Dependency auditing

**When it runs:**
- On every push to `main` or `develop` branches
- On every pull request to `main` or `develop` branches

## 🚀 How to Activate (First Time)

### Step 1: Review the Files

All files have been created. Review them to make sure everything looks good:

```bash
# View workflow files
cat .github/workflows/ci.yml
cat .github/workflows/code-quality.yml

# View configuration files
cat pyproject.toml
cat .flake8
```

### Step 2: Commit and Push

```bash
# Add all new files
git add .github/ pyproject.toml .flake8 .gitignore dev-setup.sh run-checks.sh GITHUB_WORKFLOWS_SETUP.md

# Commit
git commit -m "Add GitHub workflows for CI and code quality checks"

# Push to GitHub
git push origin main  # or 'develop' if that's your default branch
```

### Step 3: Enable GitHub Actions

1. Go to your repository on GitHub: https://github.com/akave-ai/akavesdk-py
2. Click the **"Actions"** tab at the top
3. If you see a message about workflows, click **"I understand my workflows, go ahead and enable them"**
4. You should see your two workflows listed:
   - CI
   - Code Quality

That's it! 🎉 Your workflows are now active.

### Step 4: (Optional) Set Up Codecov for Coverage Reports

If you want coverage reports (recommended):

1. Go to [codecov.io](https://codecov.io)
2. Sign in with your GitHub account
3. Click "Add Repository" and select `akavesdk-py`
4. If your repo is private, you'll get a token:
   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: paste the token from Codecov
5. Coverage reports will now appear on PRs automatically

## 🧪 Testing Locally Before Pushing

To avoid workflow failures, always test locally first:

### Option 1: Quick Setup (Recommended)

```bash
# One-time setup
./dev-setup.sh

# Run all checks before pushing
./run-checks.sh
```

### Option 2: Manual Commands

```bash
# Install development tools
pip install black isort flake8 pylint mypy bandit safety pip-audit

# Format code (auto-fix)
black akavesdk/ private/ sdk/ tests/
isort akavesdk/ private/ sdk/ tests/

# Run tests
pytest tests/unit -v --cov=akavesdk --cov=private --cov=sdk

# Check code quality
flake8 akavesdk/ private/ sdk/ tests/
pylint akavesdk/ private/ sdk/
mypy akavesdk/ private/ sdk/

# Security checks
bandit -r akavesdk/ private/ sdk/ -ll
safety check
```

## 📊 Viewing Workflow Results

### On GitHub:

1. Go to your repository
2. Click the **"Actions"** tab
3. You'll see a list of all workflow runs:
   - ✅ Green checkmark = passed
   - ❌ Red X = failed
   - 🟡 Yellow circle = running
4. Click any run to see detailed logs

### On Pull Requests:

- Workflow checks appear automatically at the bottom of each PR
- Must pass before merging (if you configure branch protection)
- Click "Details" next to any check to see logs

### Adding Status Badges to README

Add these badges to your `README.md` to show build status:

```markdown
[![CI](https://github.com/akave-ai/akavesdk-py/actions/workflows/ci.yml/badge.svg)](https://github.com/akave-ai/akavesdk-py/actions/workflows/ci.yml)
[![Code Quality](https://github.com/akave-ai/akavesdk-py/actions/workflows/code-quality.yml/badge.svg)](https://github.com/akave-ai/akavesdk-py/actions/workflows/code-quality.yml)
[![codecov](https://codecov.io/gh/akave-ai/akavesdk-py/branch/main/graph/badge.svg)](https://codecov.io/gh/akave-ai/akavesdk-py)
```

## 🔧 Configuration Files Explained

### `pyproject.toml`
Modern Python configuration file that contains settings for:
- Black (formatter)
- isort (import sorter)
- mypy (type checker)
- pylint (linter)
- pytest (test runner)
- coverage (code coverage)

### `.flake8`
Configuration for flake8 linter:
- Max line length: 120 characters
- Excludes: generated files, virtual environments
- Custom ignore rules for compatibility with Black

### Updated `.gitignore`
Added exception to allow `pyproject.toml` to be committed (was previously blocked by `*.toml`)

## 🎓 Learning Resources

### Understanding GitHub Actions:
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Quickstart](https://docs.github.com/en/actions/quickstart)

### Python Code Quality Tools:
- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [flake8 Documentation](https://flake8.pycqa.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)

## 🐛 Troubleshooting

### Problem: Workflow doesn't run after pushing

**Solution:**
1. Check that workflow files are in `.github/workflows/`
2. Verify GitHub Actions is enabled (Settings → Actions → Allow all actions)
3. Check branch name matches (`main` or `develop`)

### Problem: All tests fail with "Module not found"

**Solution:**
1. Check that `requirements.txt` includes all dependencies
2. Verify package structure in workflow matches your project
3. May need to add `pip install -e .` to install your package

### Problem: Code quality checks fail

**Solution:**
Run locally to see specific issues:
```bash
./run-checks.sh
```
Or run individual tools to fix specific issues.

### Problem: Different results locally vs CI

**Solution:**
- **Python version:** CI tests multiple versions (3.8-3.12)
  - Test locally with different Python versions using `pyenv` or `conda`
- **Operating system:** CI tests Ubuntu, macOS, Windows
  - Consider OS-specific issues in your code
- **Dependencies:** Make sure `requirements.txt` is complete

## 📋 Maintenance

### Updating Workflows

To modify workflows:
1. Edit `.github/workflows/ci.yml` or `.github/workflows/code-quality.yml`
2. Commit and push changes
3. Workflows automatically use the new configuration

### Adding New Python Versions

In `.github/workflows/ci.yml`, update the matrix:
```yaml
python-version: ['3.8', '3.9', '3.10', '3.11', '3.12', '3.13']  # Add new version
```

### Changing Branch Triggers

In workflow files, modify the `on:` section:
```yaml
on:
  push:
    branches: [ main, develop, staging ]  # Add more branches
  pull_request:
    branches: [ main, develop ]
```

## 🎯 Next Steps

Now that workflows are set up, consider:

1. **Enable branch protection** (Settings → Branches):
   - Require status checks to pass before merging
   - Require pull request reviews
   - Prevent force pushes to main

2. **Add more workflows:**
   - Release workflow for PyPI publishing
   - Documentation builds
   - Dependency updates (Dependabot)

3. **Configure notifications:**
   - GitHub → Settings → Notifications
   - Get alerts when workflows fail

4. **Set up project board:**
   - Track issues and PRs
   - Automate with Actions

## 🤝 Contributing

See `.github/CONTRIBUTING.md` for detailed contribution guidelines.

## ❓ Questions?

If you need help:
- Read `.github/WORKFLOWS.md` for detailed workflow documentation
- Read `.github/CONTRIBUTING.md` for contribution guidelines
- Open an issue on GitHub
- Check GitHub Actions documentation

---

**Created:** October 18, 2025  
**Version:** 1.0  
**Status:** ✅ Ready to use


