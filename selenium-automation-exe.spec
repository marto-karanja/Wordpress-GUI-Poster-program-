# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main_gui.py'],
             pathex=['C:\\Users\\Administrator\\Documents\\Crawler\\uploader\\1.2'],
             binaries=[],
             datas=[('config.json', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
a.datas += [('gui/posta.ico','C:\\Users\\Admin\\Documents\\projects\\crawler\\Devt\\posta\\1.2\\gui\\posta.ico', "DATA"), ('gui/posta.png','C:\\Users\\Admin\\Documents\\projects\\crawler\\Devt\\posta\\1.2\\gui\\posta.png', "DATA")]
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Posta Uploader',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True , icon='gui/posta.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Posta Uploader')

