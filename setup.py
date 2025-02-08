from cx_Freeze import setup, Executable
import os

# Include templates and other non-Python files
include_files = [
    ('templates', 'templates'),  # Copy templates directory
    'icon.ico'  # Include the app icon
]

# Dependencies (can be automatically detected)
build_exe_options = {
    "packages": ["pkgs"],  # Add any other dependencies like pandas or pdfplumber here
    "include_files": include_files,
    "includes": []
}

# Define the executable
exe = Executable(
    script="main.py",  # Entry point of your app
    base="Win32GUI",  # For GUI apps, use "Win32GUI", for console apps, omit this
    target_name="OrDraft.exe",  # Output executable name
    icon="icon.ico"  # Application icon
)

# Setup configuration
setup(
    name="OrDraft",
    version="0.1.2",
    description="OrDraft Installer with cx_Freeze",
    options={"build_exe": build_exe_options},
    executables=[exe]
)
