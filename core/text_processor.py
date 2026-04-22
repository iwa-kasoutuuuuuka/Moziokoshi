import os
import re
from numba import njit

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

from numba import njit
import numpy as np

@njit(cache=True)
def _numba_trie_match(text_chars, trie_data, trie_is_end):
    """
    NumbaでJITコンパイルされたTrie木マッチング・エンジン。
    C言語のポインタ遷移と同等の速度で動作します。
    """
    n = len(text_chars)
    result_mask = np.ones(n, dtype=np.bool_)
    
    i = 0
    while i < n:
        state = 0
        curr_i = i
        temp_match_len = 0
        
        while curr_i < n:
            char_code = text_chars[curr_i]
            # シンプルな文字コードマッチング（ハッシュ計算なしのO(1)アクセス）
            # trie_dataは [state, char_code] -> next_state の2D配列
            if char_code < 0 or char_code >= 10000: # 簡易的な制限
                break
            
            next_state = trie_data[state, char_code]
            if next_state == 0:
                break
            
            state = next_state
            curr_i += 1
            if trie_is_end[state]:
                temp_match_len = curr_i - i
        
        if temp_match_len > 0:
            for k in range(i, i + temp_match_len):
                result_mask[k] = False
            i += temp_match_len
        else:
            i += 1
            
    return result_mask

def remove_fillers(text, fillers):
    if not fillers or not text:
        return text
    
    # 1. Build Array-based Trie (Pythonで構築し、Numbaへ渡す)
    # 文字を Unicode ポイントに変換
    all_chars = sorted(list(set("".join(fillers))))
    char_map = {c: ord(c) for c in all_chars}
    max_char = max(char_map.values()) if char_map else 0
    
    # 最大文字コードが大きすぎる場合はフォールバック
    if max_char > 10000:
        # 以前のトライ木実装（Python）を使用
        return _remove_fillers_python(text, fillers)
        
    # [状態数, 文字コード範囲] の遷移テーブル
    # 簡易的に状態数を計算
    total_states = sum(len(f) for f in fillers) + 1
    trie_data = np.zeros((total_states, max_char + 1), dtype=np.int32)
    trie_is_end = np.zeros(total_states, dtype=np.bool_)
    
    next_free_state = 1
    for filler in fillers:
        state = 0
        for char in filler:
            c_code = ord(char)
            if trie_data[state, c_code] == 0:
                trie_data[state, c_code] = next_free_state
                next_free_state += 1
            state = trie_data[state, c_code]
        trie_is_end[state] = True
        
    # 2. Match with Numba
    text_arr = np.array([ord(c) for c in text], dtype=np.int32)
    mask = _numba_trie_match(text_arr, trie_data, trie_is_end)
    
    # 3. Reconstruct string
    result = []
    for i, m in enumerate(mask):
        if m:
            result.append(text[i])
            
    res_str = "".join(result)
    res_str = re.sub(r' +', ' ', res_str).strip()
    return res_str

def _remove_fillers_python(text, fillers):
    # フォールバック用（以前のトライ木実装）
    trie = {}
    for filler in fillers:
        node = trie
        for char in filler:
            node = node.setdefault(char, {})
        node['#'] = True
    result = []
    i = 0
    n = len(text)
    while i < n:
        node = trie
        curr_i = i
        temp_match_len = 0
        while curr_i < n and text[curr_i] in node:
            node = node[text[curr_i]]
            curr_i += 1
            if '#' in node:
                temp_match_len = curr_i - i
        if temp_match_len > 0:
            i += temp_match_len
        else:
            result.append(text[i])
            i += 1
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

def load_replacement_dict(app_dir):
    rep_path = os.path.join(app_dir, 'replacement_dict.txt')
    replacements = {}
    if os.path.exists(rep_path):
        with open(rep_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('#') or ',' not in line:
                    continue
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    replacements[parts[0]] = parts[1]
    return replacements

def replace_terms(text, replacement_dict):
    if not replacement_dict or not text:
        return text
        
    # フィラー除去と同じTrieロジックを使用するが、マッチした際に置換を行う
    # 簡略化のため、ここでは最長一致置換を実装
    # (より高速にするには _numba_trie_match を拡張して ID を返すようにするが、
    #  一般的な辞書サイズであれば Python での Trie 走査でも十分高速)
    
    fillers = list(replacement_dict.keys())
    # 最長一致のために長い順にソート
    fillers.sort(key=len, reverse=True)
    
    trie = {}
    for filler in fillers:
        node = trie
        for char in filler:
            node = node.setdefault(char, {})
        node['#'] = True
        node['value'] = replacement_dict[filler]
        
    result = []
    i = 0
    n = len(text)
    while i < n:
        node = trie
        curr_i = i
        temp_match_len = 0
        replacement_val = ""
        
        while curr_i < n and text[curr_i] in node:
            node = node[text[curr_i]]
            curr_i += 1
            if '#' in node:
                temp_match_len = curr_i - i
                replacement_val = node['value']
        
        if temp_match_len > 0:
            result.append(replacement_val)
            i += temp_match_len
        else:
            result.append(text[i])
            i += 1
            
    return "".join(result)

def process_text(text, app_dir, enable_filler_removal=False, enable_punctuation=False, enable_replacement=True):
    processed = text
    
    # 1. Custom Term Replacement (置換)
    if enable_replacement:
        rep_dict = load_replacement_dict(app_dir)
        if rep_dict:
            processed = replace_terms(processed, rep_dict)
        
    # 2. Filler Removal (除去)
    if enable_filler_removal:
        fillers = load_filler_dict(app_dir)
        processed = remove_fillers(processed, fillers)
        
    # 3. Punctuation (句読点)
    if enable_punctuation:
        processed = add_punctuation(processed)
        
    return processed
