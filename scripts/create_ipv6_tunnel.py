# -*- coding: utf-8 -*-
# @Author: Cheniosc
# @Date: 2024/3/25
import tempfile
from functools import partial
from pymobiledevice3.remote.common import TunnelProtocol
from pymobiledevice3.cli.remote import install_driver_if_required, cli_tunneld
from pymobiledevice3.remote.module_imports import MAX_IDLE_TIMEOUT, start_tunnel, verify_tunnel_imports
from pymobiledevice3.tunneld import TunneldRunner
from pymobiledevice3.remote.utils import TUNNELD_DEFAULT_ADDRESS


# def create_tunneld(host: str, port: int, daemonize: bool, protocol: str):
#     """ Start Tunneld service for remote tunneling """
#     if not verify_tunnel_imports():
#         return
#     install_driver_if_required()
#     protocol = TunnelProtocol(protocol)
#     tunneld_runner = partial(TunneldRunner.create, host, port, protocol)
#     if daemonize:
#         try:
#             from daemonize import Daemonize
#         except ImportError:
#             raise NotImplementedError('daemonizing is only supported on unix platforms')
#         with tempfile.NamedTemporaryFile('wt') as pid_file:
#             daemon = Daemonize(app=f'Tunneld {host}:{port}', pid=pid_file.name,
#                                action=tunneld_runner)
#
#             daemon.start()
#     else:
#         tunneld_runner()
#


if __name__ == '__main__':
    cli_tunneld()
