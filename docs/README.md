# MoziOkoshi

> [!IMPORTANT]
> **実行ファイルの配布について**  
> 本アプリケーションは AI エンジン（PyTorch/CUDA）を同梱しているため、ビルド後のファイル容量が非常に巨大（数 GB）になります。GitHub のリポジトリ制限により実行ファイルを直接公開することが難しいため、必要に応じて各自でビルドしていただくか、外部ストレージ等での配布を想定しています。

## 概要
MoziOkoshi は、音声・動画ファイルを高速に文字起こしするデスクトップアプリケーションです。  
- **言語**: 日本語（デフォルト） / 英語  
- **モデル**: `faster-whisper` の `large-v3-turbo` / `large-v3` / `medium`  
- **UI**: PySide6 で構築されたシンプルな GUI  
- **出力形式**: TXT（全文）、SRT（字幕）、VTT（字幕）、タイムスタンプ付き TXT

## 主な機能
| 機能 | 説明 |
|------|------|
| **音声分割** | 20分ごとに自動で分割し、メモリ使用量を抑制 |
| **GPU/CPU 自動判定** | CUDA が利用可能なら GPU で推論、無ければ CPU で実行 |
| **フィラー除去** | `filler_dict.txt` に登録された語を除去 |
| **句読点補正** | 文末に句点を自動追加 |
| **複数フォーマット出力** | 同時に複数形式で保存可能 |
| **ログ表示** | GUI 内でリアルタイムログを確認 |

## 使い方
1. **起動**  
   `python main.py`（またはビルド済み実行ファイル）  
2. **ファイル選択**  
   - ドラッグ＆ドロップ  
   - 「ファイルを選択」ボタン  
3. **出力設定**  
   - 出力先フォルダを指定  
   - 形式・言語・フィラー除去・句読点補正を選択  
4. **実行**  
   「文字起こし開始」ボタンを押す  
5. **結果確認**  
   出力フォルダに指定した形式のファイルが生成されます。  

## 注意事項
- **初回起動時**  
  - モデル（`large-v3-turbo` など）と `ffmpeg` がローカルに無い場合、自動でダウンロードします。  
  - ダウンロードに数分かかる場合があります。  
- **GPU 要件**  
  - 4GB 以上の VRAM が必要（`medium` モデルは 3GB 未満でも動作）。  
- **ファイルサイズ**  
  - 大きな音声ファイルは分割処理によりメモリを節約しますが、処理時間は長くなる可能性があります。  
  - **配布用実行ファイル（ZIP版）の容量について**:  
    最新の最適化により、巨大な **PyTorch を同梱しない構成** に移行しました。これにより、以前の数 GB 単位から数百 MB 単位へと劇的に軽量化されています。AI エンジンには軽量・高速な `ctranslate2` を採用しており、Python や PyTorch のインストール不要で、引き続き GPU による高速な文字起こしが可能です。

## 外部ソフトウェア・モデル
本プロジェクトでは以下の外部ソフトウェアおよびモデルを使用しています。

- **FFmpeg**: 音声の抽出・変換に使用
  - 公式サイト: [https://ffmpeg.org/](https://ffmpeg.org/)
  - 配布元 (BtbN): [https://github.com/BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds)
- **faster-whisper**: 文字起こしエンジン
  - リポジトリ: [https://github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- **Whisper Model (large-v3-turbo)**: 学習済み AI モデル
  - モデル配布元: [https://huggingface.co/Systran/faster-whisper-large-v3-turbo](https://huggingface.co/Systran/faster-whisper-large-v3-turbo)

## 開発環境
- Python 3.10  
- PySide6  
- faster-whisper 1.2.1  
- torch 2.5.1+cu121  
- torchaudio 2.5.1+cu121  

## ライセンス
MIT License

## 連絡先
- GitHub: https://github.com/iwa-kasoutuuuuuka/Moziokoshi  
- メール: example@example.com