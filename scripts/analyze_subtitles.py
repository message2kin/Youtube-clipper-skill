#!/usr/bin/env python3
"""
分析字幕並生成章節
解析 VTT 字幕文件，準備數據供 Claude AI 分析
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
    解析 VTT 字幕文件

    Args:
        vtt_path: VTT 文件路徑

    Returns:
        List[Dict]: 字幕列表，每項包含 {start, end, text}

    Example:
        [
            {'start': 0.0, 'end': 3.5, 'text': 'Hello world'},
            {'start': 3.5, 'end': 7.2, 'text': 'This is a test'},
            ...
        ]
    """
    vtt_path = Path(vtt_path)

    if not vtt_path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {vtt_path}")

    print(f"📊 解析字幕文件: {vtt_path.name}")

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
            # 匹配時間戳格式: 00:00:00.000 --> 00:00:03.000
            if '-->' in line:
                timestamp_line = line
            elif line and not line.isdigit():  # 跳過序號
                text_lines.append(line)

        if not timestamp_line or not text_lines:
            continue

        # 解析時間戳
        try:
            # 移除可能的位置信息（如 align:start position:0%）
            timestamp_line = re.sub(r'align:.*|position:.*', '', timestamp_line).strip()

            times = timestamp_line.split('-->')
            start_str = times[0].strip()
            end_str = times[1].strip()

            start = time_to_seconds(start_str)
            end = time_to_seconds(end_str)

            # 合併文本行
            text = ' '.join(text_lines)

            # 清理 HTML 標籤（如果有）
            text = re.sub(r'<[^>]+>', '', text)

            # 清理特殊字符
            text = text.strip()

            if text:
                subtitles.append({
                    'start': start,
                    'end': end,
                    'text': text
                })

        except Exception as e:
            # 跳過無法解析的字幕塊
            continue

    print(f"   找到 {len(subtitles)} 條字幕")

    if subtitles:
        total_duration = subtitles[-1]['end']
        print(f"   總時長: {get_video_duration_display(total_duration)}")

    return subtitles


def prepare_analysis_data(subtitles: List[Dict], target_chapter_duration: int = 180) -> Dict:
    """
    準備數據供 Claude AI 分析

    Args:
        subtitles: 字幕列表
        target_chapter_duration: 目標章節時長（秒），默認 180 秒（3 分鐘）

    Returns:
        Dict: {
            'subtitle_text': 帶時間戳的完整字幕文本,
            'total_duration': 總時長,
            'subtitle_count': 字幕條數,
            'target_chapter_duration': 目標章節時長,
            'estimated_chapters': 預估章節數
        }
    """
    if not subtitles:
        raise ValueError("No subtitles to analyze")

    print(f"\n📝 準備分析數據...")

    # 將字幕合併為帶時間戳的完整文本
    full_text_lines = []

    for sub in subtitles:
        time_str = seconds_to_time(sub['start'], include_hours=True, use_comma=False)
        full_text_lines.append(f"[{time_str}] {sub['text']}")

    full_text = '\n'.join(full_text_lines)

    total_duration = subtitles[-1]['end']
    estimated_chapters = max(1, int(total_duration / target_chapter_duration))

    print(f"   總時長: {get_video_duration_display(total_duration)}")
    print(f"   字幕條數: {len(subtitles)}")
    print(f"   目標章節時長: {target_chapter_duration} 秒 ({target_chapter_duration // 60} 分鐘)")
    print(f"   預估章節數: {estimated_chapters}")

    return {
        'subtitle_text': full_text,
        'total_duration': total_duration,
        'subtitle_count': len(subtitles),
        'target_chapter_duration': target_chapter_duration,
        'estimated_chapters': estimated_chapters,
        'subtitles_raw': subtitles  # 保留原始數據供後續使用
    }


