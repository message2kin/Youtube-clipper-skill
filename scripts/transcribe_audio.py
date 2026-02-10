#!/usr/bin/env python3
"""
Audio Transcription using OpenAI Whisper
Extracts audio from video and generates VTT subtitles
"""

import sys
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from utils import format_file_size, seconds_to_time

try:
    import whisper
except ImportError:
    print("❌ Error: openai-whisper not installed")
    print("Please install: pip install openai-whisper")
    sys.exit(1)


def extract_audio(video_path: str, output_audio_path: str) -> str:
    """
    Extract audio from video using FFmpeg
    """
    print(f"   Extracting audio from {Path(video_path).name}...")
    
    cmd = [
        'ffmpeg',
        '-y',
        '-i', video_path,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        output_audio_path
    ]
    
    # Run quietly unless error
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr.decode()}")
        
    return output_audio_path


def format_timestamp(seconds: float) -> str:
    """
    Format timestamp for VTT (HH:MM:SS.mmm)
    """
    return seconds_to_time(seconds, include_hours=True, use_comma=False)


def create_vtt(segments: list, output_path: str):
    """
    Create VTT file from Whisper segments
    """
    print(f"   Writing VTT file to {Path(output_path).name}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        
        for segment in segments:
            start = format_timestamp(segment['start'])
            end = format_timestamp(segment['end'])
            text = segment['text'].strip()
            
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")


def transcribe_video(video_path: str, model_size: str = "base", output_dir: str = None) -> str:
    """
    Transcribe video audio to VTT subtitle
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
        
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        vtt_path = output_dir / f"{video_path.stem}.vtt"
    else:
        vtt_path = video_path.with_suffix('.vtt')
        
    print(f"🎤 Starting transcription...")
    print(f"   Video: {video_path.name}")
    print(f"   Model: {model_size}")
    
    # Create temp directory for audio extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = os.path.join(temp_dir, "audio.wav")
        
        try:
            # 1. Extract Audio
            extract_audio(str(video_path), audio_path)
            
            # 2. Load Model
            print(f"   Loading Whisper model ({model_size})...")
            model = whisper.load_model(model_size)
            
            # 3. Transcribe
            print(f"   Transcribing audio (this may take a while)...")
            result = model.transcribe(audio_path, verbose=False)
            
            # 4. Save VTT
            create_vtt(result['segments'], str(vtt_path))
            
            print(f"✅ Transcription complete")
            print(f"   Output: {vtt_path}")
            
            return str(vtt_path)
            
        except Exception as e:
            print(f"\n❌ Transcription failed: {str(e)}")
            raise


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_audio.py <video_path> [model_size]")
        print("Models: tiny, base, small, medium, large")
        sys.exit(1)
        
    video_path = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else "base"
    
    try:
        transcribe_video(video_path, model_size)
    except Exception as e:
        sys.exit(1)


if __name__ == "__main__":
    main()
