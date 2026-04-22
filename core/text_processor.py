import os
import re

def load_filler_dict(app_dir):
    filler_path = os.path.join(app_dir, 'filler_dict.txt')
    fillers = []
    if os.path.exists(filler_path):
        with open(filler_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    fillers.append(word)
    return fillers

def remove_fillers(text, fillers):
    if not fillers:
        return text
    
    # Sort fillers by length descending to match longer phrases first
    fillers.sort(key=len, reverse=True)
    
    # Simple regex to remove filler words. Matches optional surrounding spaces.
    pattern = r'\s*(' + '|'.join(map(re.escape, fillers)) + r')\s*'
    
    # Replace with single space if there were spaces, or nothing
    # Actually, we should be careful not to remove parts of words.
    # Japanese doesn't usually use spaces, so simple replacement is mostly safe.
    result = text
    for filler in fillers:
        # standard replace
        result = result.replace(filler, '')
    
    # Clean up double spaces if any
    result = re.sub(r' +', ' ', result).strip()
    return result

def add_punctuation(text):
    if not text:
        return text
        
    text = text.strip()
    # If the text does not end with punctuation, add a period
    if not text.endswith(('。', '！', '？', '.', '!', '?')):
        text += '。'
        
    # Optional: simple heuristic for commas.
    # We leave deeper structural commas to the model, but we can fix obvious gaps.
    # A simple approach is just keeping the model's output for internal commas.
    
    return text

def process_text(text, app_dir, enable_filler_removal=False, enable_punctuation=False):
    processed = text
    if enable_filler_removal:
        fillers = load_filler_dict(app_dir)
        processed = remove_fillers(processed, fillers)
        
    if enable_punctuation:
        processed = add_punctuation(processed)
        
    return processed
