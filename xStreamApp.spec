# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['xstream.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('res/xstream_icon.ico', 'res')  # Icon-Datei
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',

        # pyqtgraph (falls verwendet)
        'pyqtgraph',
        'pyqtgraph.opengl',  # Nur falls OpenGL genutzt wird
        'pyqtgraph.widgets',  # Falls zusätzliche Widgets verwendet werden

        # selenium
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium.webdriver.chrome',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='xStreamApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='res/xstream_icon.ico'  # Pfad zur Icon-Datei
)
