# 技術陷阱記錄

本文檔記錄 YouTube Clipper Skill 開發過程中遇到的關鍵技術問題和解決方案。

## 1. FFmpeg libass 支持問題

### 問題描述

標準 Homebrew FFmpeg 不包含 libass 庫，導致無法使用 `subtitles` 濾鏡燒錄字幕。

### 錯誤信息

```
No such filter: 'subtitles'
```

或者在檢查濾鏡時：

```bash
$ ffmpeg -filters 2>&1 | grep subtitles
# 無輸出
```

### 根本原因

- Homebrew 的標準 `ffmpeg` formula 為了減小包體積，不包含某些非核心庫
- libass 是字幕渲染庫，用於 `subtitles` 濾鏡
- 沒有 libass，FFmpeg 無法燒錄字幕到影片

### 解決方案

#### macOS

使用 `ffmpeg-full` 替代標準 FFmpeg：

```bash
# 安裝 ffmpeg-full
brew install ffmpeg-full

# 路徑（Apple Silicon）
/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg

# 路徑（Intel）
/usr/local/opt/ffmpeg-full/bin/ffmpeg

# 驗證 libass 支持
/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg -filters 2>&1 | grep subtitles
```

#### 其他系統

從源碼編譯 FFmpeg，確保包含 libass：

```bash
# Ubuntu/Debian
sudo apt-get install libass-dev
./configure --enable-libass
make
sudo make install

# 驗證
ffmpeg -filters 2>&1 | grep subtitles
```

### 檢測邏輯

`burn_subtitles.py` 中實現的檢測邏輯：

1. 優先檢查 `ffmpeg-full` 路徑（macOS）
2. 檢查標準 `ffmpeg` 是否支持 libass
3. 如果都不滿足，提示安裝指南

```python
def detect_ffmpeg_variant():
    # 檢查 ffmpeg-full（macOS）
    if platform.system() == 'Darwin':
        full_path = '/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg'
        if Path(full_path).exists():
            return {'type': 'full', 'path': full_path}

    # 檢查標準 ffmpeg
    standard_path = shutil.which('ffmpeg')
    if standard_path:
        has_libass = check_libass_support(standard_path)
        return {'has_libass': has_libass}
```

---

## 2. 文件路徑空格問題

### 問題描述

FFmpeg `subtitles` 濾鏡無法正確處理包含空格的文件路徑，即使使用引號或轉義也無效。

### 錯誤信息

```
[Parsed_subtitles_0 @ 0x...] Unable to find '/path/with'
```

注意路徑被截斷在空格處（`/path/with spaces` → `/path/with`）。

### 示例

```bash
# 失敗的嘗試
ffmpeg -i video.mp4 -vf "subtitles='/path/with spaces/sub.srt'" output.mp4
ffmpeg -i video.mp4 -vf "subtitles=/path/with\ spaces/sub.srt" output.mp4
ffmpeg -i video.mp4 -vf subtitles="'/path/with spaces/sub.srt'" output.mp4

# 都會報錯：Unable to find '/path/with'
```

### 根本原因

FFmpeg `subtitles` 濾鏡的路徑解析存在 bug，無法正確處理：

- 引號內的空格
- 轉義的空格
- 混合引號

這是 FFmpeg 的已知限制。

### 解決方案：使用臨時目錄

核心思路：將文件複製到**無空格路徑**的臨時目錄，處理後再移回。

```python
import tempfile
import shutil

def burn_subtitles(video_path, subtitle_path, output_path):
    # 1. 創建臨時目錄（路徑保證無空格）
    temp_dir = tempfile.mkdtemp(prefix='youtube_clipper_')
    # 例如: /tmp/youtube_clipper_abc123

    try:
        # 2. 複製文件到臨時目錄
        temp_video = os.path.join(temp_dir, 'video.mp4')
        temp_subtitle = os.path.join(temp_dir, 'subtitle.srt')
        shutil.copy(video_path, temp_video)
        shutil.copy(subtitle_path, temp_subtitle)

        # 3. 執行 FFmpeg（路徑無空格）
        cmd = [
            'ffmpeg',
            '-i', temp_video,
            '-vf', f'subtitles={temp_subtitle}',
            temp_output
        ]
        subprocess.run(cmd, check=True)

        # 4. 移動輸出文件到目標位置
        shutil.move(temp_output, output_path)

    finally:
        # 5. 清理臨時目錄
        shutil.rmtree(temp_dir, ignore_errors=True)
```

