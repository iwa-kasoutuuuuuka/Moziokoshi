import os
import gc
# import torch  <-- Remove this to save ~2GB in build
from faster_whisper import WhisperModel
from core.audio_utils import get_audio_chunks, cleanup_chunks
from core.text_processor import process_text
from utils.logger import logger

def get_gpu_info():
    """
    Returns (use_gpu: bool, vram_gb: float, forced_medium: bool)
    torch を使わずに、環境変数や ctranslate2 の挙動から推測または簡易チェックします。
    """
    # 簡易的に NVIDIA GPU があるかチェック (Windows)
    try:
        import subprocess
        # nvidia-smi が実行できれば GPU ありと判断
        res = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            vram_mb = float(res.stdout.strip().split('\n')[0])
            vram_gb = vram_mb / 1024.0
            forced_medium = vram_gb < 3.0
            return True, vram_gb, forced_medium
    except Exception:
        pass
        
    return False, 0.0, False

def format_timestamp(seconds: float, separator: str = ","):
    """
    >>> format_timestamp(1234.567)
    '00:20:34,567'
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_int = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{seconds_int:02d}{separator}{milliseconds:03d}"

class Transcriber:
    def __init__(self, mode, model_dir, app_dir, ffmpeg_path):
        self.mode = mode # 'large-v3-turbo', 'large-v3', 'medium'
        self.model_dir = model_dir
        self.app_dir = app_dir
        self.ffmpeg_path = ffmpeg_path
        
        # Check GPU
        self.use_gpu, self.vram_gb, self.forced_medium = get_gpu_info()
        logger.info(f"GPU Available: {self.use_gpu}, VRAM: {self.vram_gb:.2f}GB")
        
        if self.forced_medium and self.mode != 'medium':
            logger.warning("VRAM is less than 3GB. Forcing 'medium' model.")
            self.mode = 'medium'
            
        # Ensure model is downloaded if not local
        model_path = os.path.join(self.model_dir, self.mode)
        if not os.path.exists(model_path):
            from core.downloader import setup_model
            logger.info(f"Model {self.mode} not found locally. Downloading...")
            setup_model(self.mode)
            
        device = "cuda" if self.use_gpu else "cpu"
        compute_type = "float16" if self.use_gpu else "int8"
        
        # CPU can't do float16 smoothly, sometimes we do int8 or compute_type="auto"
        # Since larger models with CPU and float16 might fail:
        if not self.use_gpu:
            compute_type = "int8"
            
        logger.info(f"Loading model {self.mode} on {device} with {compute_type}...")
        self.model = WhisperModel(self.mode, device=device, compute_type=compute_type, download_root=self.model_dir)
        logger.info("Model loaded successfully.")

    def transcribe_file(self, file_path, output_dir, formats, lang='ja', enable_filler=False, enable_punc=False, progress_callback=None):
        logger.info(f"Starting transcription for: {file_path}")
        
        chunks = get_audio_chunks(file_path, self.ffmpeg_path)
        if not chunks:
            logger.error("No valid audio found in the file.")
            return False
            
        all_segments = []
        total_chunks = len(chunks)
        
        try:
            for i, chunk in enumerate(chunks):
                chunk_data = chunk['data']
                time_offset = chunk['start_time']
                
                logger.info(f"Processing chunk {i+1}/{total_chunks}...")
                
                # Using faster-whisper with in-memory NumPy array
                segments, info = self.model.transcribe(chunk_data, language=lang, beam_size=5)
                
                for segment in segments:
                    # Apply text processing
                    text = process_text(segment.text, self.app_dir, enable_filler, enable_punc)
                    
                    adjusted_segment = {
                        "start": segment.start + time_offset,
                        "end": segment.end + time_offset,
                        "text": text
                    }
                    all_segments.append(adjusted_segment)
                    
                if progress_callback:
                    progress_callback(int((i + 1) / total_chunks * 100))
                    
                # Clean up memory
                gc.collect()
                # if self.use_gpu:
                #    torch.cuda.empty_cache()
                    
            # Export results
            self._export_results(file_path, output_dir, formats, lang, all_segments)
            logger.info(f"Completed transcription for: {file_path}")
            return True
            
        finally:
            cleanup_chunks(chunks)
            gc.collect()
            # if self.use_gpu:
            #    torch.cuda.empty_cache()

    def _export_results(self, file_path, output_dir, formats, lang, segments):
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        suffix = f"_{lang}"
        
        if "txt" in formats:
            out_path = os.path.join(output_dir, f"{base_name}{suffix}.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                for seg in segments:
                    f.write(f"{seg['text'].strip()}\n")
            logger.info(f"Saved: {out_path}")
            
        if "srt" in formats:
            out_path = os.path.join(output_dir, f"{base_name}{suffix}.srt")
            with open(out_path, "w", encoding="utf-8") as f:
                for idx, seg in enumerate(segments, start=1):
                    start = format_timestamp(seg['start'], ",")
                    end = format_timestamp(seg['end'], ",")
                    f.write(f"{idx}\n{start} --> {end}\n{seg['text'].strip()}\n\n")
            logger.info(f"Saved: {out_path}")
            
        if "vtt" in formats:
            out_path = os.path.join(output_dir, f"{base_name}{suffix}.vtt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("WEBVTT\n\n")
                for seg in segments:
                    start = format_timestamp(seg['start'], ".")
                    end = format_timestamp(seg['end'], ".")
                    f.write(f"{start} --> {end}\n{seg['text'].strip()}\n\n")
            logger.info(f"Saved: {out_path}")
            
        if "timestamp_txt" in formats:
            out_path = os.path.join(output_dir, f"{base_name}{suffix}_timestamp.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                for seg in segments:
                    start = format_timestamp(seg['start'], ".")[:8] # HH:MM:SS
                    f.write(f"[{start}] {seg['text'].strip()}\n")
            logger.info(f"Saved: {out_path}")
