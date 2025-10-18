#!/bin/bash

set -e  # Exit on error

echo "🔍 Running Akave Python SDK code quality checks..."
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

run_check() {
    local name=$1
    local command=$2
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔧 Running: $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if eval "$command"; then
        echo -e "${GREEN}✅ $name passed${NC}"
    else
        echo -e "${RED}❌ $name failed${NC}"
        FAILED=$((FAILED + 1))
    fi
    echo ""
}

run_check "Black (code formatting)" \
    "black --check --diff akavesdk/ private/ sdk/ tests/"

run_check "isort (import sorting)" \
    "isort --check-only --diff akavesdk/ private/ sdk/ tests/"

run_check "flake8 (linting)" \
    "flake8 akavesdk/ private/ sdk/ tests/"

run_check "pylint (code analysis)" \
    "pylint akavesdk/ private/ sdk/ --max-line-length=120 --disable=C0111,R0903,W0212,C0103,R0913,R0914"

run_check "mypy (type checking)" \
    "mypy akavesdk/ private/ sdk/ --ignore-missing-imports --no-strict-optional"

run_check "pytest (unit tests)" \
    "pytest tests/unit -v --cov=akavesdk --cov=private --cov=sdk --cov-report=term-missing"

run_check "bandit (security scan)" \
    "bandit -r akavesdk/ private/ sdk/ -ll"

run_check "safety (dependency check)" \
    "safety check || true"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✨ All checks passed! Ready to commit.${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED check(s) failed. Please fix the issues before committing.${NC}"
    echo ""
    echo "💡 Quick fixes:"
    echo "  • Format code: black akavesdk/ private/ sdk/ tests/"
    echo "  • Sort imports: isort akavesdk/ private/ sdk/ tests/"
    echo "  • See details above for other issues"
    exit 1
fi