### 為什麼這樣有效？

- `tempfile.mkdtemp()` 生成的路徑不包含空格（通常是 `/tmp/xxx`）
- FFmpeg 可以正確處理無空格的路徑
- 對用户透明，輸入輸出可以有任意路徑

### 其他嘗試過但無效的方案

❌ 使用雙引號：`subtitles="/path/with spaces/sub.srt"`
❌ 使用單引號：`subtitles='/path/with spaces/sub.srt'`
❌ 轉義空格：`subtitles=/path/with\ spaces/sub.srt`
❌ 混合引號：`subtitles="'/path/with spaces/sub.srt'"`
❌ FFmpeg `-filter_complex`：仍然有同樣問題

✅ **唯一有效**：臨時目錄方案

---

## 3. VTT 轉 SRT 格式轉換

### 格式差異

| 項目       | VTT      | SRT               |
| ---------- | -------- | ----------------- |
| 頭部       | `WEBVTT` | 無                |
| 序號       | 可選     | 必需（從 1 開始） |
| 時間分隔符 | `.` (點) | `,` (逗號)        |
| 樣式信息   | 支持     | 不支持            |

### 時間戳格式

```
VTT:  00:00:00.000 --> 00:00:03.500
SRT:  00:00:00,000 --> 00:00:03,500
              ↑                  ↑
            逗號                逗號
```

### 轉換實現

```python
def vtt_to_srt(vtt_path, srt_path):
    # 1. 移除 WEBVTT 頭部
    content = content.replace('WEBVTT\n\n', '')

    # 2. 移除樣式信息
    content = re.sub(r'STYLE.*?-->', '', content, flags=re.DOTALL)

    # 3. 轉換時間戳分隔符
    # . → , (僅在時間戳中)
    content = re.sub(
        r'(\d{2}:\d{2}:\d{2})\.(\d{3})',
        r'\1,\2',
        content
    )

    # 4. 添加序號（如果沒有）
    # ...
```

### 注意事項

- VTT 可能包含位置信息（`align:start position:0%`），需要移除
- VTT 可能有多行文本，轉 SRT 時保持多行
- 時間戳格式嚴格：`HH:MM:SS,mmm`（必須有小時）

---

## 4. 字幕時間戳調整

### 問題描述

剪輯影片後，字幕時間戳需要相對於新的起始時間。

### 示例

原影片：

```
[00:02:00] 字幕1
[00:02:03] 字幕2
[00:02:06] 字幕3
```

剪輯 02:00-02:10 後，字幕應該變為：

```
[00:00:00] 字幕1
[00:00:03] 字幕2
[00:00:06] 字幕3
```

### 實現

```python
def adjust_subtitle_time(time_seconds, offset):
    """
    調整字幕時間戳

    Args:
        time_seconds: 原始時間（秒）
        offset: 偏移量（秒），即剪輯起始時間

    Returns:
        float: 調整後的時間
    """
    adjusted = time_seconds - offset
    return max(0.0, adjusted)  # 確保不為負數
```

### 邊界情況處理

1. 字幕完全在時間範圍內：保留
2. 字幕完全在時間範圍外：丟棄
3. 字幕跨越邊界：
   - 起始時間調整為 0（如果在範圍前）
   - 結束時間調整為片段時長（如果在範圍後）

---

## 5. 批量翻譯優化

### 問題

逐條翻譯字幕會產生大量 API 調用，速度慢且成本高。

### 數據

- 一個 30 分鐘影片：約 600 條字幕
- 逐條翻譯：600 次 API 調用
- 批量翻譯（20 條/批）：30 次 API 調用
- **節省 95% API 調用**

### 實現策略

```python
def translate_batch(subtitles, batch_size=20):
    batches = []
    for i in range(0, len(subtitles), batch_size):
        batch = subtitles[i:i + batch_size]
        batches.append(batch)

    # 每批一起翻譯
    for batch in batches:
        # 合併為單個文本
        batch_text = '\n'.join([sub['text'] for sub in batch])

        # 一次 API 調用翻譯整批
        translations = translate_text(batch_text)

        # 分配翻譯結果
        # ...
```

### 批量大小選擇

- **20 條**是平衡點：
  - 小於 20：API 調用過多
  - 大於 30：單次輸入過長，翻譯質量下降
  - 20-25：最佳範圍

### 翻譯質量保證

批量翻譯時需要：

1. 保持上下文連貫性
2. 每條字幕單獨翻譯（不要合併）
3. 返回 JSON 數組，順序對應

