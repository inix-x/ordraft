import os

class Data:
    @property
    def app_data_path(self):
        return os.path.join(os.environ.get("APPDATA"), "OrDraft")

class Utils:
    
    @staticmethod
    def ensure_paths(self, path: str):
        os.makedirs(path, exist_ok=True)