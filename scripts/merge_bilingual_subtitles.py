#!/usr/bin/env python3
"""
合併英文和中文字幕為雙語 SRT 文件
"""

import sys
import re

def parse_srt_file(file_path):
    """解析 SRT 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分割字幕塊
    blocks = content.strip().split('\n\n')
    subtitles = []

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            index = lines[0]
            time = lines[1]
            text = '\n'.join(lines[2:])
            subtitles.append({
                'index': index,
                'time': time,
                'text': text
            })

    return subtitles

def merge_bilingual_subtitles(english_file, chinese_file, output_file):
    """合併英文和中文字幕"""
    print(f"📝 合併雙語字幕...")
    print(f"   英文字幕: {english_file}")
    print(f"   中文字幕: {chinese_file}")

    # 解析兩個字幕文件
    english_subs = parse_srt_file(english_file)
    chinese_subs = parse_srt_file(chinese_file)

    if len(english_subs) != len(chinese_subs):
        print(f"⚠️  警告: 英文字幕 ({len(english_subs)} 條) 和中文字幕 ({len(chinese_subs)} 條) 數量不匹配")

    # 合併字幕
    bilingual_subs = []
    for i in range(min(len(english_subs), len(chinese_subs))):
        bilingual_subs.append({
            'index': english_subs[i]['index'],
            'time': english_subs[i]['time'],
            'text': f"{english_subs[i]['text']}\n{chinese_subs[i]['text']}"
        })

    # 寫入雙語字幕文件
    with open(output_file, 'w', encoding='utf-8') as f:
        for sub in bilingual_subs:
            f.write(f"{sub['index']}\n")
            f.write(f"{sub['time']}\n")
            f.write(f"{sub['text']}\n")
            f.write("\n")

    print(f"✅ 雙語字幕生成完成")
    print(f"   輸出文件: {output_file}")
    print(f"   字幕條數: {len(bilingual_subs)}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("用法: python merge_bilingual_subtitles.py <english_srt> <chinese_srt> <output_srt>")
        sys.exit(1)

    english_file = sys.argv[1]
    chinese_file = sys.argv[2]
    output_file = sys.argv[3]

    merge_bilingual_subtitles(english_file, chinese_file, output_file)
