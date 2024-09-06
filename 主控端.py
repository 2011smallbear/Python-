import socket
import socketserver
import threading
import tkinter as tk

cmd_port = 9021
normal_port = 8021


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print("[+] 初始化连接：", self.client_address)
        try:
            while True:
                self.data = self.request.recv(1024)
                if not self.data:
                    print("[-] 连接断开或结束")
                    break
                else:
                    print(f"[+] 来自{self.client_address}: {self.data.decode('gbk')}的连接")
        except Exception as e:
            print('[-] 发生错误', self.client_address, "连接断开或结束", e)
        finally:
            self.request.close()


def handle_user_input(clients):
    while True:
        cmd = input("(quit退出>> ").strip()
        if cmd == "quit":
            break
        if len(cmd) == 0:
            continue
        for client in clients:
            try:
                client.sendall(cmd.encode('gbk'))
            except Exception as e:
                print(f"[-] 发送命令失败: {e}")


def start_cmd():
    HOST, PORT = "127.0.0.1", cmd_port
    server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
    clients = []

    def track_clients(server):
        while True:
            client, addr = server.get_request()
            print(f"[+] 新连接：{addr}")
            clients.append(client)
            handler = MyTCPHandler(client, addr, server)
            threading.Thread(target=handler.handle).start()

    server_thread = threading.Thread(target=track_clients, args=(server,))
    server_thread.daemon = True
    server_thread.start()

    input_thread = threading.Thread(target=handle_user_input, args=(clients,))
    input_thread.start()

    input_thread.join()
    server.shutdown()
    server.server_close()


def create_textbox(parent, text, side, width=40, height=20):
    textbox = tk.Text(parent, height=height, width=width, bg='black', fg='green')
    textbox.insert(tk.END, text)
    textbox.config(state=tk.DISABLED)  # 设置文本框为只读

    # 创建滚动条
    scrollbar = tk.Scrollbar(parent, command=textbox.yview)
    textbox.config(yscrollcommand=scrollbar.set)

    # 布局
    textbox.pack(side=side, padx=20, pady=20, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=side, fill=tk.Y)

    return textbox


def add_text(textbox, new_text):
    textbox.config(state=tk.NORMAL)  # 将文本框设置为可编辑
    textbox.insert(tk.END, new_text)  # 插入新文本
    textbox.config(state=tk.DISABLED)  # 再次设置为只读


def start_server(left_textbox, middle_textbox, port=normal_port, host='127.0.0.1'):
    i = 0
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"服务启动于{host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        data = b''
        while True:
            packet = client_socket.recv(4096)  # 分块接收数据
            if not packet:
                break
            data += packet

        if data:
            # 分离消息类型和数据
            try:
                message_parts = data.split(b'|', 1)
                message_type = message_parts[0].decode('utf-8')
                message_data = message_parts[1]

                if message_type == 'screenshot':
                    i += 1
                    print(message_data)
                    screenshot_filename = f'your_screenshot{i}.bmp'
                    with open(screenshot_filename, 'wb') as f:
                        f.write(message_data)
                    add_text(middle_textbox, f"[+] 截图{i}已保存到 {screenshot_filename}")
                elif message_type == 'normal':
                    add_text(left_textbox, message_data.decode('utf-8'))


            except:
                add_text(middle_textbox, '[-] 收到非法数据包')
                add_text(left_textbox, f'[-] 收到非法数据包')


if __name__ == '__main__':
    # 创建主窗口
    root = tk.Tk()
    root.configure(bg='black')  # 设置窗口背景颜色
    root.title("服务器信息显示")
    root.geometry("1200x600+200+200")  # 设置窗口大小

    # 创建左、中、右三个文本框
    frame = tk.Frame(root)
    frame.pack(padx=20, pady=20)

    left_textbox = create_textbox(frame, "普通信息", tk.LEFT, width=80, height=60)
    middle_textbox = create_textbox(frame, "图片保存提示", tk.LEFT, width=80, height=60)

    # 启动服务器
    from threading import Thread

    server_thread = Thread(target=start_server, args=(left_textbox, middle_textbox))
    server_thread.daemon = False
    cmd_thread = Thread(target=start_cmd)
    cmd_thread.daemon = False
    server_thread.start()
    cmd_thread.start()

    # 运行主循环
    root.mainloop()
