#!/bin/bash
# Define variables for Python version and installer package name
PYTHON_VERSION="3.12.5"
PYTHON_PKG="python-${PYTHON_VERSION}-macos11.pkg"
DOWNLOAD_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_PKG}"

# Download the Python installer if it doesn't already exist
if [ ! -f "${PYTHON_PKG}" ]; then
    echo "Downloading Python ${PYTHON_VERSION}..."
    curl -O "${DOWNLOAD_URL}"
else
    echo "Installer ${PYTHON_PKG} already exists."
fi

# Open the installer package (this will launch the installer GUI)
echo "Opening Python installer. Please complete the installation."
open "${PYTHON_PKG}"

# Optionally wait for the user to confirm that installation is complete
read -p "After installing Python, press Enter to continue..."

# Install required Python packages if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing requirements from requirements.txt..."
    python3 -m pip install -r requirements.txt
else
    echo "No requirements.txt found. Skipping package installation."
fi

# Create a shortcut (a .command file) on the Desktop to run main.py
DESKTOP_DIR="${HOME}/Desktop"
SHORTCUT_NAME="Run_main.command"

# Determine the absolute path for main.py (assuming it's in the same folder as this script)
MAIN_PY_PATH="$(pwd)/main.py"

echo "Creating shortcut on your Desktop: ${DESKTOP_DIR}/${SHORTCUT_NAME}"
cat <<EOL > "${DESKTOP_DIR}/${SHORTCUT_NAME}"
#!/bin/bash
# Change to the directory containing main.py and execute it
cd "$(dirname "${MAIN_PY_PATH}")"
python3 "$(basename "${MAIN_PY_PATH}")"
EOL

# Make the shortcut executable
chmod +x "${DESKTOP_DIR}/${SHORTCUT_NAME}"

echo "Setup complete. You can run main.py by double-clicking the shortcut on your Desktop."
