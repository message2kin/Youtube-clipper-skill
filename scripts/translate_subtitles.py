#!/usr/bin/env python3
"""
翻譯字幕
批量翻譯優化：每批 20 條字幕一起翻譯，節省 95% API 調用
"""

import sys
import json
from pathlib import Path
from typing import List, Dict

from utils import seconds_to_time


def translate_subtitles_batch(
    subtitles: List[Dict],
    batch_size: int = 20,
    target_lang: str = "中文"
) -> List[Dict]:
    """
    批量翻譯字幕

    注意：此函數需要在 Claude Code Skill 環境中調用
    Claude 會自動處理翻譯邏輯

    Args:
        subtitles: 字幕列表（每項包含 {start, end, text}）
        batch_size: 每批翻譯的字幕數量
        target_lang: 目標語言

    Returns:
        List[Dict]: 翻譯後的字幕列表，每項包含 {start, end, text, translation}
    """
    print(f"\n🌐 開始翻譯字幕...")
    print(f"   總條數: {len(subtitles)}")
    print(f"   批量大小: {batch_size}")
    print(f"   目標語言: {target_lang}")

    # 準備批量翻譯數據
    batches = []
    for i in range(0, len(subtitles), batch_size):
        batch = subtitles[i:i + batch_size]
        batches.append(batch)

    print(f"   分為 {len(batches)} 批")

    # 輸出待翻譯文本（供 Claude 處理）
    print("\n" + "="*60)
    print("待翻譯字幕（JSON 格式）:")
    print("="*60)
    print(json.dumps(subtitles, indent=2, ensure_ascii=False))

    print("\n" + "="*60)
    print("翻譯要求:")
    print("="*60)
    print(f"""
請將上述字幕翻譯為{target_lang}。

翻譯要求：
1. 保持技術術語的準確性
2. 口語化表達（適合短片）
3. 簡潔流暢（避免冗長）
4. 保持原意，不要添加或刪減內容

輸出格式（JSON）：
[
  {{"start": 0.0, "end": 3.5, "text": "原文", "translation": "譯文"}},
  {{"start": 3.5, "end": 7.2, "text": "原文", "translation": "譯文"}},
  ...
]

請分批翻譯，每批 {batch_size} 條。
""")

    # 注意：實際翻譯由 Claude 在 Skill 執行時完成
    # 這個腳本只是準備數據和提供接口
    # 返回佔位符數據
    translated_subtitles = []
    for sub in subtitles:
        translated_subtitles.append({
            'start': sub['start'],
            'end': sub['end'],
            'text': sub['text'],
            'translation': '[待翻譯]'  # Claude 會在運行時替換
        })

    return translated_subtitles


def create_bilingual_subtitles(
    subtitles: List[Dict],
    output_path: str,
    english_first: bool = True
) -> str:
    """
    創建雙語字幕文件（SRT 格式）

    Args:
        subtitles: 字幕列表（包含 text 和 translation）
        output_path: 輸出文件路徑
        english_first: 英文在上（True）或中文在上（False）

    Returns:
        str: 輸出文件路徑
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n📝 生成雙語字幕文件...")
    print(f"   輸出: {output_path}")
    print(f"   順序: {'英文在上，中文在下' if english_first else '中文在上，英文在下'}")

    with open(output_path, 'w', encoding='utf-8') as f:
        for i, sub in enumerate(subtitles, 1):
            # SRT 序號
            f.write(f"{i}\n")

            # SRT 時間戳
            start_time = seconds_to_time(sub['start'], include_hours=True, use_comma=True)
            end_time = seconds_to_time(sub['end'], include_hours=True, use_comma=True)
            f.write(f"{start_time} --> {end_time}\n")

            # 雙語文本
            english = sub['text']
            chinese = sub.get('translation', '[未翻譯]')

            if english_first:
                f.write(f"{english}\n{chinese}\n")
            else:
                f.write(f"{chinese}\n{english}\n")

            # 空行分隔
            f.write("\n")

    print(f"✅ 雙語字幕已保存: {output_path}")
    return str(output_path)


def load_subtitles_from_srt(srt_path: str) -> List[Dict]:
    """
    從 SRT 文件加載字幕

    Args:
        srt_path: SRT 文件路徑

    Returns:
        List[Dict]: 字幕列表
    """
    try:
        import pysrt
    except ImportError:
        print("❌ Error: pysrt not installed")
        print("Please install: pip install pysrt")
        sys.exit(1)

    srt_path = Path(srt_path)
    if not srt_path.exists():
        raise FileNotFoundError(f"SRT file not found: {srt_path}")

    print(f"📂 加載 SRT 字幕: {srt_path.name}")

    subs = pysrt.open(srt_path)
    subtitles = []

    for sub in subs:
        # 轉換時間為秒數
        start = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000
        end = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000

        subtitles.append({
            'start': start,
            'end': end,
            'text': sub.text.replace('\n', ' ')  # 合併多行
        })

    print(f"   找到 {len(subtitles)} 條字幕")
    return subtitles


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("Usage: python translate_subtitles.py <subtitle_file> [output_file] [batch_size]")
        print("\nArguments:")
        print("  subtitle_file - 字幕文件路徑（SRT 格式）")
        print("  output_file   - 輸出文件路徑（可選，默認為 <原文件名>_bilingual.srt）")
        print("  batch_size    - 每批翻譯數量（可選，默認 20）")
        print("\nExample:")
        print("  python translate_subtitles.py subtitle.srt")
        print("  python translate_subtitles.py subtitle.srt bilingual.srt")
        print("  python translate_subtitles.py subtitle.srt bilingual.srt 30")
        print("\nNote:")
        print("  此腳本在 Claude Code Skill 中運行時，Claude 會自動處理翻譯")
        print("  獨立運行時，會輸出待翻譯數據供手動處理")
        sys.exit(1)

    subtitle_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    try:
        # 加載字幕
        subtitles = load_subtitles_from_srt(subtitle_file)

        if not subtitles:
            print("❌ 未找到有效字幕")
            sys.exit(1)

        # 翻譯字幕（準備數據）
        translated = translate_subtitles_batch(subtitles, batch_size)

        # 設置輸出路徑
        if output_file is None:
            subtitle_path = Path(subtitle_file)
            output_file = subtitle_path.parent / f"{subtitle_path.stem}_bilingual.srt"

        # 創建雙語字幕
        # 注意：在實際使用中，Claude 會先完成翻譯，然後再調用這個函數
        print("\n⚠️  提示：此腳本需要在 Claude Code Skill 中運行")
        print("   Claude 會自動處理翻譯邏輯")
        print("   當前僅輸出待翻譯數據")

    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
