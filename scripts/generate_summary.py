#!/usr/bin/env python3
"""
生成總結文案
基於章節信息生成適合社交媒體的文案
"""

import sys
import json
from pathlib import Path
from typing import Dict


def generate_summary(
    chapter_info: Dict,
    output_path: str = None
) -> str:
    """
    生成總結文案

    注意：此函數需要在 Claude Code Skill 環境中調用
    Claude 會自動處理文案生成邏輯

    Args:
        chapter_info: 章節信息，包含：
            - title: 章節標題
            - time_range: 時間範圍
            - summary: 核心摘要
            - keywords: 關鍵詞列表
        output_path: 輸出文件路徑（可選）

    Returns:
        str: 生成的文案
    """
    print(f"\n📝 生成總結文案...")
    print(f"   章節: {chapter_info.get('title', 'Unknown')}")

    # 輸出章節信息（供 Claude 分析）
    print("\n" + "="*60)
    print("章節信息（JSON 格式）:")
    print("="*60)
    print(json.dumps(chapter_info, indent=2, ensure_ascii=False))

    print("\n" + "="*60)
    print("文案生成要求:")
    print("="*60)
    print("""
請基於上述章節信息生成適合社交媒體的文案。

文案要求：
1. 吸引人的標題（10-20字）
2. 核心觀點（3-5個要點，每個1-2句話）
3. 適合平台：
   - 小紅書：口語化，有emoji，1000字以內
   - 抖音：精煉，突出金句，300字以內
   - 微信公眾號：詳細，結構清晰，不限字數

輸出格式（Markdown）：

# [標題]

## 核心觀點

1. 觀點1
2. 觀點2
3. 觀點3

## 適合平台

### 小紅書版本（1000字）
[文案內容]

### 抖音版本（300字）
[文案內容]

### 微信公眾號版本
[文案內容]

## 標籤

#標籤1 #標籤2 #標籤3
""")

    # 生成基礎文案（佔位符）
    summary_template = f"""# {chapter_info.get('title', '未命名章節')}

## 章節信息

- 時間範圍: {chapter_info.get('time_range', 'N/A')}
- 核心摘要: {chapter_info.get('summary', 'N/A')}
- 關鍵詞: {', '.join(chapter_info.get('keywords', []))}

## 核心觀點

[待生成 - Claude 會在 Skill 執行時自動填充]

## 適合平台

### 小紅書版本

[待生成]

### 抖音版本

[待生成]

### 微信公眾號版本

[待生成]

## 標籤

{' '.join(['#' + kw for kw in chapter_info.get('keywords', [])])}

---

生成時間: {chapter_info.get('generated_at', 'N/A')}
"""

    # 保存到文件（如果指定）
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary_template)

        print(f"✅ 文案已保存: {output_path}")

    return summary_template


def load_chapter_info(json_path: str) -> Dict:
    """
    從 JSON 文件加載章節信息

    Args:
        json_path: JSON 文件路徑

    Returns:
        Dict: 章節信息
    """
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    print(f"📂 加載章節信息: {json_path.name}")

    with open(json_path, 'r', encoding='utf-8') as f:
        chapter_info = json.load(f)

    return chapter_info


def create_chapter_info(
    title: str,
    time_range: str,
    summary: str,
    keywords: list
) -> Dict:
    """
    創建章節信息字典

    Args:
        title: 章節標題
        time_range: 時間範圍（如 "00:00 - 03:15"）
        summary: 核心摘要
        keywords: 關鍵詞列表

    Returns:
        Dict: 章節信息
    """
    from datetime import datetime

    return {
        'title': title,
        'time_range': time_range,
        'summary': summary,
        'keywords': keywords,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("Usage: python generate_summary.py <chapter_info_json> [output_file]")
        print("   or: python generate_summary.py --create <title> <time_range> <summary> <keywords> [output_file]")
        print("\nArguments:")
        print("  chapter_info_json - 章節信息 JSON 文件路徑")
        print("  output_file       - 輸出文件路徑（可選，默認為 summary.md）")
        print("\nCreate mode arguments:")
        print("  --create    - 創建模式")
        print("  title       - 章節標題")
        print("  time_range  - 時間範圍（如 '00:00 - 03:15'）")
        print("  summary     - 核心摘要")
        print("  keywords    - 關鍵詞（逗號分隔）")
        print("\nExample:")
        print("  python generate_summary.py chapter.json")
        print("  python generate_summary.py chapter.json summary.md")
        print("  python generate_summary.py --create 'AGI指數曲線' '00:00-03:15' '核心摘要' 'AGI,指數增長,Claude' summary.md")
        sys.exit(1)

    try:
        if sys.argv[1] == '--create':
            # 創建模式
            if len(sys.argv) < 6:
                print("❌ 創建模式需要提供: title, time_range, summary, keywords")
                sys.exit(1)

            title = sys.argv[2]
            time_range = sys.argv[3]
            summary = sys.argv[4]
            keywords = sys.argv[5].split(',')
            output_file = sys.argv[6] if len(sys.argv) > 6 else 'summary.md'

            chapter_info = create_chapter_info(title, time_range, summary, keywords)

        else:
            # JSON 模式
            json_file = sys.argv[1]
            output_file = sys.argv[2] if len(sys.argv) > 2 else 'summary.md'

            chapter_info = load_chapter_info(json_file)

        # 生成文案
        summary = generate_summary(chapter_info, output_file)

        print("\n" + "="*60)
        print("生成的文案預覽:")
        print("="*60)
        print(summary)

        print("\n⚠️  提示：此腳本需要在 Claude Code Skill 中運行")
        print("   Claude 會自動生成詳細的文案內容")
        print("   當前僅輸出模板")

    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
