# -*- coding: utf-8 -*-
# @Author: Cheniosc
# @Date: 2024/3/25


# import sys
# import tempfile
# from functools import partial
# import click
# from pymobiledevice3.remote.common import TunnelProtocol
# from pymobiledevice3.cli.cli_common import BaseCommand
from pymobiledevice3.cli.remote import cli_tunneld
# from pymobiledevice3.remote.module_imports import verify_tunnel_imports
# from pymobiledevice3.tunneld import TunneldRunner

# 升级pymobiledevice3到4.8.9后部分接口不存在了，先注释，后面有空再处理
# @click.command("create_ipv6_tunnel", cls=BaseCommand)
# @click.option('--host', default=TUNNELD_DEFAULT_ADDRESS[0])
# @click.option('--port', type=click.INT, default=TUNNELD_DEFAULT_ADDRESS[1])
# @click.option('-d', '--daemonize', is_flag=True)
# @click.option('-p', '--protocol', type=click.Choice([e.value for e in TunnelProtocol]),
#               default=TunnelProtocol.QUIC.value)
# def create_tunnel(host: str, port: int, daemonize: bool, protocol: str):
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
#             daemon.start()
#     else:
#         tunneld_runner()


if __name__ == '__main__':
    cli_tunneld()
    # create_tunneld()
    # cli_tunneld(TUNNELD_DEFAULT_ADDRESS[0], TUNNELD_DEFAULT_ADDRESS[1], True, TunnelProtocol.QUIC.value)
    # if sys.platform == 'win32':
    #     create_tunneld(TUNNELD_DEFAULT_ADDRESS[0], TUNNELD_DEFAULT_ADDRESS[1], False, TunnelProtocol.QUIC.value)
    # else:
    #     create_tunneld(TUNNELD_DEFAULT_ADDRESS[0], TUNNELD_DEFAULT_ADDRESS[1], True, TunnelProtocol.QUIC.value)
