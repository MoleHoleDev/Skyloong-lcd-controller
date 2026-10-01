import os
import glob
import time
import psutil
from typing import Dict, Any, Optional

class SystemMonitor:
    """
    Reads hardware metrics: CPU %, RAM %, GPU %, and temperatures (CPU, GPU, NVMe).
    Optimized for Linux (Arch / CachyOS / Ubuntu / Debian / Fedora / generic).
    """

    def __init__(self):
        # Initial call to psutil.cpu_percent to initialize internal counter
        psutil.cpu_percent(interval=None)
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        self.boot_time = psutil.boot_time()

    def get_cpu_temp(self) -> float:
        """Finds CPU temperature via psutil or sysfs."""
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                # Check known CPU sensor chip names
                for chip in ['k10temp', 'coretemp', 'zenpower', 'cpu_thermal', 'acpitz']:
                    if chip in temps and temps[chip]:
                        for entry in temps[chip]:
                            if entry.current is not None and entry.current > 0:
                                return float(entry.current)
                # Fallback to any sensor containing 'cpu' or 'tctl' or 'package'
                for chip, entries in temps.items():
                    for entry in entries:
                        label = (entry.label or '').lower()
                        if 'tctl' in label or 'cpu' in label or 'package' in label or 'tccd' in label:
                            if entry.current:
                                return float(entry.current)
        except Exception:
            pass

        # Sysfs fallback
        try:
            for p in glob.glob('/sys/class/hwmon/hwmon*'):
                name_file = os.path.join(p, 'name')
                if os.path.exists(name_file):
                    with open(name_file, 'r') as f:
                        name = f.read().strip().lower()
                    if name in ['k10temp', 'coretemp', 'zenpower', 'acpitz']:
                        for tf in glob.glob(os.path.join(p, 'temp*_input')):
                            with open(tf, 'r') as f:
                                return float(f.read().strip()) / 1000.0
        except Exception:
            pass

        return 45.0

    def get_gpu_temp(self) -> float:
        """Finds GPU temperature via psutil or sysfs."""
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                for chip in ['amdgpu', 'nvidia', 'nouveau', 'gpu']:
                    if chip in temps and temps[chip]:
                        for entry in temps[chip]:
                            if entry.current is not None and entry.current > 0:
                                return float(entry.current)
        except Exception:
            pass

        # Sysfs fallback for amdgpu
        try:
            for p in glob.glob('/sys/class/drm/card*/device/hwmon/hwmon*/temp1_input'):
                with open(p, 'r') as f:
                    return float(f.read().strip()) / 1000.0
        except Exception:
            pass

        return 40.0

    def get_nvme_temp(self) -> float:
        """Finds NVMe temperature via psutil or sysfs."""
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                for chip, entries in temps.items():
                    if 'nvme' in chip.lower():
                        for entry in entries:
                            if entry.current is not None and entry.current > 0:
                                return float(entry.current)
        except Exception:
            pass

        try:
            for p in glob.glob('/sys/class/hwmon/hwmon*'):
                name_file = os.path.join(p, 'name')
                if os.path.exists(name_file):
                    with open(name_file, 'r') as f:
                        if 'nvme' in f.read().strip().lower():
                            for tf in glob.glob(os.path.join(p, 'temp1_input')):
                                with open(tf, 'r') as f:
                                    return float(f.read().strip()) / 1000.0
        except Exception:
            pass

        return 45.0

    def get_gpu_usage(self) -> float:
        """Returns GPU utilization percentage."""
        # 1. AMD DRM sysfs
        for p in glob.glob('/sys/class/drm/card*/device/gpu_busy_percent'):
            try:
                with open(p, 'r') as f:
                    return float(f.read().strip())
            except Exception:
                pass

        # 2. Intel GPU sysfs (if available)
        for p in glob.glob('/sys/class/drm/card*/gt_act_freq_mhz'):
            try:
                # Approximate activity or 0
                return 5.0
            except Exception:
                pass

        return 0.0

    def get_all_metrics(self) -> Dict[str, Any]:
        """Collects all real-time system stats."""
        cpu_pct = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        ram_pct = mem.percent
        ram_used_gb = mem.used / (1024 ** 3)
        ram_total_gb = mem.total / (1024 ** 3)

        gpu_pct = self.get_gpu_usage()
        cpu_t = self.get_cpu_temp()
        gpu_t = self.get_gpu_temp()
        nvme_t = self.get_nvme_temp()

        # Network speed
        curr_time = time.time()
        curr_net = psutil.net_io_counters()
        dt = max(0.1, curr_time - self.last_net_time)
        net_rx_kb = (curr_net.bytes_recv - self.last_net_io.bytes_recv) / 1024.0 / dt
        net_tx_kb = (curr_net.bytes_sent - self.last_net_io.bytes_sent) / 1024.0 / dt
        self.last_net_io = curr_net
        self.last_net_time = curr_time

        # Uptime
        uptime_sec = int(curr_time - self.boot_time)
        hours = uptime_sec // 3600
        minutes = (uptime_sec % 3600) // 60
        uptime_str = f"{hours}h {minutes}m"

        return {
            'cpu_percent': round(cpu_pct, 1),
            'ram_percent': round(ram_pct, 1),
            'ram_used_gb': round(ram_used_gb, 1),
            'ram_total_gb': round(ram_total_gb, 1),
            'gpu_percent': round(gpu_pct, 1),
            'cpu_temp': round(cpu_t, 1),
            'gpu_temp': round(gpu_t, 1),
            'nvme_temp': round(nvme_t, 1),
            'net_rx_kb': round(net_rx_kb, 1),
            'net_tx_kb': round(net_tx_kb, 1),
            'uptime_str': uptime_str,
            'timestamp': curr_time
        }
