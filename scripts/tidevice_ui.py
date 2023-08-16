# -*- coding: utf-8 -*-
# @Author: Cheniosc
# @Date: 2023/8/11

import sys
import typing
from tkinter import *
from tkinter import ttk
from logzero import setup_logger
from tabulate import tabulate
from loguru import logger as ulogger
from typing import Optional, Union
from tidevice._usbmux import Usbmux
from tidevice._proto import LOG, MODELS, PROGRAM_NAME, ConnectionType
from tidevice._device import Device
from tidevice.exceptions import MuxError, MuxServiceError, ServiceError


class FNDeviceDebugApp:
    def __init__(self):
        self.um = Usbmux()
        self.device_combobox: ttk.Combobox = None
        self.bunde_entry: Entry = None

    @staticmethod
    def set_win(tk, title, width=800, height=480):
        tk.title(title)
        # 获取屏幕尺寸以计算布局参数，使窗口居屏幕中央
        screenwidth = tk.winfo_screenwidth()
        screenheight = tk.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        tk.geometry(alignstr)
        # 设置窗口是否可变长、宽，True：可变，False：不可变
        tk.resizable(width=False, height=False)

    def update_combobox_data(self, Event=None):
        print(self.device_combobox.get())
        self.device_combobox.set('')
        device_list = self.get_device_list()
        values = [device_list[udid][3]+"("+device_list[udid][2]+")" for udid in device_list]
        self.device_combobox["values"] = values
        if len(values) > 0:
            self.device_combobox.current(0)

    def get_device_list(self):
        ds = self.um.device_list()
        ds = [info for info in ds if info.conn_type == ConnectionType.USB]

        device_list = {}
        for dinfo in ds:
            udid, conn_type = dinfo.udid, dinfo.conn_type
            try:
                _d = Device(udid, self.um)
                name = _d.name
                serial = _d.get_value("SerialNumber")
                device_list[udid] = [udid, serial, name, MODELS.get(_d.product_type, "-"), _d.product_version, conn_type]
            except MuxError:
                name = ""
        return device_list

    def _complete_udid(self, udid: Optional[str] = None) -> str:
        infos = self.um.device_list()
        # Find udid exactly match
        for info in infos:
            if info.udid == udid:
                return udid
        if udid:
            sys.exit("Device for %s not detected" % udid)

        if len(infos) == 1:
            return infos[0].udid

        # filter only usb connected devices
        infos = [info for info in infos if info.conn_type == ConnectionType.USB]
        if not udid:
            if len(infos) >= 2:
                sys.exit("More than 2 usb devices detected")
            if len(infos) == 0:
                sys.exit("No local device detected")
            return infos[0].udid

        ## Find udid starts-with
        # _udids = [
        #     info.udid for info in infos
        #     if info.udid.startswith(udid)
        # ]

        # if len(_udids) == 1:
        #     return _udids[0]
        raise RuntimeError("No matched device", udid)


    def _udid2device(self, udid: Optional[str] = None) -> Device:
        _udid = self._complete_udid(udid)
        # if _udid != udid:
        #     logger.debug("AutoComplete udid %s", _udid)
        del (udid)
        return Device(_udid, self.um)

    def launch_app(self):

        bunde_id = self.bunde_entry.get()
        # d = _udid2device(args.udid)
        d = self._udid2device()

        env = {}
        launch_args = []
        launch_args.append('-FIRAnalyticsDebugEnabled')
        launch_args.append('-FIRDebugEnabled')

        try:
            with d.connect_instruments() as ts:
                pid = ts.app_launch(bunde_id,
                                    app_env=env,
                                    args=launch_args,
                                    kill_running=False)
                print("PID:", pid)
        except ServiceError as e:
            sys.exit(e)

    def show(self):
        root = Tk()
        self.set_win(root, 'iOS调试工具', 800, 480)
        # root.configure(bg='white')

        device_label = Label(root, text="设备：")
        device_label.grid(row=1, column=1, sticky=E)

        self.device_combobox = ttk.Combobox(root, state="readonly")
        self.device_combobox.grid(row=1, column=3, sticky=W)
        self.update_combobox_data()
        self.device_combobox.bind("<Button-1>", self.update_combobox_data)

        bundle_label = Label(root, text="应用BundleID：")
        bundle_label.grid(row=3, column=1, sticky=E)

        self.bunde_entry = Entry(root)
        self.bunde_entry.grid(row=3, column=3, rowspan=2, sticky=W)

        button = Button(root, text="调试", command=self.launch_app, width=10)
        button.grid(row=5, column=3, sticky=W)

        # 为了确保总共有6列，我们可以使用columnconfigure()方法设置每列的权重
        for i in range(7):
            root.columnconfigure(i, weight=1)
        # for i in range(4):
        #     root.rowconfigure(i, weight=1)
        root.mainloop()


def main():
    app = FNDeviceDebugApp()
    app.show()


if __name__ == '__main__':
    main()
