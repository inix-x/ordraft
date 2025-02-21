import os

from .enums import TemplateType, TemplateFile

class Data:
    @property
    def app_data_path(self):
        return os.path.join(os.environ.get("APPDATA"), "OrDraft")

class Utils:
    
    @staticmethod
    def ensure_paths(self, path: str):
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def get_unique_filename(save_location, filename, template_type: TemplateType, extension="docx"):
        """Generate a unique filename by adding a numeric suffix if the file exists."""
        suffix = TemplateFile.get_template_filetype(template_type)
        path = os.path.join(save_location, f"{filename}_{suffix}.{extension}")
        counter = 1

        while os.path.exists(path):
            path = os.path.join(save_location, f"{filename}_{suffix}_{counter}.{extension}")
            counter += 1

        return os.path.realpath(path)
    
    def get_app_resource(self, file) -> str:
        return os.path.join(os.path.dirname(os.path.abspath(file)), "resource")