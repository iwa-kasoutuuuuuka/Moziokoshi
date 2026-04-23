import os
import sys
import zipfile
import shutil
import requests
from pathlib import Path
from tqdm import tqdm

FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def download_file(url, dest_path, desc="Downloading"):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024
    
    with open(dest_path, "wb") as f, tqdm(
            desc=desc,
            total=total_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(block_size):
            size = f.write(data)
            bar.update(size)

def get_ffmpeg_path():
    app_dir = get_app_dir()
    ffmpeg_dir = os.path.join(app_dir, "ffmpeg")
    ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")
    return ffmpeg_exe

def setup_ffmpeg():
    app_dir = get_app_dir()
    ffmpeg_dir = os.path.join(app_dir, "ffmpeg")
    ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")
    
    if os.path.exists(ffmpeg_exe):
        print("FFmpeg implies already installed.")
        return True
        
    print("FFmpeg not found. Downloading...")
    os.makedirs(ffmpeg_dir, exist_ok=True)
    zip_path = os.path.join(app_dir, "ffmpeg.zip")
    
    try:
        download_file(FFMPEG_URL, zip_path, desc="FFmpeg")
        
        print("Extracting FFmpeg...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # We want to extract only the bins (ffmpeg.exe, ffprobe.exe) to /ffmpeg/
            # Zip structure is usually ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe
            for member in zip_ref.namelist():
                if member.endswith("bin/ffmpeg.exe") or member.endswith("bin/ffprobe.exe"):
                    filename = os.path.basename(member)
                    source = zip_ref.open(member)
                    target_path = os.path.join(ffmpeg_dir, filename)
                    with open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)
        
        # Cleanup
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
        print("FFmpeg setup complete.")
        return True
    except Exception as e:
        print(f"Failed to download FFmpeg: {e}")
        return False

def setup_model(model_name="large-v3-turbo"):
    # This function uses faster-whisper's builtin download function
    try:
        from faster_whisper import download_model
        app_dir = get_app_dir()
        models_dir = os.path.join(app_dir, "models")
        os.makedirs(models_dir, exist_ok=True)
        
        print(f"Downloading model {model_name} to {models_dir}...")
        download_model(model_name, output_dir=os.path.join(models_dir, model_name))
        print("Model downloaded successfully.")
        return True
    except Exception as e:
        print(f"Failed to download model: {e}")
        return False

if __name__ == "__main__":
    print("Running initial setup...")
    setup_ffmpeg()
    setup_model("large-v3-turbo")
    print("Initial setup complete.")
