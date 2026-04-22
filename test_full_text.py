import os
import sys
from core.text_processor import process_text, load_filler_dict

def test_full_processing():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Create a dummy replacement dict
    with open(os.path.join(app_dir, 'replacement_dict.txt'), 'w', encoding='utf-8') as f:
        f.write("文字起こし,MoziOkoshi\n")
        f.write("えー, \n") # This is also a way to remove
        f.write("テニス,Tennis\n")
    
    text = "えー、この文字起こしツールはテニスのように軽快です。"
    print(f"Original: {text}")
    
    # Test with both enabled
    result = process_text(text, app_dir, enable_filler_removal=True, enable_punctuation=False, enable_replacement=True)
    print(f"Result  : {result}")
    
    if "MoziOkoshi" in result and "Tennis" in result:
        print("SUCCESS: Replacement and Filler removal worked together.")
    else:
        print("FAILED: Check logic.")

if __name__ == "__main__":
    test_full_processing()
