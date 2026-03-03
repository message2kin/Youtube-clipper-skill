---
name: youtube-clipper
description: >
  YouTube 影片智能剪輯工具。下載影片和字幕，AI 分析生成精細章節（幾分鐘級別），
  用户選擇片段後自動剪輯、翻譯字幕為中英雙語、燒錄字幕到影片，並生成總結文案。
  使用場景：當用户需要剪輯 YouTube 影片、生成短片片段、製作雙語字幕版本時。
  關鍵詞：影片剪輯、YouTube、字幕翻譯、雙語字幕、影片下載、clip video
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - AskUserQuestion
model: claude-sonnet-4-5-20250514
---

# YouTube 影片智能剪輯工具

> **Installation**: If you're installing this skill from GitHub, please refer to [README.md](README.md#installation) for installation instructions. The recommended method is `npx skills add https://github.com/op7418/Youtube-clipper-skill`.

## 工作流程

你將按照以下 6 個階段執行 YouTube 影片剪輯任務：

### 階段 0: 模式選擇

**目標**: 確認用户想要製作哪種類型的影片

1. 詢問用户：
   - **Standard (默認)**: 16:9 橫屏，保留完整畫面，適合 YouTube 長影片切片。
   - **Shorts**: 9:16 豎屏裁剪，強力字幕樣式，<60s 片段，適合 TikTok/Shorts/Reels。
   - **Analysis Only**: 僅分析影片，生成章節和 Shorts 創意，不進行剪輯處理。適合作為 YouTube 影片優化的輔助工具。

**後續步驟差異**:

- 如果選擇 **Shorts**: 在後續所有腳本調用中添加 `--shorts` 參數。
- 如果選擇 **Analysis Only**:
  - 下載階段使用 `--subs-only`
  - 運行 `analyze_subtitles.py --analysis-only`
  - 生成包含 Standard 章節和 Viral Shorts 的綜合分析報告
  - 跳過剪輯和燒錄階段
  - 直接輸出文本報告

---

### 階段 1: 環境檢測

**目標**: 確保所有必需工具和依賴都已安裝

1. 檢測 yt-dlp 是否可用

   ```bash
   yt-dlp --version
   ```

2. 檢測 FFmpeg 版本和 libass 支持

   ```bash
   # 優先檢查 ffmpeg-full（macOS）
   /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg -version

   # 檢查標準 FFmpeg
   ffmpeg -version

   # 驗證 libass 支持（字幕燒錄必需）
   ffmpeg -filters 2>&1 | grep subtitles
   ```

3. 檢測 Python 依賴
   ```bash
   ./venv/bin/python3 -c "import yt_dlp; print('✅ yt-dlp available')"
   ./venv/bin/python3 -c "import pysrt; print('✅ pysrt available')"
   ./venv/bin/python3 -c "import anthropic; print('✅ anthropic available')"
   ```
   **注意**: 如果 `anthropic` 未安裝（用於章節分析），請運行：
   ```bash
   ./venv/bin/pip install anthropic
   ```

**如果環境檢測失敗**:

- yt-dlp 未安裝: 運行 `bash install_as_skill.sh` 重新安裝
- FFmpeg 無 libass: 提示安裝 ffmpeg-full
  ```bash
  brew install ffmpeg-full  # macOS
  ```
- Python 依賴缺失: 運行 `bash install_as_skill.sh` 重新安裝

**注意**:

- 標準 Homebrew FFmpeg 不包含 libass，無法燒錄字幕
- ffmpeg-full 路徑: `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg` (Apple Silicon)
- 必須先通過環境檢測才能繼續

4. 檢測 Whisper (可選，用於自動生成字幕)
   ```bash
   ./venv/bin/python3 -c "import whisper; print('✅ whisper available')"
   ```
5. 檢測 Whisper (可選，用於自動生成字幕)
   ```bash
   ./venv/bin/python3 -c "import whisper; print('✅ whisper available')"
   ```
   如果未安裝：
   ```bash
   ./venv/bin/pip install openai-whisper
   ```

---

### 階段 2: 下載影片

**目標**: 下載 YouTube 影片和英文字幕

1. 詢問用户 YouTube URL

