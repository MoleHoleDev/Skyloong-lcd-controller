import os
import subprocess
import glob
from typing import Tuple, Optional

UDEV_RULE_PATH = "/etc/udev/rules.d/98-skyloong-screen.rules"

UDEV_RULE_CONTENT = """# Skyloong GK104 Pro LCD Screen (ESP32-S3) & Serial USB rules
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", MODE="0666", GROUP="uucp", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", MODE="0666", GROUP="uucp", TAG+="uaccess"
KERNEL=="ttyACM*", MODE="0666", GROUP="uucp", TAG+="uaccess"
KERNEL=="ttyUSB*", MODE="0666", GROUP="uucp", TAG+="uaccess"
"""

def is_port_accessible(port: str) -> bool:
    """Checks if the serial port exists and has read/write permissions."""
    if not os.path.exists(port):
        return False
    return os.access(port, os.R_OK | os.W_OK)

def fix_usb_permissions(port: Optional[str] = None) -> Tuple[bool, str]:
    """
    Attempts to fix USB permissions automatically by installing permanent udev rules
    and chmodding existing serial device nodes via pkexec (graphical polkit dialog).
    No terminal interaction is required.
    """
    # Build payload to run with root permissions
    username = os.environ.get("USER", "kret")
    
    script_commands = f"""
cat << 'EOF' > {UDEV_RULE_PATH}
{UDEV_RULE_CONTENT}
EOF
chmod 644 {UDEV_RULE_PATH}
usermod -a -G uucp {username} 2>/dev/null || true
chmod 666 /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger 2>/dev/null || true
"""

    try:
        # Check if pkexec is available
        pkexec_path = "/usr/bin/pkexec"
        if not os.path.exists(pkexec_path):
            return False, "Brak narzędzia 'pkexec' w systemie. Wymagana autoryzacja administratora."

        # Execute pkexec which triggers the system GUI password prompt
        cmd = [pkexec_path, "bash", "-c", script_commands]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)

        if res.returncode == 0:
            if port and os.path.exists(port) and is_port_accessible(port):
                return True, f"Pomyślnie odblokowano uprawnienia do portu {port} oraz zainstalowano trwałe reguły udev."
            elif not port:
                return True, "Pomyślnie odblokowano uprawnienia USB i zainstalowano trwałe reguły udev."
            else:
                return True, "Zastosowano uprawnienia. Jeśli port nadal nie działa, podłącz kabel USB ponownie."
        else:
            err_msg = res.stderr.strip() or "Użytkownik anulował autoryzację lub podano błędne hasło."
            return False, f"Autoryzacja nie powiodła się: {err_msg}"
    except subprocess.TimeoutExpired:
        return False, "Upłynął limit czasu oczekiwania na autoryzację administratora."
    except Exception as e:
        return False, f"Błąd podczas nadawania uprawnień: {str(e)}"
