# MoziOkoshi 技術仕様書

## 1. アプリケーション概要
MoziOkoshi は、`faster-whisper` をエンジンとして使用した、Windows 向けの高速文字起こしアプリケーションです。

## 2. 動作要件
- **OS**: Windows 10 / 11 (64bit)
- **CPU**: x86_64
- **GPU (推奨)**: NVIDIA GeForce シリーズ (VRAM 4GB以上推奨)
- **メモリ**: 8GB 以上

## 3. 主要技術スタック
- **言語**: Python 3.10
- **GUI フレームワーク**: PySide6 (Qt for Python)
- **AI エンジン**: faster-whisper (ctranslate2 4.4.0)
- **数値計算/AI 基盤**:
  - torch (PyTorch) 2.5.1+cu121
  - torchaudio 2.5.1+cu121
- **依存ツール**: FFmpeg (音声抽出・変換用)

## 4. 配布形態
- **ポータブル版 (ZIP)**:
  - PyInstaller を用いてパッケージ化。
  - **容量に関する特記事項**:
    ポータブル版の ZIP ファイルは約 3GB〜4GB のサイズとなります。これには以下のコンポーネントが含まれているためです：
    - **PyTorch 実行環境**: ディープラーニングモデルを実行するためのエンジン。
    - **NVIDIA CUDA/cuDNN ライブラリ**: GPU 加速を実現するためのドライバライブラリ。
    - **Python インタプリタと標準ライブラリ**: ユーザ環境に Python が未インストールでも動作させるための同梱。

## 5. 自動セットアップ機能
初回起動時に以下のコンポーネントが不足している場合、自動的にダウンロードが行われます：
- **FFmpeg**: `https://github.com/BtbN/FFmpeg-Builds` より最新版を取得。
- **Whisper モデル**: `large-v3-turbo` モデルを Hugging Face より取得。
※ これらを除外することで、配布時のパッケージサイズを最小限に抑えています。

## 6. 処理フロー
1. 入力ファイル（動画/音声）の解析。
2. FFmpeg による音声ストリームの抽出・WAV 変換。
3. 音声ファイルの分割（20分単位、メモリ節約のため）。
4. faster-whisper による推論（文字起こし）。
5. 各フォーマット（TXT, SRT, VTT）への整形・保存。