def save_analysis_data(data: Dict, output_path: str):
    """
    保存分析數據到 JSON 文件

    Args:
        data: 分析數據
        output_path: 輸出文件路徑
    """
    output_path = Path(output_path)

    # 創建輸出目錄
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存為 JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 分析數據已保存: {output_path}")


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_subtitles.py <vtt_file> [target_duration] [output_json]")
        print("\nArguments:")
        print("  vtt_file         - VTT 字幕文件路徑")
        print("  target_duration  - 目標章節時長（秒），默認 180")
        print("  output_json      - 輸出 JSON 文件路徑（可選）")
        print("\nExample:")
        print("  python analyze_subtitles.py video.en.vtt")
        print("  python analyze_subtitles.py video.en.vtt 240")
        print("  python analyze_subtitles.py video.en.vtt 240 analysis.json")
        sys.exit(1)

    is_shorts = '--shorts' in sys.argv
    is_analysis_only = '--analysis-only' in sys.argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    
    if len(args) < 1:
        print("Usage: python analyze_subtitles.py <vtt_file> [target_duration] [output_json] [--shorts] [--analysis-only]")
        sys.exit(1)

    vtt_file = args[0]
    
    # Determine default duration
    default_duration = 60 if is_shorts else 180
    
    target_duration = int(args[1]) if len(args) > 1 else default_duration
    output_json = args[2] if len(args) > 2 else None

    try:
        # 解析字幕
        subtitles = parse_vtt(vtt_file)

        if not subtitles:
            print("❌ 未找到有效字幕")
            sys.exit(1)

        # 準備分析數據
        analysis_data = prepare_analysis_data(subtitles, target_duration)

        # 輸出字幕文本（供 Claude 分析）
        print("\n" + "="*60)
        print("字幕文本（前 50 行預覽）:")
        print("="*60)
        lines = analysis_data['subtitle_text'].split('\n')
        preview_lines = lines[:50]
        print('\n'.join(preview_lines))
        if len(lines) > 50:
            print(f"\n... （還有 {len(lines) - 50} 行）")

        # 保存到文件（如果指定）
        if output_json:
            save_analysis_data(analysis_data, output_json)

        # 輸出摘要信息
        print("\n" + "="*60)
        print("分析摘要:")
        print("="*60)
        print(json.dumps({
            'total_duration': analysis_data['total_duration'],
            'total_duration_display': get_video_duration_display(analysis_data['total_duration']),
            'subtitle_count': analysis_data['subtitle_count'],
            'target_chapter_duration': analysis_data['target_chapter_duration'],
            'estimated_chapters': analysis_data['estimated_chapters'],
            'mode': 'Analysis Only' if is_analysis_only else ('Shorts' if is_shorts else 'Standard')
        }, indent=2, ensure_ascii=False))

        hint_msg = "💡 提示：現在可以使用 Claude AI 分析上述字幕文本，生成精細章節"
        shorts_criteria_msg = "   ## 病毒短片 (Viral Shorts) 要求:\n"
        shorts_criteria_msg += "   1. 時長: 15-60秒 (嚴格限制)\n"
        shorts_criteria_msg += "   2. 鈎子 (Hook): 開頭 3 秒必須有視覺/聽覺衝擊或懸念\n"
        shorts_criteria_msg += "   3. 結構: 結尾有反轉、金句或適合循環播放 (Loop)\n"
        shorts_criteria_msg += "   4. 優先: 情緒飽滿、快節奏、信息密度高的片段\n"

        # 1. Header
        if is_analysis_only:
            hint_msg += "\n   請按以下格式輸出分析結果（包含 Standard 章節和 Viral Shorts）:\n"
        elif is_shorts:
            hint_msg += "\n   (Shorts 模式)\n"
        else:
            hint_msg += "\n   請按以下格式輸出章節（Standard 模式）:\n"

        # 2. Standard Section
        if is_analysis_only or not is_shorts:
            if is_analysis_only:
                hint_msg += "   ## 章節 (Standard)\n"
                hint_msg += "   MM:SS <章節標題>\n"
                hint_msg += "   - 摘要: ...\n"
                hint_msg += "   - 關鍵詞: ...\n\n"
            else:
                hint_msg += "   MM:SS <章節標題>\n"
                hint_msg += "   例如:\n"
                hint_msg += "   00:00 黎智英20年重判與香港三條路\n"
                hint_msg += "   03:25 黎智英作為反抗象徵與歷史對比"

        # 3. Shorts Section
        if is_analysis_only or is_shorts:
            if is_analysis_only:
                hint_msg += f"{shorts_criteria_msg}\n"
                hint_msg += "   請按以下格式輸出 Shorts:\n"
                hint_msg += "   - 時間範圍: MM:SS - MM:SS\n"
                hint_msg += "   - 評分: [1-10] (病毒傳播潛力)\n"
                hint_msg += "   - 鈎子 (Hook): ...\n"
                hint_msg += "   - 理由: 為什麼適合 TikTok/Shorts\n"
            else:
                hint_msg += f"{shorts_criteria_msg}"
                hint_msg += "\n   請輸出符合上述要求的高能片段列表。"
        print(f"\n{hint_msg}")

    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
