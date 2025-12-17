#!/bin/bash
set -e

echo "🔨 Building LiteLLM Puter Debian Package"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Are you in the project root?"
    exit 1
fi

# Check for Poetry
if ! command -v poetry &> /dev/null; then
    echo "❌ Error: Poetry is not installed"
    echo "   Install with: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check for build dependencies
echo "📦 Checking build dependencies..."
MISSING_DEPS=()

for dep in debhelper dh-python python3-all python3-setuptools build-essential; do
    if ! dpkg -l | grep -q "^ii  $dep "; then
        MISSING_DEPS+=($dep)
    fi
done

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo "⚠️  Missing dependencies: ${MISSING_DEPS[@]}"
    echo "   Install with: sudo apt install ${MISSING_DEPS[@]}"
    exit 1
fi

echo "✅ All dependencies found"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.egg-info debian/litellm-puter
poetry run python -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', '.pytest_cache']]" 2>/dev/null || true

# Build Python wheel
echo "🎡 Building Python wheel with Poetry..."
export PATH="$HOME/.local/bin:$PATH"
poetry build -f wheel

if [ $? -ne 0 ]; then
    echo "❌ Poetry build failed"
    exit 1
fi

echo "✅ Wheel built successfully"

# Build Debian package
echo "📦 Building Debian package..."
dpkg-buildpackage -us -uc -b

if [ $? -ne 0 ]; then
    echo "❌ Debian package build failed"
    exit 1
fi

# Move package to current directory
echo "📥 Moving package to current directory..."
mv ../litellm-puter_*.deb . 2>/dev/null || true
mv ../litellm-puter_*.buildinfo . 2>/dev/null || true
mv ../litellm-puter_*.changes . 2>/dev/null || true

# List built packages
echo ""
echo "✅ Build complete!"
echo "=================="
ls -lh litellm-puter_*.deb

echo ""
echo "📦 Package info:"
dpkg-deb -I litellm-puter_*.deb | head -20

echo ""
echo "🚀 To install:"
echo "   sudo dpkg -i litellm-puter_*.deb"
echo "   sudo apt-get install -f"
echo ""
echo "📚 See docs/setup/DEBIAN_PACKAGE.md for more information"
