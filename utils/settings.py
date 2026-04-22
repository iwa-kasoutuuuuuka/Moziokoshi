import json
import os
from core.downloader import get_app_dir

class Settings:
    def __init__(self):
        self.settings_path = os.path.join(get_app_dir(), 'settings.json')
        self.defaults = {
            'output_dir': '',
            'formats': ['txt', 'srt'],
            'model': 'large-v3-turbo',
            'lang': 'ja',
            'enable_filler': True,
            'enable_punc': True
        }
        self.data = self.load()

    def load(self):
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Merge with defaults to handle missing keys
                    return {**self.defaults, **data}
            except Exception:
                return self.defaults.copy()
        return self.defaults.copy()

    def save(self, data=None):
        if data:
            self.data.update(data)
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def get(self, key):
        return self.data.get(key, self.defaults.get(key))

settings = Settings()
