import os
# import torch
from core.transcriber import Transcriber
from core.downloader import get_ffmpeg_path, get_app_dir

def verify_features():
    print("--- Starting Detailed Operation Verification ---")
    
    app_dir = get_app_dir()
    ffmpeg_path = get_ffmpeg_path()
    models_dir = os.path.join(app_dir, 'models')
    
    # Initialize transcriber with medium model for faster testing
    transcriber = Transcriber('medium', models_dir, app_dir, ffmpeg_path)
    
    file_path = os.path.join(app_dir, 'test_audio.wav')
    output_dir = os.path.join(app_dir, 'verification_output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Test cases: (enable_filler, enable_punc, formats)
    test_cases = [
        (True, True, ['txt', 'srt', 'vtt', 'timestamp_txt']),
        (False, False, ['txt'])
    ]
    
    for i, (filler, punc, formats) in enumerate(test_cases):
        print(f"\nTest Case {i+1}: filler={filler}, punc={punc}, formats={formats}")
        success = transcriber.transcribe_file(
            file_path=file_path,
            output_dir=output_dir,
            formats=formats,
            lang='ja',
            enable_filler=filler,
            enable_punc=punc
        )
        
        if success:
            print(f"Test Case {i+1} completed successfully.")
            for fmt in formats:
                suffix = "_ja"
                if fmt == "timestamp_txt":
                    suffix = "_ja_timestamp"
                    fmt = "txt"
                
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                out_path = os.path.join(output_dir, f"{base_name}{suffix}.{fmt}")
                if os.path.exists(out_path):
                    print(f"Verified output: {out_path} (Size: {os.path.getsize(out_path)} bytes)")
                else:
                    print(f"FAILED: Output missing: {out_path}")
        else:
            print(f"Test Case {i+1} FAILED.")

if __name__ == "__main__":
    verify_features()
