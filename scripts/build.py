# -*- coding: utf-8 -*-
# @Author: Cheniosc
# @Date: 2024/6/5

import shutil
import os
import site

import PyInstaller.__main__

site_packages_path = site.getsitepackages()[1]

PyInstaller.__main__.run([
    os.path.join(os.path.dirname(__file__), 'create_ipv6_tunnel.py'),
    '--hidden-import=ipsw_parser',
    '--hidden-import=zeroconf',
    '--hidden-import=pyimg4',
    '--hidden-import=apple_compress',
    '--hidden-import=zeroconf._utils.ipaddress',
    '--hidden-import=zeroconf._handlers.answers',
    '--hidden-import=readchar',
    '--copy-metadata=pyimg4',
    '--copy-metadata=readchar',
    '--copy-metadata=apple_compress',
    '--add-binary', f"{site_packages_path}/pytun_pmd3/*;pytun_pmd3",
    '--onefile'
])


PyInstaller.__main__.run([
    os.path.join(os.path.dirname(__file__), 'tidevice_ui.py'),
    '--hidden-import=ipsw_parser',
    '--hidden-import=zeroconf',
    '--hidden-import=pyimg4',
    '--hidden-import=apple_compress',
    '--hidden-import=zeroconf._utils.ipaddress',
    '--hidden-import=zeroconf._handlers.answers',
    '--hidden-import=readchar',
    '--copy-metadata=pyimg4',
    '--copy-metadata=readchar',
    '--copy-metadata=apple_compress',
    '--add-binary', f"{site_packages_path}/pytun_pmd3/*;pytun_pmd3",
    '--onefile'
])

