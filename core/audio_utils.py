import os
import subprocess
import math
from utils.logger import logger

def get_audio_duration(file_path, ffmpeg_path="ffmpeg"):
    """使用するffprobeでメディアの長さを取得します"""
    # Case-insensitive replacement of ffmpeg.exe with ffprobe.exe
    if ffmpeg_path.lower().endswith('ffmpeg.exe'):
        ffprobe_path = ffmpeg_path[:-10] + 'ffprobe.exe'
    elif ffmpeg_path.lower().endswith('ffmpeg'):
        # If it's just 'ffmpeg' or path/to/ffmpeg (without exe)
        # Check if it's a file or directory
        if os.path.isfile(ffmpeg_path):
            ffprobe_path = ffmpeg_path[:-6] + 'ffprobe'
        else:
            ffprobe_path = 'ffprobe'
    else:
        ffprobe_path = 'ffprobe'

    if not os.path.isfile(ffprobe_path):
        logger.debug(f"ffprobe not found at {ffprobe_path}, falling back to system PATH")
        ffprobe_path = 'ffprobe' # Fallback to system PATH

    logger.debug(f"Using ffprobe: {ffprobe_path}")

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
        logger.error(f"Failed to get duration for {file_path} using {ffprobe_path}: {e}")
        return 0.0

def convert_to_wav(input_path, output_path, ffmpeg_path="ffmpeg", start_time=0, duration=None):
    """ffmpegを使用して音声のみ抽出し16kHz/モノラルwavに変換します"""
    # Verify ffmpeg_path is not a directory
    if os.path.isdir(ffmpeg_path):
        logger.error(f"ffmpeg_path is a directory: {ffmpeg_path}. Falling back to 'ffmpeg' in PATH.")
        ffmpeg_path = "ffmpeg"

    cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_path
    ]
    
    if start_time > 0:
        cmd = [ffmpeg_path, "-y", "-ss", str(start_time), "-i", input_path]
        
    if duration is not None:
        cmd.extend(["-t", str(duration)])
        
    cmd.extend([
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_path
    ])
    
    # Hide window on Windows
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, startupinfo=startupinfo)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg conversion failed: {e.stderr.decode('utf-8', errors='ignore')}")
        return False

def get_audio_chunks(file_path, ffmpeg_path, chunk_duration_sec=1200): # 20 minutes
    """
    ファイルを20分ごとに分割し、一時WAVファイルのパスリストとその開始時間を返します。
    """
    logger.info(f"Analyzing {file_path}...")
    total_duration = get_audio_duration(file_path, ffmpeg_path)
    if total_duration == 0:
        return []
        
    chunks = []
    num_chunks = math.ceil(total_duration / chunk_duration_sec)
    
    logger.info(f"Total duration: {total_duration:.2f}s, splitting into {num_chunks} chunks.")
    
    temp_dir = os.path.join(os.path.dirname(file_path), "temp_audio_chunks")
    os.makedirs(temp_dir, exist_ok=True)
    
    base_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    for i in range(num_chunks):
        start_time = i * chunk_duration_sec
        chunk_file = os.path.join(temp_dir, f"{name_without_ext}_chunk_{i}.wav")
        # Ensure we only extract exactly until the end
        dur = min(chunk_duration_sec, total_duration - start_time)
        
        logger.info(f"Extracting chunk {i+1}/{num_chunks} ({start_time}s to {start_time+dur}s)...")
        success = convert_to_wav(file_path, chunk_file, ffmpeg_path, start_time, dur)
        if success:
            chunks.append({
                "path": chunk_file,
                "start_time": start_time
            })
        else:
            logger.error(f"Failed to create chunk {i+1}")
            
    return chunks

def cleanup_chunks(chunks):
    """処理後の一時チャンクを削除します"""
    for chunk in chunks:
        if os.path.exists(chunk["path"]):
            os.remove(chunk["path"])
            
    # Try removing the dir if empty
    if chunks:
        dir_path = os.path.dirname(chunks[0]["path"])
        if os.path.exists(dir_path) and not os.listdir(dir_path):
            os.rmdir(dir_path)
