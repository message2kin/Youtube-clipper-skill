#!/usr/bin/env python3
"""
燒錄字幕到影片
處理 FFmpeg libass 支持和路徑空格問題
"""

import sys
import os
import shutil
import subprocess
import tempfile
import platform
from pathlib import Path
from typing import Dict, Optional

from utils import format_file_size


def detect_ffmpeg_variant() -> Dict:
    """
    檢測 FFmpeg 版本和 libass 支持

    Returns:
        Dict: {
            'type': 'full' | 'standard' | 'none',
            'path': FFmpeg 可執行文件路徑,
            'has_libass': 是否支持 libass
        }
    """
    print("🔍 檢測 FFmpeg 環境...")

    # 優先檢查 ffmpeg-full（macOS）
    if platform.system() == 'Darwin':
        # Apple Silicon
        full_path_arm = '/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg'
        # Intel
        full_path_intel = '/usr/local/opt/ffmpeg-full/bin/ffmpeg'

        for full_path in [full_path_arm, full_path_intel]:
            if Path(full_path).exists():
                has_libass = check_libass_support(full_path)
                print(f"   找到 ffmpeg-full: {full_path}")
                print(f"   libass 支持: {'✅ 是' if has_libass else '❌ 否'}")
                return {
                    'type': 'full',
                    'path': full_path,
                    'has_libass': has_libass
                }

    # 檢查標準 FFmpeg
    standard_path = shutil.which('ffmpeg')
    if standard_path:
        has_libass = check_libass_support(standard_path)
        variant_type = 'full' if has_libass else 'standard'
        print(f"   找到 FFmpeg: {standard_path}")
        print(f"   類型: {variant_type}")
        print(f"   libass 支持: {'✅ 是' if has_libass else '❌ 否'}")
        return {
            'type': variant_type,
            'path': standard_path,
            'has_libass': has_libass
        }

    # 未找到 FFmpeg
    print("   ❌ 未找到 FFmpeg")
    return {
        'type': 'none',
        'path': None,
        'has_libass': False
    }


def check_libass_support(ffmpeg_path: str) -> bool:
    """
    檢查 FFmpeg 是否支持 libass（字幕燒錄必需）

    Args:
        ffmpeg_path: FFmpeg 可執行文件路徑

    Returns:
        bool: 是否支持 libass
    """
    try:
        # 檢查是否有 subtitles 濾鏡
        result = subprocess.run(
            [ffmpeg_path, '-filters'],
            capture_output=True,
            text=True,
            timeout=5
        )

        # 查找 subtitles 濾鏡
        return 'subtitles' in result.stdout.lower()

    except Exception:
        return False


def install_ffmpeg_full_guide():
    """
    顯示安裝 ffmpeg-full 的指南
    """
    print("\n" + "="*60)
    print("⚠️  需要安裝 ffmpeg-full 才能燒錄字幕")
    print("="*60)

    if platform.system() == 'Darwin':
        print("\nmacOS 安裝方法:")
        print("  brew install ffmpeg-full")
        print("\n安裝後，FFmpeg 路徑:")
        print("  /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg  (Apple Silicon)")
        print("  /usr/local/opt/ffmpeg-full/bin/ffmpeg     (Intel)")
    else:
        print("\n其他系統:")
        print("  請從源碼編譯 FFmpeg，確保包含 libass 支持")
        print("  參考: https://trac.ffmpeg.org/wiki/CompilationGuide")

    print("\n驗證安裝:")
    print("  ffmpeg -filters 2>&1 | grep subtitles")
    print("="*60)


