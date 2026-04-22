import os
import sys
import subprocess
from pathlib import Path

def build():
    print("Starting build process...")
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure dependencies like ffmpeg and models exist first
    ffmpeg_dir = os.path.join(app_dir, 'ffmpeg')
    models_dir = os.path.join(app_dir, 'models')
    filler_dict = os.path.join(app_dir, 'filler_dict.txt')
    
    if not os.path.exists(ffmpeg_dir):
        print("Warning: ffmpeg folder not found. Downloading via core.downloader...")
        from core.downloader import setup_ffmpeg
        setup_ffmpeg()
        
    if not os.path.exists(os.path.join(models_dir, 'large-v3-turbo')):
        print("Warning: model large-v3-turbo not found. Downloading...")
        from core.downloader import setup_model
        setup_model('large-v3-turbo')
        
    # Pyinstaller command
    # We want a directory distribution (onedir) with necessary assets.
    # faster-whisper and ctranslate2 need some special care sometimes, 
    # but PyInstaller usually handles it if imported properly.
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--windowed", # No console window
        "--name", "MoziOkoshi",
        "--icon", "NONE", # Add icon path later if needed
        "--add-data", f"{filler_dict};.",
        "--add-data", f"ui/styles.qss;ui/",
        "--collect-data", "faster_whisper", # ensures whisper assets
        "--collect-data", "ctranslate2",
        "main.py"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    # Post build step:
    # We need to manually copy ffmpeg and models to the dist/MoziOkoshi directory 
    # to keep it neat (so users can add other models).
    import shutil
    dist_dir = os.path.join(app_dir, 'dist', 'MoziOkoshi')
    
    if os.path.exists(ffmpeg_dir):
        dest_ffmpeg = os.path.join(dist_dir, 'ffmpeg')
        if not os.path.exists(dest_ffmpeg):
            shutil.copytree(ffmpeg_dir, dest_ffmpeg)
            
    if os.path.exists(models_dir):
        dest_models = os.path.join(dist_dir, 'models')
        if not os.path.exists(dest_models):
            shutil.copytree(models_dir, dest_models)
            
    print("Build finished successfully! Check the 'dist/MoziOkoshi' folder.")

if __name__ == "__main__":
    build()
