import os
import subprocess
import math
import numpy as np
from utils.logger import logger

def get_audio_duration(file_path, ffmpeg_path="ffmpeg"):
    """使用するffprobeでメディアの長さを取得します"""
    if ffmpeg_path.lower().endswith('ffmpeg.exe'):
        ffprobe_path = ffmpeg_path[:-10] + 'ffprobe.exe'
    elif ffmpeg_path.lower().endswith('ffmpeg'):
        if os.path.isfile(ffmpeg_path):
            ffprobe_path = ffmpeg_path[:-6] + 'ffprobe'
        else:
            ffprobe_path = 'ffprobe'
    else:
        ffprobe_path = 'ffprobe'

    if not os.path.isfile(ffprobe_path):
        ffprobe_path = 'ffprobe'

    cmd = [
        ffprobe_path, 
        "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Failed to get duration: {e}")
        return 0.0

def load_audio_to_numpy(file_path, ffmpeg_path="ffmpeg", sr=16000):
    """
    FFmpegのパイプを利用して、音声をメモリ上のNumPy配列として直接読み込みます。
    ディスクへの一時書き出しが発生しないため高速です。
    """
    cmd = [
        ffmpeg_path,
        "-v", "quiet",
        "-i", file_path,
        "-f", "s16le", # Signed 16-bit little-endian
        "-acodec", "pcm_s16le",
        "-ar", str(sr),
        "-ac", "1",
        "-" # Output to stdout
    ]
    
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, startupinfo=startupinfo)
        out, _ = process.communicate()
        
        # Convert buffer to float32 (Whisper expects normalized float32 or int16)
        # faster-whisper can take float32 array in range [-1, 1]
        audio = np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768.0
        return audio
    except Exception as e:
        logger.error(f"Failed to load audio in-memory: {e}")
        return None

def get_audio_chunks(file_path, ffmpeg_path, chunk_duration_sec=1200):
    """
    メモリ上で音声を分割し、NumPy配列のリストを返します。
    """
    logger.info(f"Loading {file_path} into memory...")
    audio = load_audio_to_numpy(file_path, ffmpeg_path)
    if audio is None:
        return []
        
    sr = 16000
    samples_per_chunk = chunk_duration_sec * sr
    total_samples = len(audio)
    
    chunks = []
    num_chunks = math.ceil(total_samples / samples_per_chunk)
    
    for i in range(num_chunks):
        start = i * samples_per_chunk
        end = min((i + 1) * samples_per_chunk, total_samples)
        chunk_data = audio[start:end]
        
        chunks.append({
            "data": chunk_data,
            "start_time": start / sr
        })
        
    logger.info(f"Audio loaded and split into {num_chunks} in-memory chunks.")
    return chunks

def cleanup_chunks(chunks):
    """メモリ内処理ではディスククリーンアップは不要ですが、明示的に参照を切ります"""
    chunks.clear()
