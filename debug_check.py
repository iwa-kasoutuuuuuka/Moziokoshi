import sys
import os

file_path = r"core\transcriber.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    print(f"Line 109: |{lines[108].strip()}|")
    print(f"Line 120: |{lines[119].strip()}|")
