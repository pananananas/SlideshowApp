from setuptools import setup
import os
import sys
import PySide6

# Find PySide6 location
PYSIDE6_PATH = os.path.dirname(PySide6.__file__)

# Get all PySide6 binaries and plugins
QT_PLUGINS_PATH = os.path.join(PYSIDE6_PATH, "Qt", "plugins")
BINARIES_PATH = os.path.join(PYSIDE6_PATH, "Qt", "bin")

# Collect all Qt plugins
qt_plugins = []
for plugin_type in ['platforms', 'imageformats', 'multimedia', 'styles', 'iconengines']:
    plugin_path = os.path.join(QT_PLUGINS_PATH, plugin_type)
    if os.path.exists(plugin_path):
        qt_plugins.append(plugin_type)

APP = ['app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,  # Changed to False to avoid potential issues
    'packages': [
        'PIL',
        'PySide6',
        'pathlib',
    ],
    'includes': [
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets'
    ],
    'excludes': [
        'matplotlib',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'wx'
    ],
    'qt_plugins': qt_plugins,
    'strip': True,
    'optimize': 2,
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleName': 'Slideshow',
        'CFBundleDisplayName': 'Slideshow',
        'CFBundleGetInfoString': "Slideshow",
        'CFBundleIdentifier': "com.yourcompany.slideshow",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,  # Enable dark mode support
    }
}

setup(
    name="Slideshow",
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)