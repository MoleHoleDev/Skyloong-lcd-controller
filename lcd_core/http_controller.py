import io
import time
from typing import Optional, Dict, Any, Tuple, List
import requests
from PIL import Image

class HTTPController:
    """
    Controller for managing Skyloong GK104 Pro LCD module over local Wi-Fi HTTP API.
    Communicates with ESP32 Web Server (endpoints: /info, /config.json, /list, /edit,
    /config_app_jpg, /config_app_sysinfo, /config_app_gif, /config_theme, etc.).
    """

    def __init__(self, screen_ip: str = "192.168.1.115"):
        self.screen_ip = screen_ip.strip()
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "SkyloongController/1.0"})

    def set_ip(self, ip: str):
        self.screen_ip = ip.strip()

    def get_info(self, timeout: float = 3.0) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Fetches /info from the LCD module."""
        if not self.screen_ip:
            return False, None, "Nie podano adresu IP ekranu."
        url = f"http://{self.screen_ip}/info"
        try:
            resp = self._session.get(url, timeout=timeout)
            if resp.status_code == 200:
                return True, resp.json(), "Połączono pomyślnie z ekranem LCD."
            return False, None, f"Serwer zwrócił kod {resp.status_code}"
        except Exception as e:
            return False, None, f"Brak odpowiedzi od {self.screen_ip}: {str(e)}"

    def get_config_json(self, timeout: float = 3.0) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Fetches /config.json from the LCD module."""
        if not self.screen_ip:
            return False, None, "Nie podano adresu IP ekranu."
        url = f"http://{self.screen_ip}/config.json"
        try:
            resp = self._session.get(url, timeout=timeout)
            if resp.status_code == 200:
                return True, resp.json(), "Odczytano konfigurację."
            return False, None, f"Serwer zwrócił kod {resp.status_code}"
        except Exception as e:
            return False, None, f"Błąd odczytu config.json: {str(e)}"

    def set_config_json(self, pc_ip: str, port: int = 1648, weather_key: str = "SoC098cCa8Ih-GWTb",
                        city: str = "Warszawa", userdata: str = "Skyloong Linux", timeout: float = 4.0) -> Tuple[bool, str]:
        """Sets /config.json on the LCD module so it knows where to connect for PC sysinfo."""
        if not self.screen_ip:
            return False, "Nie podano adresu IP ekranu."
        url = f"http://{self.screen_ip}/config.json"
        payload = {
            "ip": pc_ip.strip(),
            "port": int(port),
            "weather": weather_key,
            "city": city,
            "userdata": userdata
        }
        try:
            resp = self._session.post(url, json=payload, timeout=timeout)
            if resp.status_code == 200:
                return True, "Zaktualizowano konfigurację serwera PC na ekranie."
            return False, f"Błąd zapisu config.json: HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Błąd połączenia podczas zapisu config.json: {str(e)}"

    def list_files(self, timeout: float = 4.0) -> Tuple[bool, List[Dict[str, Any]], str]:
        """Lists files on LittleFS (/list?dir=/)."""
        if not self.screen_ip:
            return False, [], "Nie podano adresu IP ekranu."
        url = f"http://{self.screen_ip}/list?dir=/"
        try:
            resp = self._session.get(url, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                return True, data.get("data", []), "Pobrano listę plików."
            return False, [], f"Błąd /list: HTTP {resp.status_code}"
        except Exception as e:
            return False, [], str(e)

    def delete_file(self, filename: str, timeout: float = 4.0) -> Tuple[bool, str]:
        """Deletes a file from LittleFS."""
        if not self.screen_ip:
            return False, "Nie podano adresu IP ekranu."
        clean_name = filename.lstrip("/")
        url = f"http://{self.screen_ip}/edit?filename=/{clean_name}"
        try:
            resp = self._session.delete(url, timeout=timeout)
            if resp.status_code in (200, 204):
                return True, f"Usunięto {clean_name}"
            return False, f"Błąd usuwania: HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)

    def upload_frame(self, pil_image: Image.Image, filename: Optional[str] = None, timeout: float = 8.0) -> Tuple[bool, str]:
        """
        Uploads a rendered PIL image (240x240) to ESP32 LittleFS and activates it immediately.
        Cleans up old uploaded temporary frames to keep storage clean.
        """
        if not self.screen_ip:
            return False, "Nie podano adresu IP ekranu."

        try:
            # Generate unique timestamped filename if none provided
            if not filename:
                filename = f"{int(time.time() * 1000)}.jpg"
            elif not filename.endswith(".jpg") and not filename.endswith(".jpeg"):
                filename = f"{filename}.jpg"

            # Ensure 320x240 RGB
            if pil_image.size != (320, 240):
                pil_image = pil_image.resize((320, 240), Image.Resampling.LANCZOS)
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            # Save to JPEG buffer
            buf = io.BytesIO()
            pil_image.save(buf, format="JPEG", quality=90)
            jpeg_bytes = buf.getvalue()

            # Upload via /edit multipart/form-data
            url = f"http://{self.screen_ip}/edit"
            files = {"data": (filename, jpeg_bytes, "image/jpeg")}
            resp = self._session.post(url, files=files, timeout=timeout)

            if resp.status_code not in (200, 201):
                return False, f"Serwer odrzucił plik (HTTP {resp.status_code})"

            # Switch screen to show this image
            switch_ok, switch_msg = self.switch_to_jpg(filename=filename, timeout=timeout)
            if not switch_ok:
                return False, f"Wgrano plik, ale nie udało się aktywować trybu: {switch_msg}"

            # Async cleanup of older temporary image files in background
            self._cleanup_old_files(keep_filename=filename)

            return True, f"Pomyślnie zaktualizowano widok na ekranie LCD ({filename})!"
        except Exception as e:
            return False, f"Błąd podczas przesyłania widoku: {str(e)}"

    def _cleanup_old_files(self, keep_filename: str):
        """Removes older temporary image files to save LittleFS flash space."""
        try:
            ok, files, _ = self.list_files(timeout=2.0)
            if ok and len(files) > 3:
                # Find older jpg files that are numeric timestamps
                for item in files:
                    name = item.get("name", "")
                    if name != keep_filename and name.endswith(".jpg"):
                        base = name.replace(".jpg", "")
                        if base.isdigit():
                            self.delete_file(name, timeout=2.0)
        except Exception:
            pass

    def switch_to_jpg(self, filename: str, time_roll: int = 5000, mode: str = "fixed", timeout: float = 4.0) -> Tuple[bool, str]:
        """Activates image display mode on ESP32."""
        if not self.screen_ip:
            return False, "Nie podano adresu IP ekranu."
        url = f"http://{self.screen_ip}/config_app_jpg?enable=true&time_roll={time_roll}&jpg_mode={mode}&jpg_file={filename}"
        try:
            # Disable other apps so the screen exclusively displays the picture
            self._session.post(f"http://{self.screen_ip}/config_app_weather?enable=false", timeout=timeout)
            self._session.post(f"http://{self.screen_ip}/config_app_aps?enable=false", timeout=timeout)
            self._session.post(f"http://{self.screen_ip}/config_app_sysinfo?enable=false", timeout=timeout)
            self._session.post(f"http://{self.screen_ip}/config_app_gif?enable=false", timeout=timeout)

            resp = self._session.post(url, timeout=timeout)
            if resp.status_code == 200:
                return True, "Tryb zdjęć aktywny."
            return False, f"Status HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)

    def switch_to_sysinfo(self, pc_ip: Optional[str] = None, port: int = 1648, timeout: float = 4.0) -> Tuple[bool, str]:
        """Activates PC system telemetry mode (CPU/RAM monitor via TCP port 1648)."""
        if not self.screen_ip:
            return False, "Nie podano adresu IP ekranu."

        # If pc_ip is provided, update config.json first
        if pc_ip:
            self.set_config_json(pc_ip=pc_ip, port=port, timeout=timeout)

        url = f"http://{self.screen_ip}/config_app_sysinfo?enable=true"
        try:
            # Disable others
            self._session.post(f"http://{self.screen_ip}/config_app_weather?enable=false", timeout=timeout)
            self._session.post(f"http://{self.screen_ip}/config_app_aps?enable=false", timeout=timeout)
            self._session.post(f"http://{self.screen_ip}/config_app_gif?enable=false", timeout=timeout)
            self._session.post(f"http://{self.screen_ip}/config_app_jpg?enable=false&time_roll=5000&jpg_mode=fixed&jpg_file=", timeout=timeout)

            resp = self._session.post(url, timeout=timeout)
            if resp.status_code == 200:
                return True, "Tryb monitora PC aktywny."
            return False, f"Status HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)

    def switch_theme(self, theme_idx: int = 0, timeout: float = 4.0) -> Tuple[bool, str]:
        """Switches base watchface theme (0, 1, 2)."""
        if not self.screen_ip:
            return False, "Nie podano adresu IP ekranu."
        url = f"http://{self.screen_ip}/config_theme?theme={theme_idx}"
        try:
            resp = self._session.post(url, timeout=timeout)
            if resp.status_code == 200:
                return True, f"Zmieniono motyw na {theme_idx}."
            return False, f"Status HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)

    def switch_to_gif(self, timeout: float = 4.0) -> Tuple[bool, str]:
        """Activates GIF / MPEG video mode."""
        if not self.screen_ip:
            return False, "Nie podano adresu IP ekranu."
        url = f"http://{self.screen_ip}/config_app_gif?enable=true"
        try:
            # Disable others
            self._session.post(f"http://{self.screen_ip}/config_app_weather?enable=false", timeout=timeout)
            self._session.post(f"http://{self.screen_ip}/config_app_aps?enable=false", timeout=timeout)
            self._session.post(f"http://{self.screen_ip}/config_app_sysinfo?enable=false", timeout=timeout)
            self._session.post(f"http://{self.screen_ip}/config_app_jpg?enable=false&time_roll=5000&jpg_mode=fixed&jpg_file=", timeout=timeout)

            resp = self._session.post(url, timeout=timeout)
            if resp.status_code == 200:
                return True, "Tryb GIF/Wideo aktywny."
            return False, f"Status HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)