2. 調用 download_video.py 腳本

   ```bash
   cd ~/.claude/skills/youtube-clipper
   ./venv/bin/python3 scripts/download_video.py <youtube_url> [--subs-only]
   ```

   - **Analysis Only 模式**: 添加 `--subs-only` 參數。如果影片有字幕，將跳過影片下載；如果無字幕，會自動下載影片以進行後續轉錄。

3. 腳本會：

   - 下載影片（最高 1080p，mp4 格式）
   - 下載字幕（優先中文/粵語，其次英文，最後自動生成）
   - 輸出文件路徑和影片信息

4. 向用户展示：
   - 影片標題
   - 影片時長
   - 文件大小
   - 下載路徑

**輸出**:

- 影片文件: `<id>.mp4`
- 字幕文件: `<id>.<lang>.vtt` (如 `.zh-Hant.vtt` 或 `.en.vtt`)

### 階段 2.5: 自動生成字幕 (Fallback)

**目標**: 當無法從 YouTube 下載字幕時，使用 Whisper 本地生成

**如果階段 2 未找到字幕**:

1. 詢問用户是否生成字幕

   - 是否生成？
   - 偏好的模型大小？(默認 `base`, 可選 `small`, `medium`)
   - 偏好的語言？(默認自動檢測, 可選 `zh`, `en`, `ja`)
   - 提示：需安裝 `openai-whisper`，較大模型生成速度較慢 (medium 可能需要幾分鐘)

2. 調用 transcribe_audio.py

   ```bash
   ./venv/bin/python3 scripts/transcribe_audio.py <video_path> [model_size] [language]
   ```

   - model_size: `base` (默認，快), `small`, `medium` (更準但慢)
   - language: `zh`, `en`, `ja` 等 (可選，指定語言可提高準確率)

3. 輸出:
   - 字幕文件: `<video_filename>.vtt`

---

### 階段 3: 分析章節（核心差異化功能）

**目標**: 使用 Claude AI 分析字幕內容，生成精細章節（2-5 分鐘級別）

1. 調用 analyze_subtitles.py 解析 VTT 字幕

   ```bash
   # Standard
   ./venv/bin/python3 scripts/analyze_subtitles.py <subtitle_path>

   # Shorts Mode (專用腳本，<60s 粒度)
   ./venv/bin/python3 scripts/analyze_shorts.py <subtitle_path>

   # Analysis Only Mode
   # 運行 analyze_subtitles.py 並添加 --analysis-only 參數
   ./venv/bin/python3 scripts/analyze_subtitles.py <subtitle_path> --analysis-only
   # 輸出將提示生成 Standard 章節和 Viral Shorts
   ```

2. 腳本會輸出結構化字幕數據：

   - 完整字幕文本（帶時間戳）
   - 總時長
   - 字幕條數

3. **你需要執行 AI 分析**（這是最關鍵的步驟）：

   - 閲讀完整字幕內容
   - 理解內容語義和主題轉換點
   - 識別自然的話題切換位置
   - 生成 2-5 分鐘粒度的章節（Standard 模式）
   - 生成 < 60 秒 的高能片段（Shorts 模式）

4. 為每個章節生成：

   - **標題**: 精煉的主題概括（10-20 字）
   - **時間範圍**: 起始和結束時間（格式: MM:SS 或 HH:MM:SS）
   - **核心摘要**: 1-2 句話説明這段講了什麼（50-100 字）
   - **關鍵詞**: 3-5 個核心概念詞

5. **章節生成原則**：

   - 粒度：每個章節 2-5 分鐘（避免太短或太長）
   - 完整性：確保所有影片內容都被覆蓋，無遺漏
   - 有意義：每個章節是一個相對獨立的話題
   - 自然切分：在主題轉換點切分，不要機械地按時間切
   - **Shorts 特別提示**: 尋找反差、金句、情緒高點，開頭前 3 秒必須吸引人。

6. 向用户展示章節列表：

   ```
   📊 分析完成，生成 X 個章節：

   1. [00:00 - 03:15] AGI 不是時間點，是指數曲線
      核心: AI 模型能力每 4-12 月翻倍，工程師已用 Claude 寫代碼
      關鍵詞: AGI、指數增長、Claude Code

   2. [03:15 - 06:30] 中國在 AI 上的差距
      核心: 芯片禁運卡住中國，DeepSeek benchmark 優化不代表實力
      關鍵詞: 中國、芯片禁運、DeepSeek

   ... (所有章節)

   ✓ 所有內容已覆蓋，無遺漏
   ```

