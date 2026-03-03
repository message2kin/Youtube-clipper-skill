#!/usr/bin/env python3
"""
【Shorts 專用】分析字幕並生成短片片段
解析 VTT 字幕文件，專為 <60s 短片優化，
側重於尋找富有衝擊力、金句密集的高能片段。
"""

import sys
import re
import json
from pathlib import Path
from typing import List, Dict

from utils import (
    time_to_seconds,
    seconds_to_time,
    get_video_duration_display
)


def parse_vtt(vtt_path: str) -> List[Dict]:
    """
    解析 VTT 字幕文件 (複用 analyze_subtitles.py 邏輯)
    """
    vtt_path = Path(vtt_path)

    if not vtt_path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {vtt_path}")

    print(f"📊 [Shorts Mode] 解析字幕文件: {vtt_path.name}")

    subtitles = []

    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 移除 WEBVTT 頭部和樣式信息
    content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
    content = re.sub(r'STYLE.*?-->', '', content, flags=re.DOTALL)

    # 分割字幕塊
    blocks = content.strip().split('\n\n')

    for block in blocks:
        lines = block.strip().split('\n')

        if len(lines) < 2:
            continue

        # 查找時間戳行
        timestamp_line = None
        text_lines = []

        for line in lines:
            if '-->' in line:
                timestamp_line = line
            elif line and not line.isdigit():
                text_lines.append(line)

        if not timestamp_line or not text_lines:
            continue

        # 解析時間戳
        try:
            timestamp_line = re.sub(r'align:.*|position:.*', '', timestamp_line).strip()

            times = timestamp_line.split('-->')
            start = time_to_seconds(times[0].strip())
            end = time_to_seconds(times[1].strip())
            text = ' '.join(text_lines).strip()
            text = re.sub(r'<[^>]+>', '', text) # 清理 HTML

            if text:
                subtitles.append({
                    'start': start,
                    'end': end,
                    'text': text
                })

        except Exception:
            continue

    print(f"   找到 {len(subtitles)} 條字幕")
    return subtitles


def prepare_shorts_analysis_data(subtitles: List[Dict]) -> Dict:
    """
    準備 Shorts 專屬分析數據
    """
    if not subtitles:
        raise ValueError("No subtitles to analyze")

    print(f"\n📝 準備 Shorts 分析數據 (目標 < 60s)...")

    full_text_lines = []
    for sub in subtitles:
        time_str = seconds_to_time(sub['start'], include_hours=True, use_comma=False)
        full_text_lines.append(f"[{time_str}] {sub['text']}")

    full_text = '\n'.join(full_text_lines)
    total_duration = subtitles[-1]['end']

    # Shorts 目標時長通常為 15-60 秒
    target_duration = 60 

    return {
        'subtitle_text': full_text,
        'total_duration': total_duration,
        'subtitle_count': len(subtitles),
        'target_chapter_duration': target_duration,
        'subtitles_raw': subtitles
    }


def save_analysis_data(data: Dict, output_path: str):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ 分析數據已保存: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_shorts.py <vtt_file> [output_json]")
        sys.exit(1)

    vtt_file = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        subtitles = parse_vtt(vtt_file)
        if not subtitles:
            print("❌ 未找到有效字幕")
            sys.exit(1)

        analysis_data = prepare_shorts_analysis_data(subtitles)

        # 輸出提示給 Claude
        print("\n" + "="*60)
        print("Shorts 分析模式 - 字幕文本預覽:")
        print("="*60)
        lines = analysis_data['subtitle_text'].split('\n')
        print('\n'.join(lines[:50]))
        if len(lines) > 50:
            print(f"\n... (剩餘 {len(lines) - 50} 行)")

        if output_json:
            save_analysis_data(analysis_data, output_json)

        print("\n" + "="*60)
        print("💡 Claude 提示: 請尋找 15-60秒 的高能片段")
        print("   要求: 開頭 3 秒必須有鈎子，結尾有反轉或金句，適合豎屏傳播。")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
