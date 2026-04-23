# MoziOkoshi Pro (v1.3.0)

高性能・軽量な音声および動画の文字起こしデスクトップアプリケーション。  
OpenAI Whisper (Faster-Whisper) を極限まで最適化し、プロフェッショナルな実用性を追求しました。

![App Icon](app_icon.png)

## 主な特徴

- **圧倒的な処理速度**: 
  - **Speculative Decoding (推論支援)**: `large-v3-turbo` をアシスタントモデルで支援し、精度を落とさず高速化。
  - **Numba JIT 最適化**: 音声処理や文字列操作をマシンコードレベルで最適化し、ボトルネックを排除。
  - **完全メモリ内処理**: ディスク I/O を回避し、すべての処理を RAM 上で完結。
- **配布サイズの大幅削減**: 
  - 不要なライブラリ（OpenCV, Matplotlib等）を排除し、成果物を約 6.2GB に集約。
- **柔軟なカスタマイズ**:
  - **カスタム置換**: `replacement_dict.txt` を編集することで、固有名詞や社内用語の誤字を自動補正。
  - **フィラー除去**: 「えー」「あのー」などの不要な語句を Trie 木エンジンで高速に一括削除。
- **ポータブル設計**:
  - インストール不要。`ffmpeg` や `models` を内蔵し、環境を選ばず即座に動作。

## システム要件

- **OS**: Windows 10/11 (64-bit)
- **GPU (推奨)**: NVIDIA GPU (VRAM 4GB以上推奨)
- **CPU**: AVX2 命令セット対応の CPU

## 使い方

1. `MoziOkoshi.exe` を実行します。
2. 文字起こししたい動画または音声ファイルをドラッグ＆ドロップします。
3. 言語や出力形式、オプション（推論支援、カスタム置換など）を選択します。
4. 「文字起こし開始」をクリックします。

## カスタマイズ

### `replacement_dict.txt`
`元の単語,置換後の単語` の形式で記述します。
例:
```text
Gemini,ジェミニ
AIアシスタント,Antigravity
```

## 開発・ビルド

ソースコードからビルドする場合：
```bash
py -m pip install -r requirements.txt
py build.py
```

## ライセンス

[MIT License](LICENSE)