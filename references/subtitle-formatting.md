# 字幕格式規範

本文檔介紹 YouTube Clipper 中使用的字幕格式及其轉換方法。

## 支持的格式

### 1. VTT (WebVTT)

WebVTT 是 Web 影片字幕標準格式。

#### 格式示例

```vtt
WEBVTT

1
00:00:00.000 --> 00:00:03.500
This is the first subtitle

2
00:00:03.500 --> 00:00:07.000
This is the second subtitle
```

#### 特點

- 頭部必須是 `WEBVTT`
- 時間戳使用點 (`.`) 分隔毫秒
- 支持樣式和位置信息
- YouTube 默認字幕格式

#### 完整示例

```vtt
WEBVTT

STYLE
::cue {
  background-color: rgba(0,0,0,0.8);
  color: white;
}

1
00:00:00.000 --> 00:00:03.500 align:start position:0%
<v Speaker>This is the first subtitle</v>

NOTE This is a comment

2
00:00:03.500 --> 00:00:07.000
This is the second subtitle
with multiple lines
```

---

### 2. SRT (SubRip)

SRT 是最常用的字幕格式，兼容性好。

#### 格式示例

```srt
1
00:00:00,000 --> 00:00:03,500
This is the first subtitle

2
00:00:03,500 --> 00:00:07,000
This is the second subtitle
```

#### 特點

- 沒有頭部
- 時間戳使用逗號 (`,`) 分隔毫秒
- 不支持樣式（但 FFmpeg 可以覆蓋）
- 兼容性最好

#### 多行文本

```srt
1
00:00:00,000 --> 00:00:03,500
This is the first line
This is the second line
This is the third line

2
00:00:03,500 --> 00:00:07,000
Single line subtitle
```

---

## VTT 與 SRT 對比

| 特性       | VTT              | SRT        |
| ---------- | ---------------- | ---------- |
| 頭部       | 必須（`WEBVTT`） | 無         |
| 毫秒分隔符 | 點 (`.`)         | 逗號 (`,`) |
| 樣式支持   | 是               | 否         |
| 位置控制   | 是               | 否         |
| 註釋支持   | 是               | 否         |
| 兼容性     | Web              | 通用       |

---

## 格式轉換

### VTT → SRT

#### Python 實現

```python
import re

def vtt_to_srt(vtt_content):
    # 1. 移除 WEBVTT 頭部
    srt_content = re.sub(r'^WEBVTT.*?\n\n', '', vtt_content, flags=re.DOTALL)

    # 2. 移除樣式信息
    srt_content = re.sub(r'STYLE.*?\n\n', '', srt_content, flags=re.DOTALL)

    # 3. 移除 NOTE
    srt_content = re.sub(r'NOTE.*?\n\n', '', srt_content, flags=re.DOTALL)

    # 4. 轉換時間戳分隔符: . → ,
    srt_content = re.sub(
        r'(\d{2}:\d{2}:\d{2})\.(\d{3})',
        r'\1,\2',
        srt_content
    )

    # 5. 移除位置信息
    srt_content = re.sub(
        r'(-->.*?)\s+(align|position|line|size):.*',
        r'\1',
        srt_content
    )

    # 6. 移除説話人標籤 <v Speaker>
    srt_content = re.sub(r'<v [^>]+>', '', srt_content)
    srt_content = re.sub(r'</v>', '', srt_content)

    return srt_content
```

#### 命令行工具

```bash
# 使用 ffmpeg
ffmpeg -i input.vtt output.srt

# 使用 sed
sed 's/\./,/3' input.vtt > output.srt  # 簡單轉換（不完整）
```

### SRT → VTT

#### Python 實現

```python
def srt_to_vtt(srt_content):
    # 1. 添加 WEBVTT 頭部
    vtt_content = "WEBVTT\n\n" + srt_content

    # 2. 轉換時間戳分隔符: , → .
    vtt_content = re.sub(
        r'(\d{2}:\d{2}:\d{2}),(\d{3})',
        r'\1.\2',
        vtt_content
    )

    return vtt_content
```

---

## 雙語字幕

### SRT 格式

雙語字幕在 SRT 中使用多行文本：

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

### 樣式建議

燒錄到影片時的樣式：

```bash
ffmpeg -i video.mp4 \
  -vf "subtitles=bilingual.srt:force_style='FontSize=24,MarginV=30'" \
  output.mp4
```

推薦參數：

- `FontSize=24`: 適合 1080p 影片
- `MarginV=30`: 底部邊距 30 像素
- 英文在上，中文在下

---

## 時間戳格式

### 完整格式

```
HH:MM:SS.mmm --> HH:MM:SS.mmm
```

- `HH`: 小時（00-99）
- `MM`: 分鐘（00-59）
- `SS`: 秒（00-59）
- `mmm`: 毫秒（000-999）

