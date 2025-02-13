import os
import sys

class Data:
    @property
    def app_data_path(self):
        return os.path.join(os.environ.get("APPDATA"), "OrDraft")

class Utils:
    
    @staticmethod
    def ensure_paths(self, path: str):
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def get_unique_filename(save_location, filename, extension="docx"):
        """Generate a unique filename by adding a numeric suffix if the file exists."""
        path = os.path.join(save_location, f"{filename}.{extension}")
        counter = 1

        while os.path.exists(path):
            path = os.path.join(save_location, f"{filename}_{counter}.{extension}")
            counter += 1

        return os.path.realpath(path)
    
    def get_app_resource(self, file) -> str:
        return os.path.join(os.path.dirname(os.path.abspath(file)), "resource")