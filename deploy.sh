#!/bin/bash
# 金融学院AI助手 - 服务器部署脚本
# 服务器: 47.96.157.172

set -e

SERVER="root@47.96.157.172"
REMOTE_DIR="/opt/finance-agent"

echo "=== 金融学院AI助手部署 ==="
echo "目标服务器: 47.96.157.172"

# 1. 在服务器上创建目录
echo "[1/5] 创建远程目录..."
ssh $SERVER "mkdir -p $REMOTE_DIR/uploads $REMOTE_DIR/data"

# 2. 同步文件到服务器
echo "[2/5] 同步文件到服务器..."
rsync -avz --exclude='node_modules' --exclude='.git' --exclude='__pycache__' \
  --exclude='frontend/dist' --exclude='backend/*.db' \
  ./ $SERVER:$REMOTE_DIR/

# 3. 安装后端依赖
echo "[3/5] 安装后端依赖..."
ssh $SERVER "cd $REMOTE_DIR/backend && pip install -r requirements.txt -q"

# 4. 安装前端依赖并构建
echo "[4/5] 构建前端..."
ssh $SERVER "cd $REMOTE_DIR/frontend && npm install && npm run build"

# 5. 启动服务
echo "[5/5] 启动服务..."
ssh $SERVER "cd $REMOTE_DIR && pkill -f 'uvicorn main:app' || true"
ssh $SERVER "cd $REMOTE_DIR/backend && nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/finance-backend.log 2>&1 &"

echo ""
echo "=== 部署完成 ==="
echo "后端API: http://47.96.157.172:8000/api/health"
echo "前端界面: http://47.96.157.172 (需要Nginx配置)"
echo ""
echo "查看日志: ssh $SERVER 'tail -f /tmp/finance-backend.log'"
