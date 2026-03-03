#!/bin/bash

##############################################################################
# YouTube Clipper - Claude Code Skill 安裝腳本
#
# 功能：
# 1. 自動創建 Skill 目錄
# 2. 複製所有必要文件
# 3. 安裝 Python 依賴
# 4. 檢測系統依賴（yt-dlp、FFmpeg）
#
# 使用方法：
#   bash install_as_skill.sh
##############################################################################

set -e  # 遇到錯誤立即退出

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函數
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

# 檢查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 主函數
main() {
    print_header "YouTube Clipper - Claude Code Skill 安裝"

    # 1. 確定 Skill 目錄
    SKILL_DIR="$HOME/.agents/skills/youtube-clipper"
    print_info "目標目錄: $SKILL_DIR"

    # 2. 檢查是否已存在
    if [ -d "$SKILL_DIR" ]; then
        print_warning "Skill 目錄已存在: $SKILL_DIR"
        read -p "是否覆蓋安裝？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "安裝已取消"
            exit 0
        fi
        print_info "正在更新..."
        # rm -rf "$SKILL_DIR"
    fi

    # 3. 創建目錄
    print_info "創建 Skill 目錄..."
    mkdir -p "$SKILL_DIR"
    print_success "目錄已創建"

    # 4. 複製文件
    print_info "複製項目文件..."

    # 獲取當前腳本所在目錄（即項目根目錄）
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # 複製所有必要文件
    if command_exists rsync; then
        rsync -av --exclude 'venv' \
                  --exclude '.git' \
                  --exclude '__pycache__' \
                  --exclude '.DS_Store' \
                  --exclude '.env' \
                  --exclude 'youtube-clips' \
                  "$SCRIPT_DIR/" "$SKILL_DIR/"
    else
        # Fallback to cp if rsync is not available (less clean)
        cp -R "$SCRIPT_DIR"/* "$SKILL_DIR/"
        
        # Manually cleanup if using cp
        if [ -d "$SKILL_DIR/.git" ]; then rm -rf "$SKILL_DIR/.git"; fi
        if [ -d "$SKILL_DIR/venv" ]; then rm -rf "$SKILL_DIR/venv"; fi
        if [ -d "$SKILL_DIR/__pycache__" ]; then rm -rf "$SKILL_DIR/__pycache__"; fi
        if [ -d "$SKILL_DIR/youtube-clips" ]; then rm -rf "$SKILL_DIR/youtube-clips"; fi
        if [ -f "$SKILL_DIR/.env" ]; then rm "$SKILL_DIR/.env"; fi
    fi

    print_success "文件複製完成"

    # 5. 檢查 Python
    print_info "檢查 Python 環境..."
    if ! command_exists python3; then
        print_error "未找到 Python 3，請先安裝 Python 3.8+"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version)
    print_success "Python 已安裝: $PYTHON_VERSION"

    # 6. 檢查 pip
    if ! command_exists pip3 && ! command_exists pip; then
        print_error "未找到 pip，請先安裝 pip"
        exit 1
    fi
    print_success "pip 已安裝"

    # 7. 創建虛擬環境並安裝依賴
    print_info "創建 Python 虛擬環境..."
    cd "$SKILL_DIR"

    # 清除舊的 venv
    if [ -d "venv" ]; then
        rm -rf venv
    fi

    # 創建 venv
    python3 -m venv venv

    print_info "激活虛擬環境並安裝依賴..."
    # 使用 venv 中的 pip 安裝
    ./venv/bin/pip install -q --no-cache-dir --upgrade pip
    ./venv/bin/pip install -q --no-cache-dir yt-dlp pysrt python-dotenv

    print_success "Python 依賴安裝完成（已安裝至 venv）"

    # 8. 檢查 yt-dlp
    print_info "檢查 yt-dlp..."
    if [ -f "./venv/bin/yt-dlp" ]; then
        YT_DLP_VERSION=$(./venv/bin/yt-dlp --version)
        print_success "yt-dlp 已安裝 (venv): $YT_DLP_VERSION"
    elif command_exists yt-dlp; then
        YT_DLP_VERSION=$(yt-dlp --version)
        print_success "yt-dlp 已安裝 (系統): $YT_DLP_VERSION"
    else
        print_warning "yt-dlp 命令行工具未在 PATH 中找到 (但已安裝在 venv 中)"
    fi

    # 9. 檢查 FFmpeg（關鍵：需要 libass 支持）
    print_header "檢查 FFmpeg（字幕燒錄需要）"

    FFMPEG_FOUND=false
    LIBASS_SUPPORTED=false

    # 檢查 ffmpeg-full（macOS 推薦）
    if [ -f "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg" ]; then
        print_success "ffmpeg-full 已安裝（Apple Silicon）"
        FFMPEG_FOUND=true
        LIBASS_SUPPORTED=true
    elif [ -f "/usr/local/opt/ffmpeg-full/bin/ffmpeg" ]; then
        print_success "ffmpeg-full 已安裝（Intel Mac）"
        FFMPEG_FOUND=true
        LIBASS_SUPPORTED=true
    elif command_exists ffmpeg; then
        FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
        print_success "FFmpeg 已安裝: $FFMPEG_VERSION"
        FFMPEG_FOUND=true

        # 檢查 libass 支持
        if ffmpeg -filters 2>&1 | grep -q "subtitles"; then
            print_success "FFmpeg 支持 libass（字幕燒錄可用）"
            LIBASS_SUPPORTED=true
        else
            print_warning "FFmpeg 不支持 libass（字幕燒錄不可用）"
        fi
    fi

    if [ "$FFMPEG_FOUND" = false ]; then
        print_error "FFmpeg 未安裝"
        print_info "安裝方法:"
        print_info "  macOS:  brew install ffmpeg-full  # 推薦，包含 libass"
        print_info "  Ubuntu: sudo apt-get install ffmpeg libass-dev"
    elif [ "$LIBASS_SUPPORTED" = false ]; then
        print_warning "FFmpeg 缺少 libass 支持，字幕燒錄功能將不可用"
        print_info "解決方法（macOS）:"
        print_info "  brew uninstall ffmpeg"
        print_info "  brew install ffmpeg-full"
    fi

    # 10. 創建 .env 文件
    print_header "配置環境變量"

    if [ -f "$SKILL_DIR/.env.example" ]; then
        print_info "創建 .env 文件..."
        cp "$SKILL_DIR/.env.example" "$SKILL_DIR/.env"
        print_success ".env 文件已創建"
        echo ""
        print_info "配置文件位置: $SKILL_DIR/.env"
        print_info "如需自定義配置，可編輯："
        print_info "  nano $SKILL_DIR/.env"
        print_info "  或"
        print_info "  code $SKILL_DIR/.env"
    else
        print_warning "未找到 .env.example 文件"
    fi

    # 11. 完成
    print_header "安裝完成！"

    print_success "YouTube Clipper 已成功安裝為 Claude Code Skill"
    echo ""
    print_info "安裝位置: $SKILL_DIR"
    echo ""

    # 檢查依賴狀態
    if [ "$FFMPEG_FOUND" = false ] || [ "$LIBASS_SUPPORTED" = false ]; then
        print_warning "系統依賴不完整，部分功能可能不可用"
        echo ""
    fi

    print_info "使用方法："
    print_info "  在 Claude Code 中輸入："
    print_info "  \"剪輯這個 YouTube 影片：https://youtube.com/watch?v=VIDEO_ID\""
    echo ""
    print_info "詳細文檔："
    print_info "  - Skill 使用指南: $SKILL_DIR/SKILL.md"
    print_info "  - 項目文檔: $SKILL_DIR/README.md"
    print_info "  - 技術説明: $SKILL_DIR/TECHNICAL_NOTES.md"
    echo ""
    print_success "祝使用愉快！ 🎉"
    echo ""
}

# 錯誤處理
trap 'print_error "安裝過程中發生錯誤"; exit 1' ERR

# 運行主函數
main
