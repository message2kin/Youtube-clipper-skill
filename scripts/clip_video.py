#!/usr/bin/env python3
"""
剪輯影片片段
使用 FFmpeg 精確剪輯影片，保持原始質量
"""

import sys
import shutil
import subprocess
from pathlib import Path
from typing import Union

from utils import (
    time_to_seconds,
    seconds_to_time,
    format_file_size,
    get_video_duration_display
)


def clip_video(
    video_path: str,
    start_time: Union[str, float],
    end_time: Union[str, float],
    output_path: str,
    ffmpeg_path: str = None,
    is_shorts: bool = False
) -> str:
    """
    剪輯影片片段

    Args:
        video_path: 輸入影片路徑
        start_time: 起始時間（秒數或時間字符串，如 "00:01:30"）
        end_time: 結束時間（秒數或時間字符串）
        output_path: 輸出影片路徑
        ffmpeg_path: FFmpeg 可執行文件路徑（可選）
        is_shorts: 是否裁剪為 Shorts (9:16)

    Returns:
        str: 輸出影片路徑

    Raises:
        FileNotFoundError: 輸入文件不存在
        RuntimeError: FFmpeg 執行失敗
    """
    video_path = Path(video_path)
    output_path = Path(output_path)

    # 驗證輸入文件
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # 轉換時間為秒數
    if isinstance(start_time, str):
        start_seconds = time_to_seconds(start_time)
    else:
        start_seconds = float(start_time)

    if isinstance(end_time, str):
        end_seconds = time_to_seconds(end_time)
    else:
        end_seconds = float(end_time)

    # 驗證時間範圍
    if start_seconds >= end_seconds:
        raise ValueError(f"Start time ({start_seconds}s) must be before end time ({end_seconds}s)")

    duration = end_seconds - start_seconds

    # 檢測 FFmpeg
    if ffmpeg_path is None:
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")

    print(f"\n✂️  剪輯影片片段...")
    print(f"   輸入: {video_path.name}")
    print(f"   起始時間: {seconds_to_time(start_seconds)} ({start_seconds}s)")
    print(f"   結束時間: {seconds_to_time(end_seconds)} ({end_seconds}s)")
    print(f"   片段時長: {get_video_duration_display(duration)}")
    print(f"   輸出: {output_path.name}")
    print(f"   模式: {'Shorts (9:16 裁剪)' if is_shorts else '默認 (保持原比例)'}")

    # 創建輸出目錄
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 構建 FFmpeg 命令
    cmd = [
        ffmpeg_path,
        '-y',                        # 覆蓋輸出文件
        '-i', str(video_path),       # 輸入文件
        '-ss', str(start_seconds),   # 起始時間
        '-t', str(duration),         # 持續時間
    ]

    # 影片濾鏡
    filters = []
    
    if is_shorts:
        # 使用 9:16 中心裁剪
        filters.append("crop=ih*(9/16):ih:(iw-ow)/2:0")
    
    if filters:
        cmd.extend(['-vf', ','.join(filters)])

    cmd.extend([
        '-c:v', 'libx264',           # 影片編碼
        '-c:a', 'aac',               # 音頻編碼
        str(output_path)
    ])

    print(f"   執行 FFmpeg...")

    # 執行 FFmpeg
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"\n❌ FFmpeg 執行失敗:")
        print(result.stderr)
        raise RuntimeError(f"FFmpeg failed with return code {result.returncode}")

    # 驗證輸出文件
    if not output_path.exists():
        raise RuntimeError("Output file not created")

    # 獲取文件大小
    output_size = output_path.stat().st_size
    print(f"✅ 剪輯完成")
    print(f"   輸出文件: {output_path}")
    print(f"   文件大小: {format_file_size(output_size)}")

    return str(output_path)


def extract_subtitle_segment(
    subtitles: list,
    start_time: float,
    end_time: float,
    adjust_timestamps: bool = True
) -> list:
    """
    從完整字幕中提取指定時間段的字幕

    Args:
        subtitles: 完整字幕列表（每項包含 {start, end, text}）
        start_time: 起始時間（秒）
        end_time: 結束時間（秒）
        adjust_timestamps: 是否調整時間戳（減去起始時間）

    Returns:
        list: 提取的字幕列表
    """
    segment_subtitles = []

    for sub in subtitles:
        # 字幕在時間範圍內
        if sub['start'] >= start_time and sub['end'] <= end_time:
            if adjust_timestamps:
                # 調整時間戳（相對於片段起始時間）
                adjusted_sub = {
                    'start': sub['start'] - start_time,
                    'end': sub['end'] - start_time,
                    'text': sub['text']
                }
                segment_subtitles.append(adjusted_sub)
            else:
                segment_subtitles.append(sub.copy())

        # 字幕跨越時間範圍邊界（部分重疊）
        elif sub['start'] < end_time and sub['end'] > start_time:
            if adjust_timestamps:
                adjusted_sub = {
                    'start': max(0, sub['start'] - start_time),
                    'end': min(end_time - start_time, sub['end'] - start_time),
                    'text': sub['text']
                }
                segment_subtitles.append(adjusted_sub)
            else:
                segment_subtitles.append(sub.copy())

    return segment_subtitles


def save_subtitles_as_srt(subtitles: list, output_path: str):
    """
    保存字幕為 SRT 格式

    Args:
        subtitles: 字幕列表
        output_path: 輸出文件路徑
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for i, sub in enumerate(subtitles, 1):
            # SRT 序號
            f.write(f"{i}\n")

            # SRT 時間戳（使用逗號分隔毫秒）
            start_time = seconds_to_time(sub['start'], include_hours=True, use_comma=True)
            end_time = seconds_to_time(sub['end'], include_hours=True, use_comma=True)
            f.write(f"{start_time} --> {end_time}\n")

            # 字幕文本
            f.write(f"{sub['text']}\n")

            # 空行分隔
            f.write("\n")

    print(f"✅ 字幕已保存: {output_path}")


def main():
    """命令行入口"""
    # Parse args manually to handle flags
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    
    if len(args) < 4:
        print("Usage: python clip_video.py <video> <start_time> <end_time> <output> [--shorts]")
        print("\nArguments:")
        print("  video      - 輸入影片文件路徑")
        print("  start_time - 起始時間（秒數或時間字符串，如 00:01:30）")
        print("  end_time   - 結束時間（秒數或時間字符串）")
        print("  output     - 輸出影片文件路徑")
        print("  --shorts   - (可選) 啓用 Shorts 模式 (9:16 裁剪)")
        print("\nExample:")
        print("  python clip_video.py input.mp4 0 195 output.mp4")
        print("  python clip_video.py input.mp4 00:00:00 00:03:15 output.mp4 --shorts")
        sys.exit(1)

    try:
        is_shorts = '--shorts' in sys.argv
        
        video_path = args[0]
        start_time = args[1]
        end_time = args[2]
        output_path = args[3]

        result_path = clip_video(video_path, start_time, end_time, output_path, is_shorts=is_shorts)
        print(f"\n✨ 完成！輸出文件: {result_path}")

    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
