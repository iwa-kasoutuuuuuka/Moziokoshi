import os
from core.transcriber import Transcriber
from core.downloader import get_ffmpeg_path

def test_transcription():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_path = get_ffmpeg_path()
    models_dir = os.path.join(app_dir, 'models')
    
    transcriber = Transcriber('large-v3-turbo', models_dir, app_dir, ffmpeg_path)
    
    file_path = os.path.join(app_dir, 'test_audio.wav')
    output_dir = os.path.join(app_dir, 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    
    formats = ['txt', 'srt']
    
    success = transcriber.transcribe_file(
        file_path=file_path,
        output_dir=output_dir,
        formats=formats,
        lang='ja',
        enable_filler=False,
        enable_punc=False
    )
    
    if success:
        print("Transcription test completed successfully!")
        
        # Output generated content
        txt_path = os.path.join(output_dir, 'test_audio_ja.txt')
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                print(f"Content:\n{f.read()}")
    else:
        print("Transcription test failed!")

if __name__ == "__main__":
    test_transcription()
