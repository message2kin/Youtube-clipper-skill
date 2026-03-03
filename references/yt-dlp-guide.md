# yt-dlp 使用指南

yt-dlp 是一個強大的 YouTube 影片下載工具，本文檔介紹在 YouTube Clipper 中使用的核心功能。

## 安裝

### macOS

```bash
brew install yt-dlp
```

### Linux

```bash
# Ubuntu/Debian
sudo apt-get install yt-dlp

# 或使用 pip
pip install yt-dlp
```

### 更新

```bash
# Homebrew
brew upgrade yt-dlp

# pip
pip install --upgrade yt-dlp
```

## 基本用法

### 下載影片

```bash
# 下載最佳質量
yt-dlp https://youtube.com/watch?v=VIDEO_ID

# 指定格式
yt-dlp -f "best[ext=mp4]" URL

# 限制分辨率（最高 1080p）
yt-dlp -f "bestvideo[height<=1080]+bestaudio" URL
```

### 下載字幕

```bash
# 下載英文字幕
yt-dlp --write-sub --sub-lang en URL

# 下載自動生成字幕（如果沒有人工字幕）
yt-dlp --write-auto-sub --sub-lang en URL

# 下載所有可用字幕
yt-dlp --write-sub --all-subs URL

# 指定字幕格式（VTT, SRT, 等）
yt-dlp --write-sub --sub-format vtt URL
```

## YouTube Clipper 使用的配置

### 完整配置

```python
ydl_opts = {
    # 影片格式：最高 1080p，優先 mp4
    'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',

    # 輸出模板
    'outtmpl': '%(title)s [%(id)s].%(ext)s',

    # 下載字幕
    'writesubtitles': True,
    'writeautomaticsub': True,  # 自動字幕作為備選
    'subtitleslangs': ['en'],   # 英文字幕
    'subtitlesformat': 'vtt',   # VTT 格式

    # 不下載縮略圖
    'writethumbnail': False,
}
```

### 格式字符串解釋

```
bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best
│         │              │        │         │       │                           │
│         │              │        │         │       │                           └─ 最終備選
│         │              │        │         │       └─ 備選：最佳 1080p mp4
│         │              │        │         └─ 最佳音頻（m4a）
│         │              │        └─ 合併
│         │              └─ 優先 mp4 格式
│         └─ 最高 1080p
└─ 最佳影片質量
```

### 為什麼限制 1080p？

1. **文件大小**: 4K 影片可能 5-10GB
2. **處理速度**: FFmpeg 處理時間長
3. **實際需求**: 短片平台主要是 1080p
4. **存儲空間**: 節省磁盤

## 常用命令

### 1. 查看影片信息

```bash
# 不下載，僅顯示信息
yt-dlp --print-json URL

# 查看可用格式
yt-dlp -F URL
```

### 2. 下載播放列表

```bash
# 下載整個播放列表
yt-dlp PLAYLIST_URL

# 僅下載特定影片（1-5）
yt-dlp --playlist-items 1-5 PLAYLIST_URL

# 不下載播放列表，僅當前影片
yt-dlp --no-playlist URL
```

### 3. 代理設置

```bash
# HTTP 代理
yt-dlp --proxy http://proxy:port URL

# SOCKS5 代理
yt-dlp --proxy socks5://proxy:port URL
```

### 4. 速率限制

```bash
# 限制下載速度為 50KB/s
yt-dlp --rate-limit 50K URL

# 限制為 4.2MB/s
yt-dlp --rate-limit 4.2M URL
```

### 5. 自定義文件名

```bash
# 使用模板
yt-dlp -o "%(title)s.%(ext)s" URL

# 包含上傳日期
yt-dlp -o "%(upload_date)s - %(title)s.%(ext)s" URL

# 包含頻道名稱
yt-dlp -o "%(channel)s/%(title)s.%(ext)s" URL
```

## 字幕相關

### 字幕語言代碼

常用語言代碼：

- `en`: 英文
- `zh-Hans`: 簡體中文
- `zh-Hant`: 繁體中文
- `ja`: 日語
- `ko`: 韓語
- `es`: 西班牙語
- `fr`: 法語
- `de`: 德語

### 查看可用字幕

```bash
# 列出所有可用字幕
yt-dlp --list-subs URL
```

### 字幕格式

```bash
# VTT 格式（推薦，兼容性好）
yt-dlp --write-sub --sub-format vtt URL

# SRT 格式
yt-dlp --write-sub --sub-format srt URL

# 多種格式
yt-dlp --write-sub --sub-format "vtt,srt" URL
```

## Python API 使用

### 基本示例

```python
import yt_dlp

ydl_opts = {
    'format': 'best',
    'outtmpl': '%(title)s.%(ext)s',
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://youtube.com/watch?v=VIDEO_ID'])
```

### 獲取影片信息

```python
import yt_dlp

ydl_opts = {}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)

    print(f"Title: {info['title']}")
    print(f"Duration: {info['duration']} seconds")
    print(f"Uploader: {info['uploader']}")
```

### 進度回調

```python
def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
        print(f"Progress: {percent:.1f}%")
    elif d['status'] == 'finished':
        print("Download complete!")

ydl_opts = {
    'progress_hooks': [progress_hook],
}
```

## 常見問題

### Q: 下載失敗，提示 "Video unavailable"

A: 可能的原因：

- 影片已刪除或私有
- 地區限制（嘗試使用代理）
- 需要登錄（使用 `--cookies` 選項）

### Q: 字幕下載失敗

A: 嘗試：

1. 使用 `--write-auto-sub`（自動生成字幕）
2. 使用 `--list-subs` 查看可用字幕
3. 某些影片沒有字幕

### Q: 下載速度慢

A: 解決方案：

- 使用代理
- 檢查網絡連接
- YouTube 可能限速（等待後重試）

### Q: 文件名包含非法字符

A: 使用輸出模板清理：

```bash
yt-dlp -o "%(title).100s.%(ext)s" URL
# .100s 限制標題長度為 100 字符
```

### Q: 如何下載會員專屬影片？

A: 使用瀏覽器 cookies：

```bash
# 導出瀏覽器 cookies
yt-dlp --cookies-from-browser chrome URL

# 或使用 cookies 文件
yt-dlp --cookies cookies.txt URL
```

## 高級用法

### 批量下載

```bash
# 從文件讀取 URL 列表
yt-dlp -a urls.txt

# urls.txt 內容：
# https://youtube.com/watch?v=VIDEO1
# https://youtube.com/watch?v=VIDEO2
# https://youtube.com/watch?v=VIDEO3
```

### 後處理

```bash
# 下載後轉換為 MP3
yt-dlp -x --audio-format mp3 URL

# 下載後嵌入字幕
yt-dlp --embed-subs URL

# 下載後嵌入縮略圖
yt-dlp --embed-thumbnail URL
```

### 歸檔選項

```bash
# 跳過已下載的影片
yt-dlp --download-archive archive.txt PLAYLIST_URL

# archive.txt 會記錄已下載的影片 ID
```

## 支持的網站

yt-dlp 不僅支持 YouTube，還支持：

- Vimeo
- Twitter
- TikTok
- Bilibili
- 等 1000+ 網站

查看完整列表：

```bash
yt-dlp --list-extractors
```

## 參考鏈接

- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [yt-dlp 文檔](https://github.com/yt-dlp/yt-dlp#readme)
- [格式選擇説明](https://github.com/yt-dlp/yt-dlp#format-selection)
