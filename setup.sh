#!/bin/bash
# setup.sh - 环境初始化脚本
# 适用于 Ubuntu/Debian 2C4G 云服务器
# 用法: bash setup.sh
set -e

echo "=== openclaw-x-video 环境初始化 ==="

# ── 1. 系统依赖 ──────────────────────────────────────────
echo "[1/6] 安装系统依赖..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
  ffmpeg \
  curl \
  git \
  python3 \
  python3-pip \
  python3-venv \
  libfontconfig1 \
  fonts-noto-cjk

# ── 2. Node.js 20 LTS ────────────────────────────────────
echo "[2/6] 安装 Node.js 20..."
if ! command -v node &>/dev/null || [[ "$(node -v)" != v20* ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi
echo "Node.js: $(node -v), npm: $(npm -v)"

# ── 3. Python 虚拟环境 ───────────────────────────────────
echo "[3/6] 创建 Python 虚拟环境..."
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

python3 -m venv .venv
source .venv/bin/activate

pip install -q --upgrade pip
pip install -q \
  playwright \
  openai \
  python-dotenv \
  edge-tts

# 安装 Playwright 浏览器（仅 Chromium，节省空间）
python -m playwright install chromium
python -m playwright install-deps chromium

echo "Python 依赖安装完成"

# ── 4. Remotion 依赖 ─────────────────────────────────────
echo "[4/6] 安装 Remotion 依赖..."
cd "$PROJECT_DIR/skills/remotion"
npm install --silent
cd "$PROJECT_DIR"
echo "Remotion 依赖安装完成"

# ── 5. Swap 空间（2C4G 渲染保障）────────────────────────
echo "[5/6] 配置 Swap 空间..."
if [ ! -f /swapfile ]; then
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  echo "Swap 4G 已创建并启用"
else
  echo "Swap 已存在，跳过"
fi
free -h

# ── 6. 初始化配置文件 ────────────────────────────────────
echo "[6/6] 初始化配置..."
if [ ! -f "$PROJECT_DIR/config/.env" ]; then
  cp "$PROJECT_DIR/config/.env.example" "$PROJECT_DIR/config/.env"
  echo ""
  echo "⚠️  请编辑 config/.env 填写以下必要配置："
  echo "   - LLM_API_KEY"
  echo "   - LLM_API_BASE（如使用非 OpenAI 接口）"
  echo "   - X_USERNAME / X_PASSWORD"
else
  echo "config/.env 已存在，跳过"
fi

# 创建运行时目录
mkdir -p data/tasks data/bg_videos output

echo ""
echo "=== 安装完成 ==="
echo ""
echo "下一步："
echo "  1. 编辑 config/.env 填写 API Key"
echo "  2. 激活虚拟环境: source .venv/bin/activate"
echo "  3. 测试抓取: python skills/scraper/x_scraper.py --limit 5 --min-likes 100"
echo "  4. 启动 OpenClaw: openclaw start --config openclaw.json"
