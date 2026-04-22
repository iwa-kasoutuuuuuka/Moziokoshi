import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFileDialog, QGroupBox, QRadioButton, QCheckBox, 
    QTextEdit, QProgressBar, QLineEdit, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from core.transcriber import Transcriber, get_gpu_info
from core.downloader import get_ffmpeg_path, get_app_dir
from utils.logger import logger, gui_log_signal
from utils.settings import settings

class TranscriptionThread(QThread):
    progress_signal = Signal(int)
    total_progress_signal = Signal(int)
    log_signal = Signal(str)
    segment_signal = Signal(str)
    file_finished_signal = Signal(int, int) # completed, total
    finished_signal = Signal(bool, str) # success, message
    
    def __init__(self, files, output_dir, mode, formats, options):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.mode = mode
        self.formats = formats
        self.options = options
        self.is_running = True
        self.transcriber = None

    def run(self):
        try:
            app_dir = get_app_dir()
            ffmpeg_path = get_ffmpeg_path()
            models_dir = os.path.join(app_dir, 'models')
            
            self.log_signal.emit("Transcriber initialization...")
            self.transcriber = Transcriber(self.mode, models_dir, app_dir, ffmpeg_path)
            
            total_files = len(self.files)
            for idx, file_path in enumerate(self.files):
                if not self.is_running:
                    self.log_signal.emit("Batch process cancelled.")
                    break
                    
                self.log_signal.emit(f"Processing ({idx+1}/{total_files}): {os.path.basename(file_path)}")
                self.progress_signal.emit(0)
                
                def progress_cb(pct):
                    if self.is_running:
                        self.progress_signal.emit(pct)
                
                success = self.transcriber.transcribe_file(
                    file_path=file_path,
                    output_dir=self.output_dir,
                    formats=self.formats,
                    lang='ja' if self.options['lang'] == 'ja' else 'en',
                    enable_filler=self.options['enable_filler'],
                    enable_punc=self.options['enable_punc'],
                    enable_replace=self.options['enable_replace'],
                    progress_callback=progress_cb,
                    segment_callback=self.segment_signal.emit
                )
                
                if success:
                    self.log_signal.emit(f"Completed: {os.path.basename(file_path)}")
                else:
                    self.log_signal.emit(f"Failed: {os.path.basename(file_path)}")
                
                self.file_finished_signal.emit(idx + 1, total_files)
                self.total_progress_signal.emit(int((idx + 1) / total_files * 100))
                    
            if self.is_running:
                self.finished_signal.emit(True, "All files in queue processed.")
                
        except Exception as e:
            logger.error(f"Queue Thread error: {e}", exc_info=True)
            self.finished_signal.emit(False, str(e))
            
    def stop(self):
        self.is_running = False
        # If we need more aggressive stop, we could try to signal the transcriber
        # but for now, we wait for current segment/chunk to finish.

class DropLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setReadOnly(True)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.setText(path)
            elif os.path.isfile(path):
                self.setText(os.path.dirname(path))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MoziOkoshi Pro - 音声・動画文字起こし")
        self.setMinimumSize(800, 600)
        self.setAcceptDrops(True)
        
        # Set window icon
        app_dir = get_app_dir()
        icon_path = os.path.join(app_dir, "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.files_to_process = []
        self.worker_thread = None
        
        self.init_ui()
        self.setup_signals()
        self.check_system()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # 1. Input Section
        input_group = QGroupBox("入力ファイル (ドラッグ＆ドロップ可)")
        input_layout = QVBoxLayout()
        self.file_label = QLabel("ファイルが選択されていません")
        self.file_label.setWordWrap(True)
        
        btn_layout = QHBoxLayout()
        self.btn_select_files = QPushButton("ファイルを選択")
        self.btn_select_files.setObjectName("btn_select")
        self.btn_select_files.clicked.connect(self.select_files)
        # self.btn_select_folder = QPushButton("フォルダを選択")
        btn_layout.addWidget(self.btn_select_files)
        btn_layout.addStretch()
        
        input_layout.addWidget(self.file_label)
        input_layout.addLayout(btn_layout)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # 2. Output Section
        output_group = QGroupBox("出力設定")
        output_layout = QVBoxLayout()
        
        out_dir_layout = QHBoxLayout()
        out_dir_layout.addWidget(QLabel("出力先:"))
        self.out_dir_edit = DropLineEdit()
        self.out_dir_edit.setPlaceholderText("ドラッグ＆ドロップまたはボタンで選択")
        self.btn_out_dir = QPushButton("参照")
        self.btn_out_dir.setObjectName("btn_out_dir")
        self.btn_out_dir.clicked.connect(self.select_out_dir)
        out_dir_layout.addWidget(self.out_dir_edit)
        out_dir_layout.addWidget(self.btn_out_dir)
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("形式:"))
        self.chk_txt = QCheckBox("TXT (全文)")
        self.chk_srt = QCheckBox("SRT (字幕)")
        self.chk_vtt = QCheckBox("VTT (字幕)")
        self.chk_time_txt = QCheckBox("TXT (タイムスタンプ付)")
        self.chk_txt.setChecked(True)
        self.chk_srt.setChecked(True)
        format_layout.addWidget(self.chk_txt)
        format_layout.addWidget(self.chk_srt)
        format_layout.addWidget(self.chk_vtt)
        format_layout.addWidget(self.chk_time_txt)
        format_layout.addStretch()
        
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("言語:"))
        self.rdo_ja = QRadioButton("日本語")
        self.rdo_en = QRadioButton("英語")
        self.rdo_ja.setChecked(True)
        lang_layout.addWidget(self.rdo_ja)
        lang_layout.addWidget(self.rdo_en)
        lang_layout.addStretch()
        
        opt_layout = QHBoxLayout()
        self.chk_filler = QCheckBox("フィラー除去")
        self.chk_punc = QCheckBox("句読点補正")
        self.chk_replace = QCheckBox("単語置換 (辞書)")
        self.chk_replace.setChecked(True)
        opt_layout.addWidget(self.chk_filler)
        opt_layout.addWidget(self.chk_punc)
        opt_layout.addWidget(self.chk_replace)
        opt_layout.addStretch()
        
        output_layout.addLayout(out_dir_layout)
        output_layout.addLayout(format_layout)
        output_layout.addLayout(lang_layout)
        output_layout.addLayout(opt_layout)
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # 3. Model / GPU Section
        model_group = QGroupBox("処理モード / リソース")
        model_layout = QVBoxLayout()
        
        self.lbl_gpu = QLabel("GPUチェック中...")
        self.lbl_gpu.setStyleSheet("font-weight: bold; color: #ffcc00; margin-bottom: 5px;")
        
        mode_btn_layout = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        self.rdo_turbo = QRadioButton("Turbo (large-v3-turbo)")
        self.rdo_high = QRadioButton("高精度 (large-v3)")
        self.rdo_light = QRadioButton("軽量 (medium)")
        self.rdo_turbo.setChecked(True)
        
        self.mode_group.addButton(self.rdo_turbo, 0)
        self.mode_group.addButton(self.rdo_high, 1)
        self.mode_group.addButton(self.rdo_light, 2)
        
        mode_btn_layout.addWidget(self.rdo_turbo)
        mode_btn_layout.addWidget(self.rdo_high)
        mode_btn_layout.addWidget(self.rdo_light)
        
        model_layout.addWidget(self.lbl_gpu)
        model_layout.addLayout(mode_btn_layout)
        model_group.setLayout(model_layout)
        main_layout.addWidget(model_group)
        
        # --- Restore Settings ---
        self.restore_settings()
        
        # 4. Execution & Logs
        exec_layout = QHBoxLayout()
        self.btn_exec = QPushButton("文字起こし開始")
        self.btn_exec.setMinimumHeight(40)
        self.btn_exec.clicked.connect(self.start_processing)
        exec_layout.addWidget(self.btn_exec)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("current_progress")
        self.progress_bar.setValue(0)
        
        self.total_progress_bar = QProgressBar()
        self.total_progress_bar.setObjectName("total_progress")
        self.total_progress_bar.setValue(0)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("ここにリアルタイムでテキストが表示されます...")
        self.preview_text.setObjectName("preview_pane")
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        
        main_layout.addLayout(exec_layout)
        main_layout.addWidget(QLabel("現在のファイル:"))
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(QLabel("全体進捗:"))
        main_layout.addWidget(self.total_progress_bar)
        main_layout.addWidget(QLabel("リアルタイムプレビュー:"))
        main_layout.addWidget(self.preview_text, 1) # Give it stretch
        main_layout.addWidget(QLabel("ログ:"))
        main_layout.addWidget(self.log_text)
        
        self.setCentralWidget(central_widget)

    def restore_settings(self):
        self.out_dir_edit.setText(settings.get('output_dir'))
        formats = settings.get('formats')
        self.chk_txt.setChecked('txt' in formats)
        self.chk_srt.setChecked('srt' in formats)
        self.chk_vtt.setChecked('vtt' in formats)
        self.chk_time_txt.setChecked('timestamp_txt' in formats)
        
        lang = settings.get('lang')
        if lang == 'en': self.rdo_en.setChecked(True)
        else: self.rdo_ja.setChecked(True)
        
        self.chk_filler.setChecked(settings.get('enable_filler'))
        self.chk_punc.setChecked(settings.get('enable_punc'))
        self.chk_replace.setChecked(settings.get('enable_replace', True))
        
        model = settings.get('model')
        if model == 'large-v3': self.rdo_high.setChecked(True)
        elif model == 'medium': self.rdo_light.setChecked(True)
        else: self.rdo_turbo.setChecked(True)

    def save_current_settings(self):
        data = {
            'output_dir': self.out_dir_edit.text(),
            'formats': self.get_formats(),
            'model': self.get_selected_mode(),
            'lang': 'ja' if self.rdo_ja.isChecked() else 'en',
            'enable_filler': self.chk_filler.isChecked(),
            'enable_punc': self.chk_punc.isChecked(),
            'enable_replace': self.chk_replace.isChecked()
        }
        settings.save(data)

    def setup_signals(self):
        gui_log_signal.log_msg.connect(self.append_log)

    def append_preview(self, text):
        self.preview_text.append(text)
        # Scroll to bottom
        scrollbar = self.preview_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def check_system(self):
        # 1. GPU Check
        use_gpu, vram, force_medium = get_gpu_info()
        text = f"リソース状況: "
        if use_gpu:
            text += f"GPU使用可能 (VRAM: {vram:.1f}GB)"
            if force_medium:
                text += " - VRAM不足のため軽量モードに制限されます"
                self.rdo_light.setChecked(True)
                self.rdo_turbo.setEnabled(False)
                self.rdo_high.setEnabled(False)
        else:
            text += "CPU使用中 (GPUが見つからないかCUDAが利用できません)"
            
        self.lbl_gpu.setText(text)
        
        # 2. FFmpeg / FFprobe Check
        ffmpeg_path = get_ffmpeg_path()
        ffprobe_path = ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
        
        missing = []
        if not os.path.isfile(ffmpeg_path):
            missing.append("ffmpeg.exe")
        if not os.path.isfile(ffprobe_path):
            missing.append("ffprobe.exe")
            
        if missing:
            msg = f"警告: {' と '.join(missing)} が見つかりません。\nパス: {os.path.dirname(ffmpeg_path)}\n\nアプリを正しく動作させるには、セットアップ用スクリプトを実行するか、ffmpegフォルダにこれらを配置してください。"
            logger.error(msg)
            QMessageBox.warning(self, "ツール欠損", msg)
        else:
            logger.info(f"FFmpeg/FFprobe found at: {os.path.dirname(ffmpeg_path)}")

        logger.info("System check completed.")

    def append_log(self, msg):
        self.log_text.append(msg)
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "ファイルを選択", "", 
            "Media Files (*.mp4 *.mkv *.avi *.wav *.mp3 *.m4a);;All Files (*)"
        )
        if files:
            self.add_files(files)

    def select_out_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "出力先フォルダを選択")
        if dir_path:
            self.out_dir_edit.setText(dir_path)

    def add_files(self, files):
        # Extend valid media checking
        valid_exts = ['.mp4', '.mkv', '.avi', '.wav', '.mp3', '.m4a']
        added = []
        for f in files:
            if os.path.splitext(f)[1].lower() in valid_exts:
                if f not in self.files_to_process:
                    self.files_to_process.append(f)
                    added.append(os.path.basename(f))
                    
        if added:
            self.file_label.setText(f"{len(self.files_to_process)}個のファイルが選択されています:\n" + "\n".join([os.path.basename(f) for f in self.files_to_process]))
            # Set default out_dir if empty
            if not self.out_dir_edit.text() and self.files_to_process:
                self.out_dir_edit.setText(os.path.dirname(self.files_to_process[0]))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        files = []
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path):
                files.append(path)
            elif os.path.isdir(path):
                # Optionally scan folder for media
                for root, dirs, fnames in os.walk(path):
                    for fname in fnames:
                        files.append(os.path.join(root, fname))
        if files:
            self.add_files(files)

    def get_selected_mode(self):
        if self.rdo_turbo.isChecked(): return 'large-v3-turbo'
        if self.rdo_high.isChecked(): return 'large-v3'
        if self.rdo_light.isChecked(): return 'medium'
        return 'large-v3-turbo'

    def get_formats(self):
        formats = []
        if self.chk_txt.isChecked(): formats.append('txt')
        if self.chk_srt.isChecked(): formats.append('srt')
        if self.chk_vtt.isChecked(): formats.append('vtt')
        if self.chk_time_txt.isChecked(): formats.append('timestamp_txt')
        return formats

    def start_processing(self):
        if not self.files_to_process:
            QMessageBox.warning(self, "エラー", "入力ファイルが選択されていません。")
            return
            
        out_dir = self.out_dir_edit.text()
        if not out_dir or not os.path.isdir(out_dir):
            QMessageBox.warning(self, "エラー", "有効な出力先フォルダを指定してください。")
            return
            
        formats = self.get_formats()
        if not formats:
            QMessageBox.warning(self, "エラー", "出力形式を少なくとも1つ選択してください。")
            return

        self.btn_exec.setEnabled(False)
        self.btn_exec.setText("処理中...")
        
        mode = self.get_selected_mode()
        opts = {
            'lang': 'ja' if self.rdo_ja.isChecked() else 'en',
            'enable_filler': self.chk_filler.isChecked(),
            'enable_punc': self.chk_punc.isChecked(),
            'enable_replace': self.chk_replace.isChecked()
        }
        
        self.preview_text.clear() # Clear for new batch
        self.worker_thread = TranscriptionThread(self.files_to_process, out_dir, mode, formats, opts)
        self.worker_thread.progress_signal.connect(self.progress_bar.setValue)
        self.worker_thread.total_progress_signal.connect(self.total_progress_bar.setValue)
        self.worker_thread.segment_signal.connect(self.append_preview)
        self.worker_thread.log_signal.connect(lambda m: logger.info(m))
        self.worker_thread.finished_signal.connect(self.on_processing_finished)
        self.worker_thread.start()

    def on_processing_finished(self, success, msg):
        self.btn_exec.setEnabled(True)
        self.btn_exec.setText("文字起こし開始")
        self.progress_bar.setValue(100)
        
        if success:
            QMessageBox.information(self, "完了", "すべての処理が完了しました！")
            # Clear inputs
            self.files_to_process = []
            self.file_label.setText("ファイルが選択されていません")
            self.progress_bar.setValue(0)
            self.total_progress_bar.setValue(0)
        else:
            QMessageBox.warning(self, "エラー終了", f"処理が一部失敗またはキャンセルされました。\n{msg}")

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self, '確認', '処理中ですが終了しますか？',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.worker_thread.stop()
                self.worker_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
        
        self.save_current_settings()
