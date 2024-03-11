# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['configurator.py'],
    pathex=[],
    binaries=[],
    datas=[('./../parameters.xml', './src'), ('./src/*.*', './src')],
    hiddenimports=['pymavlink.dialects.v20', 'pymavlink.dialects.v20.ardupilotmega'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='configurator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='configurator',
)