---

## 6. yt-dlp 最佳實踐

### 格式選擇

```python
'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
```

解釋：

- `bestvideo[height<=1080]`：影片最高 1080p
- `[ext=mp4]`：優先 mp4 格式（兼容性好）
- `+bestaudio[ext=m4a]`：合併最佳音頻
- `/best[height<=1080][ext=mp4]`：備選方案
- `/best`：最終備選

### 為什麼限制 1080p？

1. 文件大小：4K 影片太大（可能 5-10GB）
2. 處理速度：FFmpeg 處理時間長
3. 輸出場景：短片平台主要是 1080p 或更低
4. 存儲空間：節省磁盤

### 字幕下載

```python
'writesubtitles': True,
'writeautomaticsub': True,  # 自動字幕作為備選
'subtitleslangs': ['en'],   # 英文字幕
'subtitlesformat': 'vtt',   # VTT 格式
```

優先級：

1. 人工字幕（如果有）
2. 自動字幕（YouTube 自動生成）

### 輸出模板

```python
'outtmpl': '%(title)s [%(id)s].%(ext)s'
```

結果示例：

```
Anthropic's Amodei on AI [Ckt1cj0xjRM].mp4
Anthropic's Amodei on AI [Ckt1cj0xjRM].en.vtt
```

包含影片 ID 的好處：

- 唯一性：不會重複
- 可追溯：可以找到原影片

---

## 7. 雙語字幕樣式

### SRT 格式雙語

```srt
1
00:00:00,000 --> 00:00:03,500
This is English subtitle
這是中文字幕

2
00:00:03,500 --> 00:00:07,000
Another English line
另一行中文
```

### FFmpeg 燒錄樣式

```bash
subtitles=subtitle.srt:force_style='FontSize=24,MarginV=30'
```

參數説明：

- `FontSize=24`：字體大小（適合 1080p）
- `MarginV=30`：底部邊距（像素）
- 默認：白色文字 + 黑色描邊

### 樣式調整建議

| 影片分辨率 | FontSize | MarginV |
| ---------- | -------- | ------- |
| 720p       | 20       | 20      |
| 1080p      | 24       | 30      |
| 4K         | 48       | 60      |

---

## 8. Python 依賴管理

### 必需依賴

```bash
pip install yt-dlp pysrt python-dotenv
```

- `yt-dlp`：YouTube 影片下載
- `pysrt`：SRT 字幕解析和操作
- `python-dotenv`：環境變量管理（可選）

### 導入錯誤處理

```python
try:
    import yt_dlp
except ImportError:
    print("❌ Error: yt-dlp not installed")
    print("Please install: pip install yt-dlp")
    sys.exit(1)
```

在每個腳本中檢查依賴，給出清晰的安裝指導。

---

## 9. 跨平台路徑處理

### 使用 pathlib

```python
from pathlib import Path

# ✅ 推薦
video_path = Path('/path/to/video.mp4')
if video_path.exists():
    ...

# ❌ 避免
video_path = '/path/to/video.mp4'
if os.path.exists(video_path):
    ...
```

### 路徑拼接

```python
# ✅ 推薦
output_path = output_dir / 'video.mp4'

# ❌ 避免
output_path = output_dir + '/video.mp4'  # 在 Windows 上失敗
```

---

## 10. 錯誤處理最佳實踐

### 詳細錯誤信息

```python
try:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Command failed:")
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Return code: {result.returncode}")
        print(f"   Error output:")
        print(result.stderr)
        raise RuntimeError("Command failed")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
```

### 用户友好的錯誤消息

```python
# ❌ 不好
raise Exception("FFmpeg failed")

# ✅ 好
raise RuntimeError(
    "FFmpeg does not support libass (subtitles filter). "
    "Please install ffmpeg-full: brew install ffmpeg-full"
)
```

---

## 總結

| 問題               | 解決方案             | 優先級  |
| ------------------ | -------------------- | ------- |
| FFmpeg libass 缺失 | 安裝 ffmpeg-full     | 🔴 必須 |
| 路徑空格問題       | 使用臨時目錄         | 🔴 必須 |
| VTT → SRT          | 轉換時間分隔符       | 🟡 重要 |
| 字幕時間調整       | 減去起始時間         | 🟡 重要 |
| API 調用過多       | 批量翻譯（20 條/批） | 🟢 優化 |
| 文件過大           | 限制 1080p           | 🟢 優化 |

所有關鍵問題都有經過驗證的解決方案，可以直接使用。
