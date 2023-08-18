# -*- coding: utf-8 -*-
# @Author: Cheniosc
# @Date: 2023/8/11

import tkinter.messagebox
from tkinter import *
from tkinter import ttk
from typing import Optional, Union
from tidevice._usbmux import Usbmux
from tidevice._proto import LOG, MODELS, PROGRAM_NAME, ConnectionType
from tidevice._device import Device
from tidevice.exceptions import MuxError, MuxServiceError, ServiceError
import threading
import queue


def alert(message):
    tkinter.messagebox.showinfo("", message)


class FNDeviceDebugApp:
    def __init__(self):
        self.root = None
        self.um = Usbmux()
        self.device_combobox: ttk.Combobox = None
        self.bunde_entry: Entry = None
        self.syslog_text: Text = None
        self.syslog_button: Button = None
        self.syslog_service = None
        self.syslog_queue = queue.Queue()

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
                alert(MuxError)
        return device_list

    def complete_udid(self, udid: Optional[str] = None) -> str:
        infos = self.um.device_list()
        # Find udid exactly match
        for info in infos:
            if info.udid == udid:
                return udid
        if udid:
            raise Exception("Device for %s not detected" % udid)

        if len(infos) == 1:
            return infos[0].udid

        # filter only usb connected devices
        infos = [info for info in infos if info.conn_type == ConnectionType.USB]
        if not udid:
            if len(infos) >= 2:
                raise Exception("More than 2 usb devices detected")
            if len(infos) == 0:
                raise Exception("No local device detected")
            return infos[0].udid
        raise Exception("No matched device", udid)

    def udid2device(self, udid: Optional[str] = None) -> Device:
        _udid = self.complete_udid(udid)
        # if _udid != udid:
        #     logger.debug("AutoComplete udid %s", _udid)
        del (udid)
        return Device(_udid, self.um)

    def find_device_udid(self, device_name):
        device_list = self.get_device_list()
        for udid in device_list:
            if device_list[udid][3]+"("+device_list[udid][2]+")" == device_name:
                return udid

    def update_combobox_data(self, Event=None):
        print(self.device_combobox.get())
        self.device_combobox.set('')
        device_list = self.get_device_list()
        values = [device_list[udid][3]+"("+device_list[udid][2]+")" for udid in device_list]
        self.device_combobox["values"] = values
        if len(values) > 0:
            self.device_combobox.current(0)

    def get_selected_device(self) -> Device:
        device_name = self.device_combobox.get()
        if device_name == '':
            raise Exception("请先选择连接的设备")

        udid = self.find_device_udid(device_name)
        d = self.udid2device(udid)
        return d

    def launch_app(self):
        try:
            d = self.get_selected_device()
        except Exception as e:
            alert(e)
            return

        bunde_id = self.bunde_entry.get()
        if bunde_id == '':
            alert("请输入应用BundleID")
            return

        env = {}
        launch_args = ['-FIRAnalyticsDebugEnabled', '-FIRDebugEnabled']
        try:
            with d.connect_instruments() as ts:
                pid = ts.app_launch(bunde_id,
                                    app_env=env,
                                    args=launch_args,
                                    kill_running=False)
                print("PID:", pid)
        except Exception as e:
            alert(e)

    def toggle_syslog(self):
        if self.syslog_service:
            self.syslog_button.config(text="打开实时日志")
            self.syslog_service.close()
        else:
            self.syslog_button.config(text="关闭实时日志")
            thread = threading.Thread(target=self.sys_log)
            thread.start()

    def sys_log(self):
        try:
            d = self.get_selected_device()
        except Exception as e:
            alert(e)
            return

        self.syslog_service = d.start_service("com.apple.syslog_relay")
        try:
            while not self.syslog_service.closed:
                text = self.syslog_service.psock.recv().decode('utf-8')
                text = text.replace('\x00', '')
                self.syslog_queue.put(text)

                # return
            self.syslog_service = None
        except (BrokenPipeError, IOError):
            self.syslog_service = None

    def check_queue(self):
        while not self.syslog_queue.empty():
            line = self.syslog_queue.get()
            print(line)
            self.syslog_text.insert(tkinter.END, line)
            self.syslog_text.see(tkinter.END)

        self.root.after(50, self.check_queue)

    def show(self):
        root = tkinter.Tk()
        self.set_win(root, 'iOS调试工具', 800, 480)
        # root.configure(bg='white')

        row = 1
        device_label = Label(root, text="设备：")
        device_label.grid(row=row, column=1, sticky=tkinter.E)
        self.device_combobox = ttk.Combobox(root, state="readonly")
        self.device_combobox.grid(row=row, column=3, columnspan=2, sticky=tkinter.W)
        self.update_combobox_data()
        self.device_combobox.bind("<Button-1>", self.update_combobox_data)

        row += 2
        bundle_label = Label(root, text="应用BundleID：")
        bundle_label.grid(row=row, column=1, sticky=tkinter.E)
        self.bunde_entry = Entry(root)
        self.bunde_entry.grid(row=row, column=3, rowspan=2, sticky=tkinter.W)

        row += 2
        launch_button = Button(root, text="调试", command=self.launch_app, width=10)
        launch_button.grid(row=row, column=3, sticky=tkinter.W)

        row += 2
        yscrollbar = Scrollbar(root)
        yscrollbar.grid(row=row, column=6, rowspan=7, sticky="nsw")
        xscrollbar = Scrollbar(root, orient=HORIZONTAL)
        xscrollbar.grid(row=row+7, column=1, columnspan=5, sticky="sew")
        self.syslog_text = Text(root, xscrollcommand=xscrollbar.set, yscrollcommand=yscrollbar.set, wrap=NONE)
        self.syslog_text.grid(row=row, column=1, rowspan=7, columnspan=5, sticky="nesw")
        yscrollbar.config(command=self.syslog_text.yview)
        xscrollbar.config(command=self.syslog_text.xview)

        row += 8
        self.syslog_button = Button(root, text="打开实时日志", command=self.toggle_syslog)
        self.syslog_button.grid(row=row, column=3, sticky=tkinter.W)


        for i in range(7):
            root.columnconfigure(i, weight=1)

        self.root = root
        self.root.after(100, self.check_queue)
        self.root.mainloop()


def main():
    app = FNDeviceDebugApp()
    app.show()


if __name__ == '__main__':
    main()