---

### 階段 4: 用户選擇

**目標**: 讓用户選擇要剪輯的章節和處理選項

1. 使用 AskUserQuestion 工具讓用户選擇章節

   - 提供章節編號供用户選擇
   - 支持多選（可以選擇多個章節）

2. 詢問處理選項：

   - 是否生成雙語字幕？（英文 + 中文）
   - 是否燒錄字幕到影片？（硬字幕）
   - 是否生成總結文案？

3. 確認用户選擇並展示處理計劃
   - **Analysis Only 模式**: 跳過此階段，直接輸出所有分析結果(格式: MM:SS <章節標題>)。

---

### 階段 5: 剪輯處理（核心執行階段）

**目標**: 並行執行多個處理任務

**目標**: 並行執行多個處理任務（Analysis Only 模式跳過此階段）

對於每個用户選擇的章節，執行以下步驟：

#### 5.1 剪輯影片片段

```bash
./venv/bin/python3 scripts/clip_video.py <video_path> <start_time> <end_time> <output_path> [--shorts]
```

- 使用 FFmpeg 精確剪輯
- **Shorts 模式**: 自動應用 9:16 中心裁剪
- 保持原始影片質量
- 輸出: `<章節標題>_clip.mp4`

#### 5.2 提取字幕片段

- 從完整字幕中過濾出該時間段的字幕
- 調整時間戳（減去起始時間，從 00:00:00 開始）
- 轉換為 SRT 格式
- 輸出: `<章節標題>_original.srt`

#### 5.3 翻譯字幕（如果用户選擇）

```bash
./venv/bin/python3 scripts/translate_subtitles.py <subtitle_path>
```

- **批量翻譯優化**: 每批 20 條字幕一起翻譯（節省 95% API 調用）
- 翻譯策略：
  - 保持技術術語的準確性
  - 口語化表達（適合短片）
  - 簡潔流暢（避免冗長）
- 輸出: `<章節標題>_translated.srt`

#### 5.4 生成雙語字幕文件（如果用户選擇）

- 合併英文和中文字幕
- 格式: SRT 雙語（每條字幕包含英文和中文）
- 樣式: 英文在上，中文在下
- 輸出: `<章節標題>_bilingual.srt`

#### 5.5 燒錄字幕到影片（如果用户選擇）

```bash
./venv/bin/python3 scripts/burn_subtitles.py <video_path> <subtitle_path> <output_path> [--shorts]
```

- 使用 ffmpeg-full（libass 支持）
- **使用臨時目錄解決路徑空格問題**（關鍵！）
- 字幕樣式（Standard）：
  - 字體大小: 24, 底部邊距: 30, 白色
- 字幕樣式（Shorts）：
  - 字體大小: 40, 底部邊距: 500 (避開 UI), 黃色高亮, 粗體
- 輸出: `<章節標題>_with_subtitles.mp4`

#### 5.6 生成總結文案（如果用户選擇）

```bash
./venv/bin/python3 scripts/generate_summary.py <chapter_info>
```

- 基於章節標題、摘要和關鍵詞
- 生成適合社交媒體的文案
- 包含: 標題、核心觀點、適合平台（小紅書、抖音等）
- 輸出: `<章節標題>_summary.md`

**進度展示**:

```
🎬 開始處理章節 1/3: AGI 不是時間點，是指數曲線

1/6 剪輯影片片段... ✅
2/6 提取字幕片段... ✅
3/6 翻譯字幕為中文... [=====>    ] 50% (26/52)
4/6 生成雙語字幕文件... ✅
5/6 燒錄字幕到影片... ✅
6/6 生成總結文案... ✅

✨ 章節 1 處理完成
```

---

### 階段 6: 輸出結果

**目標**: 組織輸出文件並展示給用户

1. 創建輸出目錄

   ```
   ./youtube-clips/<日期時間>/
   ```

   輸出目錄位於當前工作目錄下

2. 組織文件結構：

   ```
   <章節標題>/
   ├── <章節標題>_clip.mp4              # 原始剪輯（無字幕）
   ├── <章節標題>_with_subtitles.mp4   # 燒錄字幕版本
   ├── <章節標題>_bilingual.srt        # 雙語字幕文件
   └── <章節標題>_summary.md           # 總結文案
   ```

