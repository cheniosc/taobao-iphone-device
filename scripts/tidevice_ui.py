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
from tidevice._relay import relay
import threading, multiprocessing, queue, socket, time
import requests


def alert(message):
    tkinter.messagebox.showinfo("", message)


class FNDeviceDebugApp:
    def __init__(self):
        self.root = None
        self.um = Usbmux()
        self.device_combobox: ttk.Combobox = None
        self.bundle_combobox: ttk.Combobox = None
        self.syslog_text: Text = None
        self.syslog_button: Button = None
        self.syslog_service = None
        self.syslog_queue = queue.Queue()
        self.syslog_filter_entry: Entry = None
        self.wda_process = None
        self.mjpeg_process = None


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

    def get_app_infos(self):
        try:
            d = self.get_selected_device()
        except Exception:
            return {}
        app_type = "User"
        app_infos = {}
        for info in d.installation.iter_installed(app_type=app_type):
            bundle_id = info['CFBundleIdentifier']
            app_infos[bundle_id] = [info['CFBundleDisplayName'], bundle_id]
        return app_infos

    def update_bundle_data(self, Event=None):
        # 大概位置是在下拉箭头的区域
        if Event.x < self.bundle_combobox.winfo_width() - 30:
            return
        app_infos = self.get_app_infos()
        values = [app_infos[bundle_id][0]+" "+app_infos[bundle_id][1] for bundle_id in app_infos]
        self.bundle_combobox["values"] = values

    def get_selected_device(self) -> Device:
        device_name = self.device_combobox.get()
        if device_name == '':
            raise Exception("请先选择连接的设备")

        udid = self.find_device_udid(device_name)
        d = self.udid2device(udid)
        return d

    def get_selected_bundleid(self):
        bundle = self.bundle_combobox.get()
        app_infos = self.get_app_infos()
        for bundle_id in app_infos:
            if app_infos[bundle_id][0]+" "+app_infos[bundle_id][1] == bundle:
                return bundle_id

        return bundle

    def show_entitlements(self):
        try:
            d = self.get_selected_device()
        except Exception as e:
            alert(e)
            return

        bunde_id = self.get_selected_bundleid()
        if bunde_id == '':
            alert("请输入应用BundleID")
            return

        info = d.installation.lookup(bunde_id)
        if info is None and 'Entitlements' not in info:
            alert("查不到相关权限信息")
            return
        else:
            alert(info['Entitlements'])

    def launch_app(self):
        try:
            d = self.get_selected_device()
        except Exception as e:
            alert(e)
            return

        bunde_id = self.get_selected_bundleid()
        if bunde_id == '':
            alert("请输入应用BundleID")
            return

        ios_version = d.get_value("ProductVersion")
        if ios_version.startswith("17."):
            from pymobiledevice3.remote.utils import get_tunneld_devices
            try:
                rsds = get_tunneld_devices()
            except Exception as e:
                alert("请先管理员权限运行create_ipv6_tunnel")
                return

            for rsd in rsds:
                if rsd.udid == d.udid:
                    self.launch_app_by_rsd(rsd, bunde_id)
                    break

            # 通过wda的方式启动iOS 17的程序
            # thread = threading.Thread(target=self.launch_app_by_wda, args=(bunde_id,))
            # thread.start()
            return

        env = {}
        launch_args = ['-FIRAnalyticsDebugEnabled', '-FIRDebugEnabled', '-FIRAnalyticsVerboseLoggingEnabled']
        try:
            with d.connect_instruments() as ts:
                pid = ts.app_launch(bunde_id,
                                    app_env=env,
                                    args=launch_args)
                print("PID:", pid)
        except Exception as e:
            alert(e)

    def launch_app_by_rsd(self, rsd, bundle_id):
        from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
        from pymobiledevice3.services.dvt.instruments.process_control import ProcessControl
        dvt = DvtSecureSocketProxyService(rsd)
        dvt.perform_handshake()
        process_control = ProcessControl(dvt)
        launch_args = ['-FIRAnalyticsDebugEnabled', '-FIRDebugEnabled', '-FIRAnalyticsVerboseLoggingEnabled']
        try:
            result = process_control.launch(bundle_id, launch_args, True)
            print(result)
        except Exception as e:
            alert(e)
        dvt.close()

    def launch_app_by_wda(self, bundle_id):
        data = {
            "capabilities": {
                "alwaysMatch": {
                    "appium:bundleId": bundle_id,
                    "appium:arguments": ["-FIRAnalyticsDebugEnabled", "-FIRDebugEnabled",
                                         '-FIRAnalyticsVerboseLoggingEnabled'],
                    "appium:forceAppLaunch": "1",
                    "appium:shouldTerminateApp": "0",
                }
            }
        }
        try:
            res = requests.post("http://localhost:8100/session", json=data)
        except Exception as e:
            print(e)
            alert("检查是否开启端口代理，是否开启手机的WebDriverAgent")
            return
        if res.status_code == 200:
            # time.sleep(5)
            requests.get("http://localhost:8100/wda/shutdown")
        else:
            alert(res.text)


    def relay_port(self):
        try:
            d = self.get_selected_device()
        except Exception as e:
            alert(e)
            return

        if self.wda_process and self.wda_process.is_alive():
            self.wda_process.terminate()
        if self.mjpeg_process and self.mjpeg_process.is_alive():
            self.mjpeg_process.terminate()
        self.wda_process = multiprocessing.Process(target=start_proxy, args=(d.udid, 8100, 8100))
        self.wda_process.start()
        self.wda_process = multiprocessing.Process(target=start_proxy, args=(d.udid, 9100, 9100))
        self.wda_process.start()
        alert("开启成功")

    def reset_syslog_button_text(self):
        self.syslog_button.config(text="打开实时日志")

    def toggle_syslog(self):
        if self.syslog_service:
            self.reset_syslog_button_text()
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
                syslog_filter = self.syslog_filter_entry.get()
                if syslog_filter == '' or text.find(syslog_filter) != -1:
                    self.syslog_queue.put(text)

                # return
            self.syslog_service = None
            self.reset_syslog_button_text()
        except (BrokenPipeError, IOError):
            self.syslog_service = None
            self.reset_syslog_button_text()

    def check_queue(self):
        while not self.syslog_queue.empty():
            lines = []
            # 一次填充多个，避免频繁操作Text的insert，导致卡死
            for _ in range(20):
                if not self.syslog_queue.empty():
                    line = self.syslog_queue.get()
                    lines.append(line)
                else:
                    break
            self.syslog_text.insert(tkinter.END, "".join(lines))
            self.syslog_text.see(tkinter.END)

        self.root.after(150, self.check_queue)

    def clear_text(self):
        self.syslog_text.delete(1.0, END)

    def show(self):
        root = tkinter.Tk()
        self.set_win(root, 'iOS调试工具', 800, 480)

        row = 0
        device_label = Label(root, text="设备：")
        device_label.grid(row=row, column=2, sticky=tkinter.E)
        self.device_combobox = ttk.Combobox(root, state="readonly")
        self.update_combobox_data()
        self.device_combobox.grid(row=row, column=3, columnspan=2, sticky=tkinter.W)
        self.device_combobox.bind("<Button-1>", self.update_combobox_data)

        row += 1
        bundle_label = Label(root, text="应用BundleID：")
        bundle_label.grid(row=row, column=2, sticky=tkinter.E)
        self.bundle_combobox = ttk.Combobox(root)
        self.bundle_combobox.grid(row=row, column=3, columnspan=2, sticky=tkinter.W)
        self.bundle_combobox.bind("<Button-1>", self.update_bundle_data)

        row += 1
        entitlement_button = Button(root, text="查看应用权限", command=self.show_entitlements, width=10)
        entitlement_button.grid(row=row, column=2, sticky=E, padx=(0, 5))
        launch_button = Button(root, text="调试", command=self.launch_app, width=10)
        launch_button.grid(row=row, column=3, sticky=tkinter.W)
        proxy_button = Button(root, text="手机端口代理", command=self.relay_port, width=10)
        proxy_button.grid(row=row, column=3, sticky=tkinter.E, padx=(0, 0))


        row += 1
        yscrollbar = Scrollbar(root)
        yscrollbar.grid(row=row, column=6, rowspan=7, sticky="nsw")
        xscrollbar = Scrollbar(root, orient=HORIZONTAL)
        xscrollbar.grid(row=row+7, column=1, columnspan=5, sticky="sew")
        self.syslog_text = Text(root, xscrollcommand=xscrollbar.set, yscrollcommand=yscrollbar.set, wrap=NONE)
        self.syslog_text.grid(row=row, column=1, rowspan=7, columnspan=5, sticky="nesw")
        yscrollbar.config(command=self.syslog_text.yview)
        xscrollbar.config(command=self.syslog_text.xview)

        row += 8
        syslog_filter_label = Label(root, text="日志过滤：", )
        syslog_filter_label.grid(row=row, column=2, sticky=tkinter.E)
        self.syslog_filter_entry = Entry(root)
        self.syslog_filter_entry.grid(row=row, column=3, sticky=tkinter.W)

        row += 1
        clear_text_button = Button(root, text="清除日志", command=self.clear_text, width=10)
        clear_text_button.grid(row=row, column=2, sticky=E, padx=(0, 5))
        self.syslog_button = Button(root, text="打开实时日志", command=self.toggle_syslog, width=10)
        self.syslog_button.grid(row=row, column=3, sticky=W)

        for i in range(7):
            root.columnconfigure(i, weight=1)
        self.root = root
        self.root.after(150, self.check_queue)
        self.root.mainloop()


def start_proxy(udid, lport, rport):
    d = Device(udid=udid)
    relay(d, lport, rport)
    print(f"端口转发，pc:{lport}, iphone:{rport}")


def main():
    multiprocessing.freeze_support()

    app = FNDeviceDebugApp()
    print("本机局域网IP信息：")
    print(socket.gethostbyname_ex(socket.gethostname()))
    app.show()


if __name__ == '__main__':
    main()
