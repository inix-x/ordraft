import os
import sys
import platform
import subprocess
import shutil

from .enums import TemplateType, TemplateFile

class Data:
    @property
    def app_data_path(self):
        system = platform.system()

        if system == "Windows":
            return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming")), "OrDraft")
        elif system == "Darwin":  # macOS
            return os.path.join(os.path.expanduser("~/Library/Application Support"), "OrDraft")
        else:  # Linux & other OS
            return os.path.join(os.path.expanduser("~/.config"), "OrDraft")
    
    def get_path(self, relative_path=None):
        """
        Get absolute path for the given relative path, works for development and for PyInstaller bundled app.
        If no relative path is provided, returns the base path.
        """
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        if relative_path is not None:
            return str(os.path.join(base_path, relative_path))
        else:
            return str(base_path)
        
    @property
    def app_first_time(self):
        return os.path.join(self.app_data_path, ".app_first_time")
    
    def is_first_time(self):
        os.makedirs(self.app_data_path, exist_ok=True)
        app_first_time = self.app_first_time
        if os.path.exists(app_first_time):
            return False  

        try:
            with open(app_first_time, "w") as f:
                f.write("This file indicates that the app has been used before.")

            if platform.system() == "Windows":
                try:
                    import ctypes
                    FILE_ATTRIBUTE_HIDDEN = 0x02
                    ctypes.windll.kernel32.SetFileAttributesW(app_first_time, FILE_ATTRIBUTE_HIDDEN)
                except Exception:
                    subprocess.run(["attrib", "+H", app_first_time], shell=True, check=False)

            elif platform.system() in ["Linux", "Darwin"]:
                hidden_path = os.path.join(os.path.dirname(app_first_time), f".{os.path.basename(app_first_time)}")
                os.rename(app_first_time, hidden_path)

        except Exception as e:
            print(f"Error while creating hidden file: {e}")

        return True  
    
    def moved_templates(self):
        try:
            template_path = self.get_path("templates")
            app_data_path = self.app_data_path

            destination_path = os.path.join(app_data_path, "templates")

            if not os.path.exists(template_path):
                print(f"Error: Source path '{template_path}' does not exist.")
                return

            if os.path.exists(destination_path):
                shutil.rmtree(destination_path)

            shutil.copytree(template_path, destination_path)

            print(f"Moved '{template_path}' to '{destination_path}' successfully.")
        except Exception:
            raise

    def moved_config(self):
        try:
            config_file_path = os.path.join(self.get_path(), "config.json")
            destination_path = self.app_data_path

            shutil.copy(config_file_path, destination_path)
        except Exception:
            raise

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