### 示例

```
00:00:00.000  # 0 秒
00:00:03.500  # 3.5 秒
00:01:30.250  # 1 分 30.25 秒
01:23:45.678  # 1 小時 23 分 45.678 秒
```

### 注意事項

1. 小時部分是可選的，但為了兼容性，建議總是包含
2. VTT 使用點 (`.`)，SRT 使用逗號 (`,`)
3. 毫秒必須是 3 位數（不足補 0）

---

## 時間調整

### 場景：影片剪輯後調整字幕

剪輯影片 02:00-02:10 後，字幕時間戳需要調整：

#### 原始字幕

```srt
1
00:02:00,000 --> 00:02:03,500
First subtitle

2
00:02:03,500 --> 00:02:07,000
Second subtitle
```

#### 調整後字幕

```srt
1
00:00:00,000 --> 00:00:03,500
First subtitle

2
00:00:03,500 --> 00:00:07,000
Second subtitle
```

#### Python 實現

```python
def adjust_subtitle_time(subtitles, offset_seconds):
    """
    調整字幕時間戳

    Args:
        subtitles: 字幕列表
        offset_seconds: 偏移量（秒），即剪輯起始時間

    Returns:
        調整後的字幕列表
    """
    adjusted = []

    for sub in subtitles:
        adjusted_sub = {
            'start': max(0, sub['start'] - offset_seconds),
            'end': max(0, sub['end'] - offset_seconds),
            'text': sub['text']
        }

        # 僅保留在有效範圍內的字幕
        if adjusted_sub['end'] > 0:
            adjusted.append(adjusted_sub)

    return adjusted
```

---

## 字幕編碼

### 推薦編碼

**UTF-8**（無 BOM）

### 檢查編碼

```bash
file -i subtitle.srt
# 輸出: subtitle.srt: text/plain; charset=utf-8
```

### 轉換編碼

```bash
# GBK → UTF-8
iconv -f GBK -t UTF-8 input.srt > output.srt

# 移除 BOM
sed -i '1s/^\xEF\xBB\xBF//' subtitle.srt
```

---

## 字幕驗證

### 檢查項目

1. **時間戳格式**: 是否符合規範
2. **時間順序**: 起始時間 < 結束時間
3. **重疊檢測**: 相鄰字幕是否重疊
4. **編碼檢查**: 是否 UTF-8
5. **空行檢查**: 字幕間是否有空行分隔

### Python 驗證腳本

```python
def validate_srt(srt_path):
    errors = []

    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分割字幕塊
    blocks = content.strip().split('\n\n')

    prev_end_time = 0

    for i, block in enumerate(blocks):
        lines = block.split('\n')

        if len(lines) < 3:
            errors.append(f"Block {i+1}: Invalid format (< 3 lines)")
            continue

        # 檢查序號
        try:
            seq = int(lines[0])
            if seq != i + 1:
                errors.append(f"Block {i+1}: Invalid sequence number ({seq})")
        except ValueError:
            errors.append(f"Block {i+1}: Invalid sequence number")

        # 檢查時間戳
        timestamp_pattern = r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})'
        match = re.match(timestamp_pattern, lines[1])

        if not match:
            errors.append(f"Block {i+1}: Invalid timestamp format")
            continue

        start_str, end_str = match.groups()
        start_time = time_to_seconds(start_str)
        end_time = time_to_seconds(end_str)

        # 檢查時間邏輯
        if start_time >= end_time:
            errors.append(f"Block {i+1}: Start time >= End time")

        if start_time < prev_end_time:
            errors.append(f"Block {i+1}: Overlaps with previous subtitle")

        prev_end_time = end_time

    return errors
```

---

## 常見問題

### Q: FFmpeg 無法讀取字幕，提示編碼錯誤

A: 確保字幕是 UTF-8 編碼，且沒有 BOM：

```bash
iconv -f GBK -t UTF-8 input.srt > output.srt
sed -i '1s/^\xEF\xBB\xBF//' output.srt
```

### Q: 字幕顯示亂碼

A: 檢查編碼：

```bash
file -i subtitle.srt
# 如果不是 UTF-8，轉換編碼
```

### Q: VTT 字幕在某些播放器無法顯示

A: 嘗試轉換為 SRT 格式，兼容性更好。

### Q: 雙語字幕中文字太擠

A: 增加字體大小和邊距：

```bash
subtitles=sub.srt:force_style='FontSize=28,MarginV=40'
```

---

## 參考鏈接

- [WebVTT 規範](https://www.w3.org/TR/webvtt1/)
- [SRT 格式説明](https://en.wikipedia.org/wiki/SubRip)
- [FFmpeg Subtitles 濾鏡](https://ffmpeg.org/ffmpeg-filters.html#subtitles)
