from datetime import datetime

import psutil


class SystemInfo:
    def __init__(self):
        self.cpu_info = self.get_cpu_info()
        self.memory_info = self.get_memory_info()
        self.disk_info = self.get_disk_info()
        self.network_info = self.get_network_info()
        self.boot_time = self.get_boot_time()

    def get_size(self, bytes, suffix="B"):
        """
        将字节数转换为合适的格式，例如：
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < factor:
                return f"{bytes:.2f}{unit}{suffix}"
            bytes /= factor

    def get_cpu_info(self):
        cpu_info = {
            "物理核心数": psutil.cpu_count(logical=False),
            "逻辑核心数": psutil.cpu_count(logical=True),
            "最大频率": f"{psutil.cpu_freq().max:.2f}MHz",
            "最小频率": f"{psutil.cpu_freq().min:.2f}MHz",
            "当前频率": f"{psutil.cpu_freq().current:.2f}MHz"
        }
        return cpu_info

    def get_memory_info(self):
        svmem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        memory_info = {
            "总内存": self.get_size(svmem.total),
            "可用内存": self.get_size(svmem.available),
            "已用内存": self.get_size(svmem.used),
            "内存使用率": f"{svmem.percent}%",
            "交换分区总内存": self.get_size(swap.total),
            "交换分区可用内存": self.get_size(swap.free),
            "交换分区已用内存": self.get_size(swap.used),
            "交换分区使用率": f"{swap.percent}%"
        }
        return memory_info

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

        if_addrs = psutil.net_if_addrs()
        for interface_name, interface_addresses in if_addrs.items():
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

    def get_boot_time(self):
        boot_time_timestamp = psutil.boot_time()
        bt = datetime.fromtimestamp(boot_time_timestamp)
        boot_time_str = f"{bt.year}年{bt.month}月{bt.day}日 {bt.hour}时{bt.minute}分{bt.second}秒"
        return boot_time_str

    def display_info(self):
        print("=" * 40, "CPU 信息", "=" * 40)
        for key, value in self.cpu_info.items():
            print(f"{key}: {value}")

        print("=" * 40, "内存信息", "=" * 40)
        for key, value in self.memory_info.items():
            print(f"{key}: {value}")

        print("=" * 40, "磁盘信息", "=" * 40)
        for key, values in self.disk_info.items():
            if isinstance(values, list):
                for i, value in enumerate(values):
                    print(f"{5 * ' '}{key}: {value}")
            else:
                print(f"{key}: {values}")

        print("=" * 40, "网络信息", "=" * 40)
        for key, values in self.network_info.items():
            if isinstance(values, list):
                for i, value in enumerate(values):
                    print(f"{5 * ' '}{key}: {value}")
            else:
                print(f"{key}: {values}")

        print("=" * 40, "系统引导时间", "=" * 40)
        print(f"引导时间: {self.boot_time}")


if __name__ == "__main__":
    sys_info = SystemInfo()
    sys_info.display_info()