def burn_subtitles(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    ffmpeg_path: str = None,
    font_size: int = 24,
    margin_v: int = 30,
    bold: int = 0,
    outline: int = 1,
    shadow: int = 0,
    color: str = '&HFFFFFF'
) -> str:
    """
    燒錄字幕到影片（使用臨時目錄解決路徑空格問題）

    Args:
        video_path: 輸入影片路徑
        subtitle_path: 字幕文件路徑（SRT 格式）
        output_path: 輸出影片路徑
        ffmpeg_path: FFmpeg 可執行文件路徑（可選）
        font_size: 字體大小
        margin_v: 底部邊距
        bold: 是否加粗 (0/1)
        outline: 描邊寬度
        shadow: 陰影深度
        color: 字體顏色 (ASS hex format, e.g. &H00FFFF for yellow, &HFFFFFF for white)

    Returns:
        str: 輸出影片路徑

    Raises:
        FileNotFoundError: 輸入文件不存在
        RuntimeError: FFmpeg 執行失敗
    """
    video_path = Path(video_path)
    subtitle_path = Path(subtitle_path)
    output_path = Path(output_path)

    # 驗證輸入文件
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not subtitle_path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")

    # 檢測 FFmpeg
    if ffmpeg_path is None:
        ffmpeg_info = detect_ffmpeg_variant()

        if ffmpeg_info['type'] == 'none':
            install_ffmpeg_full_guide()
            raise RuntimeError("FFmpeg not found")

        if not ffmpeg_info['has_libass']:
            install_ffmpeg_full_guide()
            raise RuntimeError("FFmpeg does not support libass (subtitles filter)")

        ffmpeg_path = ffmpeg_info['path']

    print(f"\n🎬 燒錄字幕到影片...")
    print(f"   影片: {video_path.name}")
    print(f"   字幕: {subtitle_path.name}")
    print(f"   輸出: {output_path.name}")
    print(f"   FFmpeg: {ffmpeg_path}")

    # 創建臨時目錄（解決路徑空格問題）
    temp_dir = tempfile.mkdtemp(prefix='youtube_clipper_')
    print(f"   使用臨時目錄: {temp_dir}")

    try:
        # 複製文件到臨時目錄（路徑無空格）
        temp_video = os.path.join(temp_dir, 'video.mp4')
        temp_subtitle = os.path.join(temp_dir, 'subtitle.srt')
        temp_output = os.path.join(temp_dir, 'output.mp4')

        print(f"   複製文件到臨時目錄...")
        shutil.copy(video_path, temp_video)
        shutil.copy(subtitle_path, temp_subtitle)

        # 構建 FFmpeg 命令
        # 構建 FFmpeg 命令
        # 使用 subtitles 濾鏡燒錄字幕
        # force_style uses ASS style format
        # PrimaryColour is in &HAABBGGRR format (Hex). Yellow in RGB is FFFF00, so in BBGGRR it is 00FFFF.
        style_opts = [
            f"FontSize={font_size}",
            f"MarginV={margin_v}",
            f"Bold={bold}",
            f"Outline={outline}",
            f"Shadow={shadow}",
            f"PrimaryColour={color}"
        ]
        subtitle_filter = f"subtitles={temp_subtitle}:force_style='{','.join(style_opts)}'"

        cmd = [
            ffmpeg_path,
            '-i', temp_video,
            '-vf', subtitle_filter,
            '-c:a', 'copy',  # 音頻直接複製，不重新編碼
            '-y',  # 覆蓋輸出文件
            temp_output
        ]

        print(f"   執行 FFmpeg...")
        print(f"   命令: {' '.join(cmd)}")

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
        if not Path(temp_output).exists():
            raise RuntimeError("Output file not created")

        # 移動輸出文件到目標位置
        print(f"   移動輸出文件...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(temp_output, output_path)

        # 獲取文件大小
        output_size = output_path.stat().st_size
        print(f"✅ 字幕燒錄完成")
        print(f"   輸出文件: {output_path}")
        print(f"   文件大小: {format_file_size(output_size)}")

        return str(output_path)

    finally:
        # 清理臨時目錄
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"   清理臨時目錄")
        except Exception:
            pass


def main():
    """命令行入口"""
    # Parse args manually
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    
    if len(args) < 3:
        print("Usage: python burn_subtitles.py <video> <subtitle> <output> [font_size] [margin_v] [--shorts]")
        print("\nArguments:")
        print("  video      - 輸入影片文件路徑")
        print("  subtitle   - 字幕文件路徑（SRT 格式）")
        print("  output     - 輸出影片文件路徑")
        print("  font_size  - 字體大小，默認 24")
        print("  margin_v   - 底部邊距，默認 30")
        print("  --shorts   - (可選) 啓用 Shorts 模式 (大字體/高位置)")
        print("\nExample:")
        print("  python burn_subtitles.py input.mp4 subtitle.srt output.mp4")
        print("  python burn_subtitles.py input.mp4 subtitle.srt output.mp4 --shorts")
        sys.exit(1)

    try:
        is_shorts = '--shorts' in sys.argv
        
        video_path = args[0]
        subtitle_path = args[1]
        output_path = args[2]
        
        # Default settings
        font_size = 24
        margin_v = 30
        bold = 0
        outline = 1
        shadow = 0
        color = '&HFFFFFF' # White
        
        # Override if user provided explicitly
        if len(args) > 3:
            font_size = int(args[3])
        if len(args) > 4:
            margin_v = int(args[4])
            
        # Shorts mode overrides (unless user provided explicit args? No, let's say shorts flag changes defaults)
        if is_shorts:
            # If user didn't explicitly provide font_size/margin, use Shorts defaults
            if len(args) <= 3:
                font_size = 40  # Larger for shorts
            if len(args) <= 4:
                margin_v = 500  # Higher up (center-ish)
            
            bold = 1
            outline = 3
            shadow = 1
            color = '&H00FFFF' # Yellow

        result_path = burn_subtitles(
            video_path,
            subtitle_path,
            output_path,
            font_size=font_size,
            margin_v=margin_v,
            bold=bold,
            outline=outline,
            shadow=shadow,
            color=color
        )

        print(f"\n✨ 完成！輸出文件: {result_path}")

    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
