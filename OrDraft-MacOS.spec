# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('resource', 'resource'), ('resource/icons', 'resource/icons'), ('templates', 'templates'), ('config.json', '.')],
    hiddenimports=['pkgs'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OrDraft',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

app = BUNDLE(
    exe,
    name='OrDraft.app',
    icon=['resource\\icon.ico'],
    bundle_identifier="com.ordraft.ordraft"
)