3. 向用户展示：

   - 輸出目錄路徑
   - 文件列表（帶文件大小）
   - 快速預覽命令

   ```
   ✨ 處理完成！

   📁 輸出目錄: ./youtube-clips/20260121_143022/

   文件列表:
     🎬 AGI_指數曲線_雙語硬字幕.mp4 (14 MB)
     📄 AGI_指數曲線_雙語字幕.srt (2.3 KB)
     📝 AGI_指數曲線_總結.md (3.2 KB)

   快速預覽:
   open ./youtube-clips/20260121_143022/AGI_指數曲線_雙語硬字幕.mp4
   ```

4. 詢問是否繼續剪輯其他章節
   - 如果是，返回階段 4（用户選擇）
   - 如果否，結束 Skill

---

## 關鍵技術點

### 1. FFmpeg 路徑空格問題

**問題**: FFmpeg subtitles 濾鏡無法正確解析包含空格的路徑

**解決方案**: burn_subtitles.py 使用臨時目錄

- 創建無空格臨時目錄
- 複製文件到臨時目錄
- 執行 FFmpeg
- 移動輸出文件回目標位置

### 2. 批量翻譯優化

**問題**: 逐條翻譯會產生大量 API 調用

**解決方案**: 每批 20 條字幕一起翻譯

- 節省 95% API 調用
- 提高翻譯速度
- 保持翻譯一致性

### 3. 章節分析精細度

**目標**: 生成 2-5 分鐘粒度的章節，避免半小時粗粒度

**方法**:

- 理解字幕語義，識別主題轉換
- 尋找自然的話題切換點
- 確保每個章節有完整的論述
- 避免機械按時間切分

### 4. FFmpeg vs ffmpeg-full

**區別**:

- 標準 FFmpeg: 無 libass 支持，無法燒錄字幕
- ffmpeg-full: 包含 libass，支持字幕燒錄

**路徑**:

- 標準: `/opt/homebrew/bin/ffmpeg`
- ffmpeg-full: `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg` (Apple Silicon)
  350:
  351: ### 5. Shorts 模式優化
  352: - **裁剪**: `crop=ih*(9/16):ih:(iw-ow)/2:0` 保持中心主體
  353: - **樣式**: 黃色大號字體，大幅度上移，確保在手機小屏上清晰可見且不被 UI 遮擋
  354: - **時長**: 聚焦 < 60s 完播率高的片段

---

## 錯誤處理

### 環境問題

- 缺少工具 → 提示安裝命令
- FFmpeg 無 libass → 引導安裝 ffmpeg-full
- Python 依賴缺失 → 提示 pip install

### 下載問題

- 無效 URL → 提示檢查 URL 格式
- 字幕缺失 → 嘗試自動字幕
- 網絡錯誤 → 提示重試

### 處理問題

- FFmpeg 執行失敗 → 顯示詳細錯誤信息
- 翻譯失敗 → 重試機制（最多 3 次）
- 磁盤空間不足 → 提示清理空間

---

## 輸出文件命名規範

- 影片片段: `<章節標題>_clip.mp4`
- 字幕文件: `<章節標題>_bilingual.srt`
- 燒錄版本: `<章節標題>_with_subtitles.mp4`
- 總結文案: `<章節標題>_summary.md`

**文件名處理**:

- 移除特殊字符（`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`）
- 空格替換為下劃線
- 限制長度（最多 100 字符）

---

## 用户體驗要點

1. **進度可見**: 每個步驟都展示進度和狀態
2. **錯誤友好**: 清晰的錯誤信息和解決方案
3. **可控性**: 用户選擇要剪輯的章節和處理選項
4. **高質量**: 章節分析有意義，翻譯準確流暢
5. **完整性**: 提供原始和處理後的多個版本

---

## 開始執行

當用户觸發這個 Skill 時：

1. 立即開始階段 1（環境檢測）
2. 按照 6 個階段順序執行
3. 每個階段完成後自動進入下一階段
4. 遇到問題時提供清晰的解決方案
5. 最後展示完整的輸出結果

記住：這個 Skill 的核心價值在於 **AI 精細章節分析** 和 **無縫的技術處理**，讓用户能快速從長影片中提取高質量的短片片段。
