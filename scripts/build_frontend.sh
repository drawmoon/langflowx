#!/usr/bin/env bash

set -e

echo "==== Step 1: Detect langflow version ===="

# 优先从已安装包获取
if command -v python >/dev/null 2>&1; then
    VERSION=$(python - <<EOF
try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version  # 兼容 Python <3.8

try:
    print(version("langflow"))
except Exception:
    print("")
EOF
)
fi

# 如果没装，从 pyproject.toml 读取
if [ -z "$VERSION" ] && [ -f "pyproject.toml" ]; then
    VERSION=$(grep -Po '(?<=langflow[ ="]+)[0-9]+\.[0-9]+\.[0-9]+' pyproject.toml | head -n1)
fi

if [ -z "$VERSION" ]; then
    echo "❌ Failed to detect langflow version"
    exit 1
fi

TAG="v${VERSION}"
echo "✔ Detected version: $VERSION (tag=$TAG)"

echo "==== Step 2: Prepare workspace ===="

WORKDIR=".tmp_langflow_build"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"

echo "==== Step 3: Clone langflow repo ===="

git clone --depth 1 --branch "$TAG" https://github.com/langflow-ai/langflow.git "$WORKDIR"

FRONTEND_DIR="$WORKDIR/src/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

echo "==== Step 4: Check Node.js ===="

install_nvm() {
    echo "Installing nvm..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash

    export NVM_DIR="$HOME/.nvm"
    source "$NVM_DIR/nvm.sh"
}

if ! command -v node >/dev/null 2>&1; then
    echo "Node.js not found, installing via nvm..."

    if [ ! -d "$HOME/.nvm" ]; then
        install_nvm
    else
        export NVM_DIR="$HOME/.nvm"
        source "$NVM_DIR/nvm.sh"
    fi

    nvm install --lts
    nvm use --lts
else
    echo "✔ Node.js found: $(node -v)"
fi

echo "==== Step 5: Build frontend ===="

cd "$FRONTEND_DIR"

# 有些项目需要 pnpm，可自动检测
if [ -f "pnpm-lock.yaml" ]; then
    if ! command -v pnpm >/dev/null 2>&1; then
        echo "Installing pnpm..."
        npm install -g pnpm
    fi

    pnpm install
    pnpm build
else
    npm install
    npm run build
fi

echo "==== Step 6: Move dist to www ===="

cd -

DIST_DIR="$FRONTEND_DIR/dist"
TARGET_DIR="www"

if [ ! -d "$DIST_DIR" ]; then
    echo "❌ dist directory not found"
    exit 1
fi

rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"

cp -r "$DIST_DIR/"* "$TARGET_DIR/"

echo "✔ Build complete → $TARGET_DIR"

echo "==== Step 7: Cleanup ===="
rm -rf "$WORKDIR"

echo "🎉 Done!"