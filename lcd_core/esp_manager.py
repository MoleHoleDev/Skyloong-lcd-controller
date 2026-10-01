import os
import sys
import subprocess
import socket
import psutil
import tempfile
from typing import List, Tuple, Dict, Optional

class ESPManager:
    """
    Manages Skyloong GK104 Pro LCD Screen ESP32 hardware via USB/Serial.
    Handles LittleFS WiFi/IP configuration injection, NVS reset, rebooting, and network IP detection.
    """

    @staticmethod
    def get_pc_network_ips() -> List[Dict[str, str]]:
        """Returns all non-loopback IPv4 addresses of this machine with interface metadata."""
        ips = []
        try:
            for iface_name, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                        if_type = "Wi-Fi" if iface_name.startswith(("wl", "wlan", "wifi")) else (
                            "Ethernet" if iface_name.startswith(("eth", "en", "lan")) else "Inne"
                        )
                        ips.append({
                            "iface": iface_name,
                            "ip": addr.address,
                            "netmask": addr.netmask or "",
                            "type": if_type
                        })
        except Exception:
            pass

        # Fallback using socket connect probe
        if not ips:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                ips.append({"iface": "default", "ip": ip, "netmask": "", "type": "Domyślny"})
            except Exception:
                pass
        return ips

    @staticmethod
    def get_active_system_wifi() -> Tuple[Optional[str], Optional[str]]:
        """
        Auto-detects active Wi-Fi connection SSID and PSK password from NetworkManager.
        Returns (ssid, password) or (None, None).
        """
        ssid = None
        password = None

        # Try nmcli active connections
        try:
            out = subprocess.check_output(
                ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"],
                text=True, stderr=subprocess.DEVNULL, timeout=5
            )
            for line in out.strip().splitlines():
                parts = line.split(":")
                if len(parts) >= 2 and "wireless" in parts[1].lower():
                    ssid = parts[0]
                    break
        except Exception:
            pass

        # Try iwgetid if nmcli didn't find SSID
        if not ssid:
            try:
                out = subprocess.check_output(["iwgetid", "-r"], text=True, stderr=subprocess.DEVNULL, timeout=3)
                if out.strip():
                    ssid = out.strip()
            except Exception:
                pass

        # Get password for SSID using nmcli
        if ssid:
            try:
                pw_out = subprocess.check_output(
                    ["nmcli", "-s", "-g", "802-11-wireless-security.psk", "connection", "show", ssid],
                    text=True, stderr=subprocess.DEVNULL, timeout=5
                )
                if pw_out.strip():
                    password = pw_out.strip()
            except Exception:
                pass

        return ssid, password

    @staticmethod
    def write_wifi_and_ip_to_esp32(port: str, ssid: str, password: str, pc_ip: str, nickname: str = "PC") -> Tuple[bool, str]:
        """
        Writes .wifi.csv and .cfg.bin into the LittleFS partition at 0x820000 on the ESP32.
        This directly configures Wi-Fi credentials and PC Server IP without requiring AP mode / QR codes.
        """
        if not os.path.exists(port):
            return False, f"Port {port} nie istnieje. Podłącz ekranik kablem USB-C do komputera."

        if not ssid:
            return False, "Nazwa sieci Wi-Fi (SSID) nie może być pusta."

        try:
            from littlefs import LittleFS
        except ImportError:
            return False, "Brak biblioteki littlefs-python. Zainstaluj: pip install littlefs-python"

        tmp_in = tempfile.mktemp(suffix=".bin")
        tmp_out = tempfile.mktemp(suffix=".bin")

        try:
            # 1. Read first 64KB (16 blocks of 4096 bytes) containing LittleFS superblock and root directory
            cmd_read = [
                sys.executable, "-m", "esptool",
                "--port", port,
                "--chip", "esp32s3",
                "read-flash", "0x820000", "0x10000", tmp_in
            ]
            res_read = subprocess.run(cmd_read, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=25)
            if res_read.returncode != 0:
                # Retry without chip flag
                cmd_read_alt = [
                    sys.executable, "-m", "esptool",
                    "--port", port,
                    "read-flash", "0x820000", "0x10000", tmp_in
                ]
                res_read = subprocess.run(cmd_read_alt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=25)
                if res_read.returncode != 0:
                    return False, f"Błąd odczytu flash: {res_read.stderr.strip() or res_read.stdout.strip()}"

            with open(tmp_in, "rb") as f:
                raw_bytes = bytearray(f.read())

            fs = LittleFS(block_size=4096, block_count=2000)
            full_buf = raw_bytes + bytearray(b"\xff" * (2000 * 4096 - len(raw_bytes)))
            fs.context.buffer = full_buf
            
            try:
                fs.mount()
            except Exception:
                # If filesystem is empty/unformatted, format it
                fs.format()
                fs.mount()

            # Update .wifi.csv
            wifi_content = f"{ssid},{password}\n"
            with fs.open(".wifi.csv", "w") as f:
                f.write(wifi_content)

            # Update .cfg.bin (Format: [0..63]: IP, [64..127]: SoC/Port, [128..191]: City, [192..255]: Nickname)
            try:
                with fs.open(".cfg.bin", "rb") as f:
                    cfg = bytearray(f.read())
            except Exception:
                cfg = bytearray(256)

            if len(cfg) < 256:
                cfg += bytearray(256 - len(cfg))

            # Set PC IP
            ip_str = pc_ip.strip() if pc_ip else "192.168.1.1"
            ip_bytes = ip_str.encode("ascii") + b"\x00"
            cfg[:len(ip_bytes)] = ip_bytes
            for i in range(len(ip_bytes), 64):
                cfg[i] = 0

            # Set Nickname
            if nickname:
                nick_bytes = nickname.encode("utf-8")[:63] + b"\x00"
                cfg[192:192+len(nick_bytes)] = nick_bytes
                for i in range(192+len(nick_bytes), 256):
                    cfg[i] = 0

            with fs.open(".cfg.bin", "wb") as f:
                f.write(cfg)

            fs.unmount()

            # Save modified 64KB
            with open(tmp_out, "wb") as f:
                f.write(fs.context.buffer[:0x10000])

            # 2. Flash modified 64KB back to ESP32
            cmd_write = [
                sys.executable, "-m", "esptool",
                "--port", port,
                "--chip", "esp32s3",
                "write-flash", "0x820000", tmp_out
            ]
            res_write = subprocess.run(cmd_write, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=25)
            if res_write.returncode != 0:
                cmd_write_alt = [
                    sys.executable, "-m", "esptool",
                    "--port", port,
                    "write-flash", "0x820000", tmp_out
                ]
                res_write = subprocess.run(cmd_write_alt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=25)
                if res_write.returncode != 0:
                    return False, f"Błąd zapisu flash: {res_write.stderr.strip() or res_write.stdout.strip()}"

            # 3. Reboot the ESP32 module
            ESPManager.reboot_esp32(port)

            return True, f"Pomyślnie wgrano sieć Wi-Fi „{ssid}” oraz IP {pc_ip} do pamięci ekranu! Moduł został zrestartowany."
        except Exception as e:
            return False, f"Wystąpił błąd podczas wgrywania: {str(e)}"
        finally:
            if os.path.exists(tmp_in):
                try: os.remove(tmp_in)
                except Exception: pass
            if os.path.exists(tmp_out):
                try: os.remove(tmp_out)
                except Exception: pass

    @staticmethod
    def reset_esp32_nvs_wifi(port: str) -> Tuple[bool, str]:
        """
        Erases NVS and LittleFS wifi configuration to force AP mode and display QR code.
        """
        if not os.path.exists(port):
            return False, f"Port {port} nie istnieje. Upewnij się, że ekran jest podłączony kablem USB-C."

        try:
            # 1. Erase NVS partition (0x9000, 0x6000)
            cmd_nvs = [
                sys.executable, "-m", "esptool",
                "--port", port,
                "--chip", "esp32s3",
                "erase-region", "0x9000", "0x6000"
            ]
            subprocess.run(cmd_nvs, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)

            # 2. Erase LittleFS partition (0x820000, 0x7D0000)
            cmd_lfs = [
                sys.executable, "-m", "esptool",
                "--port", port,
                "--chip", "esp32s3",
                "erase-region", "0x820000", "0x7d0000"
            ]
            subprocess.run(cmd_lfs, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25)

            # 3. Format clean LittleFS without .wifi.csv
            try:
                from littlefs import LittleFS
                fs = LittleFS(block_size=4096, block_count=2000)
                fs.format()
                tmp_lfs = tempfile.mktemp(suffix=".bin")
                with open(tmp_lfs, "wb") as f:
                    f.write(fs.context.buffer)
                subprocess.run([
                    sys.executable, "-m", "esptool",
                    "--port", port,
                    "--chip", "esp32s3",
                    "write-flash", "0x820000", tmp_lfs
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25)
                if os.path.exists(tmp_lfs):
                    os.remove(tmp_lfs)
            except Exception:
                pass

            # 4. Reboot ESP32
            ESPManager.reboot_esp32(port)
            return True, "Pomyślnie zresetowano moduł Wi-Fi do trybu rozgłaszania AP z kodem QR!"
        except Exception as e:
            return False, f"Błąd resetu Wi-Fi: {str(e)}"

    @staticmethod
    def reboot_esp32(port: str) -> Tuple[bool, str]:
        """Restarts the ESP32 screen module via USB."""
        if not os.path.exists(port):
            return False, f"Port {port} nie istnieje."

        try:
            import serial
            ser = serial.Serial(port, 115200, timeout=1)
            ser.dtr = False
            ser.rts = True
            ser.dtr = True
            ser.rts = False
            ser.close()
            return True, "Wysłano sygnał restartu do modułu ESP32."
        except Exception as e:
            return False, f"Nie udało się zrestartować modułu: {e}"
