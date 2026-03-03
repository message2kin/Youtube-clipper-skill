# FFmpeg 使用指南

FFmpeg 是一個強大的多媒體處理工具，本文檔介紹在 YouTube Clipper 中使用的核心命令。

## 安裝

### macOS

```bash
# 標準版本（不支持字幕燒錄）
brew install ffmpeg

# 完整版本（推薦，支持字幕燒錄）
brew install ffmpeg-full
```

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install ffmpeg libass-dev
```

### 驗證安裝

```bash
# 檢查版本
ffmpeg -version

# 檢查 libass 支持（字幕燒錄必需）
ffmpeg -filters 2>&1 | grep subtitles
```

## 常用命令

### 1. 剪輯影片

```bash
# 精確剪輯（從 30 秒開始，持續 60 秒）
ffmpeg -ss 30 -i input.mp4 -t 60 -c copy output.mp4

# 從 01:30:00 到 01:33:15
ffmpeg -ss 01:30:00 -i input.mp4 -to 01:33:15 -c copy output.mp4
```

**參數説明**:

- `-ss`: 起始時間
- `-i`: 輸入文件
- `-t`: 持續時間
- `-to`: 結束時間
- `-c copy`: 直接複製流，不重新編碼（快速且無損）

### 2. 燒錄字幕

```bash
# 燒錄 SRT 字幕到影片
ffmpeg -i input.mp4 \
  -vf "subtitles=subtitle.srt" \
  -c:a copy \
  output.mp4

# 自定義字幕樣式
ffmpeg -i input.mp4 \
  -vf "subtitles=subtitle.srt:force_style='FontSize=24,MarginV=30'" \
  -c:a copy \
  output.mp4
```

**注意**:

- 需要 libass 支持
- 路徑不能包含空格（使用臨時目錄解決）
- 影片會重新編碼（比剪輯慢）

### 3. 影片壓縮

```bash
# 使用 H.264 壓縮
ffmpeg -i input.mp4 \
  -c:v libx264 \
  -crf 23 \
  -c:a aac \
  output.mp4
```

**CRF 值**:

- 18: 高質量，文件較大
- 23: 平衡（推薦）
- 28: 低質量，文件較小

### 4. 提取音頻

```bash
# 提取為 MP3
ffmpeg -i input.mp4 -vn -acodec libmp3lame -q:a 2 output.mp3

# 提取為 AAC
ffmpeg -i input.mp4 -vn -c:a copy output.aac
```

### 5. 影片信息

```bash
# 查看影片詳細信息
ffmpeg -i input.mp4

# 查看簡潔信息
ffprobe -v error -show_format -show_streams input.mp4
```

## 字幕相關

### 燒錄雙語字幕

```bash
# 雙語字幕（每條字幕包含兩行）
ffmpeg -i input.mp4 \
  -vf "subtitles=bilingual.srt:force_style='FontSize=24,MarginV=30'" \
  -c:a copy \
  output.mp4
```

### 調整字幕樣式

可用樣式選項：

- `FontSize`: 字體大小（推薦 20-28）
- `MarginV`: 垂直邊距（推薦 20-40）
- `FontName`: 字體名稱
- `PrimaryColour`: 主要顏色
- `OutlineColour`: 描邊顏色
- `Bold`: 粗體（0 或 1）

示例：

```bash
subtitles=subtitle.srt:force_style='FontSize=28,MarginV=40,Bold=1'
```

## 性能優化

### 硬件加速

```bash
# macOS (VideoToolbox)
ffmpeg -hwaccel videotoolbox -i input.mp4 ...

# NVIDIA GPU
ffmpeg -hwaccel cuda -i input.mp4 ...
```

### 多線程

```bash
# 使用 4 個線程
ffmpeg -threads 4 -i input.mp4 ...
```

## 常見問題

### Q: 字幕燒錄失敗，提示 "No such filter: 'subtitles'"

A: FFmpeg 沒有 libass 支持。macOS 需要安裝 `ffmpeg-full`。

### Q: 路徑包含空格導致字幕燒錄失敗

A: 使用臨時目錄，將文件複製到無空格路徑再處理。

### Q: 影片質量下降

A: 使用 `-c copy` 直接複製流，或降低 CRF 值（如 18）。

### Q: 處理速度慢

A:

- 使用硬件加速 (`-hwaccel`)
- 剪輯時使用 `-c copy`
- 增加線程數 (`-threads`)

## 參考鏈接

- [FFmpeg 官方文檔](https://ffmpeg.org/documentation.html)
- [FFmpeg Wiki](https://trac.ffmpeg.org/wiki)
- [Subtitles 濾鏡文檔](https://ffmpeg.org/ffmpeg-filters.html#subtitles)
