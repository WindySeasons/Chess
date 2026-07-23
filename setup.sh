#!/bin/bash
# ==========================================
# 下载皮卡鱼（Pikafish）引擎二进制文件
# 用法: bash setup.sh
# ==========================================

set -e

# 皮卡鱼最新版本（可通过 https://github.com/official-pikafish/Pikafish/releases 查看）
VERSION="2024-12-28"

echo ">>> 检测系统平台..."
OS=$(uname -s)
ARCH=$(uname -m)

if [[ "$OS" == "Linux" ]]; then
    PLATFORM="linux"
    BINARY_NAME="pikafish"
    ARCHIVE_SUFFIX=".tar.gz"
elif [[ "$OS" == "MINGW"* ]] || [[ "$OS" == "MSYS"* ]] || [[ "$OS" == "CYGWIN"* ]]; then
    PLATFORM="windows"
    BINARY_NAME="pikafish.exe"
    ARCHIVE_SUFFIX=".zip"
else
    echo "不支持的系统: $OS"
    echo "请手动从 https://github.com/official-pikafish/Pikafish/releases 下载"
    exit 1
fi

ARCHIVE_NAME="pikafish-${VERSION}-${PLATFORM}-x86_64"
RELEASE_URL="https://github.com/official-pikafish/Pikafish/releases/download/${VERSION}/${ARCHIVE_NAME}${ARCHIVE_SUFFIX}"

echo ">>> 下载皮卡鱼 ${VERSION} for ${PLATFORM}..."
echo "    URL: ${RELEASE_URL}"

if command -v wget &> /dev/null; then
    wget -q --show-progress "$RELEASE_URL" -O "$ARCHIVE_NAME$ARCHIVE_SUFFIX"
elif command -v curl &> /dev/null; then
    curl -L -o "$ARCHIVE_NAME$ARCHIVE_SUFFIX" "$RELEASE_URL"
else
    echo "错误: 需要 wget 或 curl"
    exit 1
fi

echo ">>> 解压..."
if [[ "$PLATFORM" == "linux" ]]; then
    tar -xzf "$ARCHIVE_NAME$ARCHIVE_SUFFIX"
    # 皮卡鱼二进制文件可能在不同子目录
    FOUND=$(find . -name "pikafish" -type f | head -1)
    if [ -n "$FOUND" ]; then
        cp "$FOUND" ./pikafish
    fi
    chmod +x pikafish
else
    # Windows: 用 PowerShell 解压
    powershell -Command "Expand-Archive -Path '$ARCHIVE_NAME$ARCHIVE_SUFFIX' -DestinationPath '.' -Force"
    FOUND=$(find . -name "pikafish.exe" -type f | head -1)
    if [ -n "$FOUND" ]; then
        cp "$FOUND" ./pikafish.exe
    fi
fi

# 清理
rm -rf "$ARCHIVE_NAME$ARCHIVE_SUFFIX" pikafish-*/

echo ">>> 验证..."
if [ -f "$BINARY_NAME" ]; then
    echo "✓ 皮卡鱼引擎就绪: ./$BINARY_NAME"
    if [[ "$PLATFORM" == "linux" ]]; then
        ./pikafish --version 2>/dev/null || true
    fi
else
    echo "✗ 下载失败，请手动处理"
    exit 1
fi
