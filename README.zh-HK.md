# YouTube Clipper Skill

> Claude Code 的 AI 智能影片剪輯工具。下載影片、生成語義章節、剪輯片段、翻譯雙語字幕並燒錄字幕到影片。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[English](README.md) | 繁體中文

[功能特性](#功能特性) • [安裝](#安裝) • [使用方法](#使用方法) • [系統要求](#系統要求) • [配置](#配置) • [常見問題](#常見問題)

---

## 功能特性

- **AI 語義分析** - 通過理解影片內容生成精細章節（每個 2-5 分鐘），而非機械按時間切分
- **精確剪輯** - 使用 FFmpeg 以幀精度提取影片片段
- **雙語字幕** - 批量翻譯字幕為中英雙語，減少 95% 的 API 調用
- **字幕燒錄** - 將雙語字幕硬編碼到影片中，支持自定義樣式
- **內容總結** - 自動生成適合社交媒體的文案（小紅書、抖音、微信公眾號）

---

## 安裝

### 方式 1: npx skills（推薦）

```bash
npx skills add https://github.com/op7418/Youtube-clipper-skill
```

該命令會自動將 skill 安裝到 `~/.claude/skills/youtube-clipper/` 目錄。

### 方式 2: 手動安裝

```bash
git clone https://github.com/op7418/Youtube-clipper-skill.git
cd Youtube-clipper-skill
bash install_as_skill.sh
```

安裝腳本會：

- 複製文件到 `~/.claude/skills/youtube-clipper/`
- 安裝 Python 依賴（yt-dlp、pysrt、python-dotenv）
- 檢查系統依賴（Python、yt-dlp、FFmpeg）
- 創建 `.env` 配置文件

---

## 系統要求

### 系統依賴

| 依賴項                 | 版本   | 用途               | 安裝方法                                                                                          |
| ---------------------- | ------ | ------------------ | ------------------------------------------------------------------------------------------------- |
| **Python**             | 3.8+   | 腳本執行           | [python.org](https://www.python.org/downloads/)                                                   |
| **yt-dlp**             | 最新版 | YouTube 影片下載   | `brew install yt-dlp` (macOS)<br>`sudo apt install yt-dlp` (Ubuntu)<br>`pip install yt-dlp` (pip) |
| **FFmpeg with libass** | 最新版 | 影片處理和字幕燒錄 | `brew install ffmpeg-full` (macOS)<br>`sudo apt install ffmpeg libass-dev` (Ubuntu)               |

### Python 包

安裝腳本會自動安裝以下包：

- `yt-dlp` - YouTube 下載器
- `pysrt` - SRT 字幕解析器
- `python-dotenv` - 環境變量管理

### 重要：FFmpeg libass 支持

**macOS 用户注意**：Homebrew 的標準 `ffmpeg` 包不包含 libass 支持（字幕燒錄必需）。你必須安裝 `ffmpeg-full`：

```bash
# 卸載標準 ffmpeg（如果已安裝）
brew uninstall ffmpeg

# 安裝 ffmpeg-full（包含 libass）
brew install ffmpeg-full
```

**驗證 libass 支持**：

```bash
ffmpeg -filters 2>&1 | grep subtitles
# 應該輸出：subtitles    V->V  (...)
```

---

## 使用方法

### 在 Claude Code 中使用

只需告訴 Claude 剪輯一個 YouTube 影片：

```
Clip this YouTube video: https://youtube.com/watch?v=VIDEO_ID
```

或者

```
剪輯這個 YouTube 影片：https://youtube.com/watch?v=VIDEO_ID
```

### 工作流程

1. **環境檢測** - 驗證 yt-dlp、FFmpeg 和 Python 依賴
2. **影片下載** - 下載影片（最高 1080p）和英文字幕
3. **AI 章節分析** - Claude 分析字幕生成語義章節（每個 2-5 分鐘）
4. **用户選擇** - 選擇要剪輯的章節和處理選項
5. **處理** - 剪輯影片、翻譯字幕、燒錄字幕（如果需要）
6. **輸出** - 組織文件到 `./youtube-clips/<時間戳>/`

### 輸出文件

每個剪輯的章節包含：

```
./youtube-clips/20260122_143022/
└── 章節標題/
    ├── 章節標題_clip.mp4              # 原始剪輯（無字幕）
    ├── 章節標題_with_subtitles.mp4   # 帶燒錄字幕的影片
    ├── 章節標題_bilingual.srt        # 雙語字幕文件
    └── 章節標題_summary.md           # 社交媒體文案
```

---

## 配置

本 skill 使用環境變量進行自定義配置。編輯 `~/.claude/skills/youtube-clipper/.env`：

### 主要設置

```bash
# FFmpeg 路徑（留空則自動檢測）
FFMPEG_PATH=

# 輸出目錄（默認：當前工作目錄）
OUTPUT_DIR=./youtube-clips

# 影片質量限制（720、1080、1440、2160）
MAX_VIDEO_HEIGHT=1080

# 翻譯批次大小（推薦 20-25）
TRANSLATION_BATCH_SIZE=20

# 目標翻譯語言
TARGET_LANGUAGE=中文

# 目標章節時長（秒，推薦 180-300）
TARGET_CHAPTER_DURATION=180
```

完整配置選項請參見 [.env.example](.env.example)。

---

## 使用示例

### 示例 1：從技術訪談中提取精華

**輸入**：

```
剪輯這個影片：https://youtube.com/watch?v=Ckt1cj0xjRM
```

**輸出**（AI 生成的章節）：

```
1. [00:00 - 03:15] AGI 是指數曲線而非時間點
2. [03:15 - 06:30] 中國在 AI 領域的差距
3. [06:30 - 09:45] 芯片禁令的影響
...
```

**結果**：選擇章節 → 獲得帶雙語字幕的剪輯影片 + 社交媒體文案

### 示例 2：從課程影片創建短片

**輸入**：

```
剪輯這個講座影片並創建雙語字幕：https://youtube.com/watch?v=LECTURE_ID
```

**選項**：

- 生成雙語字幕：是
- 燒錄字幕到影片：是
- 生成總結：是

**結果**：可直接在社交媒體平台分享的高質量剪輯影片

---

## 核心差異化功能

### AI 語義章節分析

與機械按時間切分不同，本 skill 使用 Claude AI 來：

- 理解內容語義
- 識別自然的主題轉換點
- 生成有意義的章節標題和摘要
- 確保完整覆蓋，無遺漏

**示例**：

```
❌ 機械切分：[0:00-30:00]、[30:00-60:00]
✅ AI 語義分析：
   - [00:00-03:15] AGI 定義
   - [03:15-07:30] 中國的 AI 格局
   - [07:30-12:00] 芯片禁令影響
```

### 批量翻譯優化

一次翻譯 20 條字幕，而非逐條翻譯：

- 減少 95% 的 API 調用
- 速度提升 10 倍
- 更好的翻譯一致性

### 雙語字幕格式

生成的字幕文件同時包含英文和中文：

```srt
1
00:00:00,000 --> 00:00:03,500
This is the English subtitle
這是中文字幕

2
00:00:03,500 --> 00:00:07,000
Another English line
另一行中文
```

---

## 常見問題

### FFmpeg 字幕燒錄失敗

**錯誤**：`Option not found: subtitles` 或 `filter not found`

**解決方案**：安裝 `ffmpeg-full`（macOS）或確保安裝了 `libass-dev`（Ubuntu）：

```bash
# macOS
brew uninstall ffmpeg
brew install ffmpeg-full

# Ubuntu
sudo apt install ffmpeg libass-dev
```

### 影片下載速度慢

**解決方案**：在 `.env` 中設置代理：

```bash
YT_DLP_PROXY=http://proxy-server:port
# 或
YT_DLP_PROXY=socks5://proxy-server:port
```

### 字幕翻譯失敗

**原因**：API 限流或網絡問題

**解決方案**：skill 會自動重試最多 3 次。如果持續失敗，請檢查：

- 網絡連接
- Claude API 狀態
- 減少 `.env` 中的 `TRANSLATION_BATCH_SIZE`

### 文件名包含特殊字符

**問題**：文件名中的 `:`、`/`、`?` 等可能導致錯誤

**解決方案**：skill 會自動清理文件名：

- 移除特殊字符：`/ \ : * ? " < > |`
- 將空格替換為下劃線
- 限制長度為 100 字符

---

## 文檔

- **[SKILL.md](SKILL.md)** - 完整工作流程和技術細節
- **[TECHNICAL_NOTES.md](TECHNICAL_NOTES.md)** - 實現筆記和設計決策
- **[FIXES_AND_IMPROVEMENTS.md](FIXES_AND_IMPROVEMENTS.md)** - 更新日誌和 Bug 修復
- **[references/](references/)** - FFmpeg、yt-dlp 和字幕格式指南

---

## 貢獻

歡迎貢獻！請：

- 通過 [GitHub Issues](https://github.com/op7418/Youtube-clipper-skill/issues) 報告 Bug
- 提交功能請求
- 為改進提交 Pull Request

---

## 許可證

本項目採用 MIT 許可證 - 詳見 [LICENSE](LICENSE) 文件。

---

## 致謝

- **[Claude Code](https://claude.ai/claude-code)** - AI 驅動的 CLI 工具
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - YouTube 下載引擎
- **[FFmpeg](https://ffmpeg.org/)** - 影片處理利器

---

<div align="center">

**Made with ❤️ by [op7418](https://github.com/op7418)**

如果這個 skill 對你有幫助，請給個 ⭐️

</div>
