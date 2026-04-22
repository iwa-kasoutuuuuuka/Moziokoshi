import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.text_processor import remove_fillers

def test_filler_removal():
    fillers = ["えー", "あのー", "そのー", "えーと"]
    text = "えー、本日はあのー、そのー、えーと、文字起こしのテストです。"
    
    # The current implementation will remove filler words
    # Note: commas are not fillers, so they will remain.
    result = remove_fillers(text, fillers)
    print(f"Original: {text}")
    print(f"Result  : {result}")
    
    # Check if fillers are gone
    for f in fillers:
        if f in result:
            print(f"FAILED: {f} still in result")
            return
    print("SUCCESS: All fillers removed efficiently.")

if __name__ == "__main__":
    test_filler_removal()
