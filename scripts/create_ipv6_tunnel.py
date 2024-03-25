# -*- coding: utf-8 -*-
# @Author: Cheniosc
# @Date: 2024/3/25

import sys
from pymobiledevice3.cli.remote import install_driver_if_required, cli_tunneld


if __name__ == '__main__':
    if sys.platform == 'win32':
        cli_tunneld(daemonize=False)
    else:
        cli_tunneld()