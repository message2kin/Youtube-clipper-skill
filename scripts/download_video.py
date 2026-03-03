#!/usr/bin/env python3
"""
下載 YouTube 影片和字幕
使用 yt-dlp 下載影片（最高 1080p）和英文字幕
"""

import sys
import json
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("❌ Error: yt-dlp not installed")
    print("Please install: pip install yt-dlp")
    sys.exit(1)

from utils import (
    validate_url,
    sanitize_filename,
    format_file_size,
    get_video_duration_display,
    ensure_directory
)


def download_video(url: str, output_dir: str = None, subs_only: bool = False) -> dict:
    """
    下載 YouTube 影片和字幕

    Args:
        url: YouTube URL
        output_dir: 輸出目錄，默認為當前目錄
        subs_only: 是否僅下載字幕（如果失敗會自動回退到下載影片）

    Returns:
        dict: {
            'video_path': 影片文件路徑,
            'subtitle_path': 字幕文件路徑,
            'title': 影片標題,
            'duration': 影片時長（秒）,
            'file_size': 文件大小（字節）
        }

    Raises:
        ValueError: 無效的 URL
        Exception: 下載失敗
    """
    # 驗證 URL
    if not validate_url(url):
        raise ValueError(f"Invalid YouTube URL: {url}")

    # 設置輸出目錄
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    output_dir = ensure_directory(output_dir)

    print(f"🎬 開始下載影片...")
    print(f"   URL: {url}")
    print(f"   輸出目錄: {output_dir}")

    # 配置 yt-dlp 選項
    ydl_opts = {
        # 影片格式：最高 1080p，優先 mp4
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',

        # 輸出模板：包含影片 ID（避免特殊字符問題）
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),

        # 下載字幕
        'writesubtitles': True,
        'writeautomaticsub': True,  # 自動字幕作為備選
        'subtitleslangs': ['zh-Hant', 'zh-HK', 'yue', 'en'],   # 優先繁體中文/廣東話
        'subtitlesformat': 'vtt',   # VTT 格式

        # 不下載縮略圖
        'writethumbnail': False,

        # 靜默模式（減少輸出）
        'quiet': False,
        'no_warnings': False,

        # 進度鈎子
        'progress_hooks': [_progress_hook],
    }

    # 如果是 subs_only 模式，先檢查字幕是否存在
    should_skip_download = False
    if subs_only:
        print("\n🔍 檢查字幕可用性...")
        check_opts = {
            'list_subtitles': True,
            'quiet': True,
            'no_warnings': True
        }
        try:
            with yt_dlp.YoutubeDL(check_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                # 檢查是否有我們要的字幕
                has_subs = False
                requested_langs = ['zh-Hant', 'zh-HK', 'yue', 'en']
                
                # Check manual subtitles
                if 'subtitles' in info and info['subtitles']:
                    for lang in requested_langs:
                        if lang in info['subtitles']:
                            has_subs = True
                            print(f"   ✅ 找到人工字幕: {lang}")
                            break
                            
                # Check auto subtitles if no manual ones found
                if not has_subs and 'automatic_captions' in info and info['automatic_captions']:
                     # Auto captions usually have 'en', 'en-orig', etc.
                     # We'll accept 'en' from auto captions
                     for lang in ['en', 'zh-Hant', 'zh-HK', 'yue']:
                         if lang in info['automatic_captions']:
                             has_subs = True
                             print(f"   ✅ 找到自動字幕: {lang}")
                             break
                
                if has_subs:
                    print("   ✨ 字幕可用，跳過影片下載")
                    ydl_opts['skip_download'] = True
                    should_skip_download = True
                else:
                    print("   ⚠️ 未找到有效字幕，將下載影片用於後續轉錄")
                    # 不設置 skip_download，繼續下載影片
        except Exception as e:
             print(f"   ⚠️ 檢查字幕失敗: {e}，將嘗試常規下載")


    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 提取信息
            print("\n📊 獲取影片信息...")
            info = ydl.extract_info(url, download=False)

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            video_id = info.get('id', 'unknown')

            print(f"   標題: {title}")
            print(f"   時長: {get_video_duration_display(duration)}")
            print(f"   影片ID: {video_id}")

            # 下載影片
            print(f"\n📥 開始下載...")
            info = ydl.extract_info(url, download=True)

            # 獲取下載的文件路徑
            video_filename = ydl.prepare_filename(info)
            video_path = Path(video_filename)

            # 查找字幕文件
            subtitle_path = None
            # 優先查找下載的字幕（按偏好順序）
            # yt-dlp 命名格式: <video_path>.<lang>.vtt
            langs = ['zh-Hant', 'zh-HK', 'yue', 'en']
            
            for lang in langs:
                potential_sub = video_path.with_suffix(f".{lang}.vtt")
                if potential_sub.exists():
                    subtitle_path = potential_sub
                    print(f"   找到字幕 ({lang}): {subtitle_path.name}")
                    break
            
            # 如果沒找到特定語言字幕，嘗試通用 vtt
            if not subtitle_path:
                potential_sub = video_path.with_suffix(".vtt")
                if potential_sub.exists():
                    subtitle_path = potential_sub
                    print(f"   找到通用字幕: {subtitle_path.name}")

            # 還沒有找到，嘗試查找自動生成的字幕 (en)
            if not subtitle_path:
                 potential_sub = video_path.with_suffix(".en.vtt")
                 if potential_sub.exists():
                     subtitle_path = potential_sub
                     print(f"   找到自動生成字幕: {subtitle_path.name}")

            # 獲取文件大小
            file_size = video_path.stat().st_size if video_path.exists() else 0

            # 驗證下載結果
            if not should_skip_download and not video_path.exists():
                raise Exception("Video file not found after download")

            if not should_skip_download:
                print(f"\n✅ 影片下載完成: {video_path.name}")
                print(f"   大小: {format_file_size(file_size)}")
            else:
                print(f"\n✅ 影片下載已跳過 (僅下載字幕)")

            if subtitle_path and subtitle_path.exists():
                print(f"✅ 字幕下載完成: {subtitle_path.name}")
            else:
                print(f"⚠️  未找到英文字幕")
                print(f"   提示：某些影片可能沒有字幕或需要自動生成")

            return {
                'video_path': str(video_path) if video_path.exists() else "",
                'subtitle_path': str(subtitle_path) if subtitle_path else None,
                'title': title,
                'duration': duration,
                'file_size': file_size,
                'video_id': video_id
            }

    except Exception as e:
        print(f"\n❌ 下載失敗: {str(e)}")
        raise


def _progress_hook(d):
    """下載進度回調"""
    if d['status'] == 'downloading':
        # 顯示下載進度
        if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes']:
            percent = d['downloaded_bytes'] / d['total_bytes'] * 100
            downloaded = format_file_size(d['downloaded_bytes'])
            total = format_file_size(d['total_bytes'])
            speed = d.get('speed', 0)
            speed_str = format_file_size(speed) + '/s' if speed else 'N/A'

            # 使用 \r 實現進度條覆蓋
            bar_length = 30
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)

            print(f"\r   [{bar}] {percent:.1f}% - {downloaded}/{total} - {speed_str}", end='', flush=True)
        elif 'downloaded_bytes' in d:
            # 無總大小信息時，只顯示已下載
            downloaded = format_file_size(d['downloaded_bytes'])
            speed = d.get('speed', 0)
            speed_str = format_file_size(speed) + '/s' if speed else 'N/A'
            print(f"\r   下載中... {downloaded} - {speed_str}", end='', flush=True)

    elif d['status'] == 'finished':
        print()  # 換行


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("Usage: python download_video.py <youtube_url> [output_dir] [--subs-only]")
        print("\nExample:")
        print("  python download_video.py https://youtube.com/watch?v=Ckt1cj0xjRM")
        print("  python download_video.py https://youtube.com/watch?v=Ckt1cj0xjRM ~/Downloads")
        print("  python download_video.py https://youtube.com/watch?v=Ckt1cj0xjRM ~/Downloads --subs-only")
        sys.exit(1)

    url = sys.argv[1]
    
    # Parse args manually
    output_dir = None
    subs_only = False
    
    for arg in sys.argv[2:]:
        if arg == '--subs-only':
            subs_only = True
        elif not arg.startswith('--'):
            output_dir = arg

    try:
        result = download_video(url, output_dir, subs_only)

        # 輸出 JSON 結果（供其他腳本使用）
        print("\n" + "="*60)
        print("下載結果 (JSON):")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
