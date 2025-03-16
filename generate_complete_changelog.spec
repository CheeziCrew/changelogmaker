# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['generate_complete_changelog.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('compare_api.py', '.'),
        ('compare_components.py', '.'),
    ],
    hiddenimports=[
        'javalang',
        'yaml',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='generate_complete_changelog',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)
