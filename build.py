import os
import sys
import subprocess
import shutil
from pathlib import Path

def build():
    print("Starting optimized build process for MoziOkoshi Pro...")
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure dependencies like ffmpeg and models exist first
    ffmpeg_dir = os.path.join(app_dir, 'ffmpeg')
    models_dir = os.path.join(app_dir, 'models')
    filler_dict = os.path.join(app_dir, 'filler_dict.txt')
    
    if not os.path.exists(ffmpeg_dir):
        print("Warning: ffmpeg folder not found. Downloading via core.downloader...")
        from core.downloader import setup_ffmpeg
        setup_ffmpeg()
        
    # Ensure necessary models are present
    from core.downloader import setup_model
    if not os.path.exists(os.path.join(models_dir, 'large-v3-turbo')):
        print("Model large-v3-turbo not found. Downloading...")
        setup_model('large-v3-turbo')
    
    if not os.path.exists(os.path.join(models_dir, 'tiny')):
        print("Model tiny (for speculative decoding) not found. Downloading...")
        setup_model('tiny')
        
    # Pyinstaller command
    # We explicitly exclude heavy libraries to keep the build size small.
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name", "MoziOkoshi",
        "--icon", "app_icon.ico",
        "--add-data", f"{filler_dict};.",
        "--add-data", "replacement_dict.txt;.",
        "--add-data", "ui/styles.qss;ui/",
        "--collect-data", "faster_whisper",
        "--collect-data", "ctranslate2",
        "--exclude-module", "matplotlib",
        "--exclude-module", "cv2",
        "--exclude-module", "pandas",
        "--exclude-module", "sklearn",
        "--exclude-module", "spacy",
        "--exclude-module", "paddle",
        "--exclude-module", "nltk",
        "--exclude-module", "scipy",
        "main.py"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    # Post build step: Selective copying of assets
    dist_dir = os.path.join(app_dir, 'dist', 'MoziOkoshi')
    
    # 1. Copy FFmpeg
    if os.path.exists(ffmpeg_dir):
        print("Copying FFmpeg...")
        dest_ffmpeg = os.path.join(dist_dir, 'ffmpeg')
        if os.path.exists(dest_ffmpeg):
            shutil.rmtree(dest_ffmpeg)
        shutil.copytree(ffmpeg_dir, dest_ffmpeg)
            
    # 2. Selective Copy Models (only actual model files, no HF cache)
    if os.path.exists(models_dir):
        print("Copying models (selective)...")
        dest_models = os.path.join(dist_dir, 'models')
        if not os.path.exists(dest_models):
            os.makedirs(dest_models)
        
        # Copy only specific models we want in the distribution
        for model_name in ['large-v3-turbo', 'tiny']:
            src = os.path.join(models_dir, model_name)
            dst = os.path.join(dest_models, model_name)
            if os.path.exists(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                # Copy model files but exclude the .cache folder if it exists
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('.cache'))
            
    print("\nBuild finished successfully!")
    print(f"Check the distribution folder: {dist_dir}")
    print("Target size should be significantly smaller (approx 5-6GB).")

if __name__ == "__main__":
    build()
