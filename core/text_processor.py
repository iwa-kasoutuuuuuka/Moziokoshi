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
    if not fillers or not text:
        return text
    
    # 1. Build Trie (トライ木の構築)
    # C++等の低レイヤ言語でも一般的に使われる高速なデータ構造です。
    trie = {}
    for filler in fillers:
        node = trie
        for char in filler:
            node = node.setdefault(char, {})
        node['#'] = True # 終端フラグ
    
    # 2. Match and Remove (一回の走査でマッチング)
    # 文字列を一度だけ走査するため、辞書サイズが大きくても O(N) で動作します。
    result = []
    i = 0
    n = len(text)
    
    while i < n:
        # トライ木を辿って最長マッチを探す
        match_len = 0
        node = trie
        curr_i = i
        
        # 最長一致を選択（例：「えー」と「えーと」がある場合「えーと」を消す）
        temp_match_len = 0
        while curr_i < n and text[curr_i] in node:
            node = node[text[curr_i]]
            curr_i += 1
            if '#' in node:
                temp_match_len = curr_i - i
        
        if temp_match_len > 0:
            # フィラーが見つかったのでスキップ
            i += temp_match_len
        else:
            # フィラーではないので文字を保持
            result.append(text[i])
            i += 1
            
    # Clean up double spaces if any
    res_str = "".join(result)
    res_str = re.sub(r' +', ' ', res_str).strip()
    return res_str

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
