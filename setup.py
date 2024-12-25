from setuptools import setup

APP = ['app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['PIL'],
    'includes': ['PySide6'],
    'iconfile': 'icon.icns',  # Optional: if you have an icon file
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 