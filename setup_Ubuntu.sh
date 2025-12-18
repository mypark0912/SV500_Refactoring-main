#!/bin/bash

# 설정
VENV_NAME="${1:-venv}"
JSON_FILE="${2:-pip_install.json}"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "========================================="
echo " Python 가상환경 설치 스크립트"
echo "========================================="

# JSON 파일 확인
if [ ! -f "$JSON_FILE" ]; then
    echo -e "${RED}[ERROR] $JSON_FILE 파일이 없습니다.${NC}"
    exit 1
fi

# jq 설치 확인
if ! command -v jq &> /dev/null; then
    echo "[INFO] jq 설치 중..."
    sudo apt-get update && sudo apt-get install -y jq
fi

# 가상환경 생성
echo "[1/3] 가상환경 생성: $VENV_NAME"
python3.11 -m venv "$VENV_NAME"

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] 가상환경 생성 실패${NC}"
    echo "[TIP] python3-venv 설치: sudo apt-get install python3.11-venv"
    exit 1
fi

# 가상환경 pip 경로 설정
VENV_PIP="$VENV_NAME/bin/pip"
VENV_PYTHON="$VENV_NAME/bin/python"

# pip 업그레이드
echo "[2/3] pip 업그레이드"
"$VENV_PIP" install --upgrade pip -q

# Python 버전 확인
echo "[INFO] Python 버전: $("$VENV_PYTHON" --version)"

# 패키지 설치
echo "[3/3] 패키지 설치 중..."
PACKAGES=$(jq -r '.dependencies[]' "$JSON_FILE")

for pkg in $PACKAGES; do
    echo "  - $pkg 설치 중..."
    "$VENV_PIP" install "$pkg" -q
    if [ $? -ne 0 ]; then
        echo -e "${RED}    [WARN] $pkg 설치 실패${NC}"
    fi
done

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN} 설치 완료!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "가상환경 활성화: source $VENV_NAME/bin/activate"
echo "가상환경 비활성화: deactivate"
