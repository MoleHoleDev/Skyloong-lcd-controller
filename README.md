# Skyloong LCD Controller (Linux) 🖥️ 🌈 ⚡

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PySide6 / Qt6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-41CD52.svg?style=flat-square&logo=qt&logoColor=white)](https://pypi.org/project/PySide6/)
[![Platform Linux](https://img.shields.io/badge/platform-Linux%20%7C%20CachyOS%20%7C%20Arch%20%7C%20Ubuntu-FCC624.svg?style=flat-square&logo=linux&logoColor=black)](https://www.kernel.org/)
[![License MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)

Nowoczesna aplikacja graficzna **Python / PySide6 (Qt6)** do kompleksowego zarządzania i wyświetlania treści na wbudowanym 2-calowym ekranie LCD klawiatury **Skyloong GK104 Pro (ESP32-S3)**.

---

## ✨ Kluczowe funkcjonalności

### 1. 🖼️ Zdjęcia (Photos & Images)
- Wgrywanie dowolnych grafik w formatach: `PNG`, `JPG`, `JPEG`, `BMP`, `WebP`, `ICO`.
- Tryby dopasowania do ekranu:
  - **Wypełnij (Cover):** Inteligentne kadrowanie i wypełnienie bez zniekształceń proporcji.
  - **Dopasuj (Contain):** Skalowanie z zachowaniem proporcji (pasy boczne/górne).
  - **Rozciągnij (Stretch):** Dokładne dopasowanie do wymiarów wyświetlacza.
- Płynna korekcja jasności (20% – 200%) oraz kontrastu (20% – 200%).

### 2. 🎞️ Animowane GIFy (GIF Player)
- Obsługa wieloklatkowych animacji `*.gif`.
- Precyzyjna regulacja prędkości odtwarzania w czasie rzeczywistym (od `0.25x` do `3.0x`).
- Płynne zapętlanie z automatyczną optymalizacją klatek do rozdzielczości ekranu.

### 3. 📋 Pokazy slajdów (Slideshows)
- Wygodna kolejka zdjęć (dodawanie wielu plików, usuwanie, czyszczenie).
- Konfigurowalny czas wyświetlania slajdu (od 1 do 300 sekund).
- Opcja losowej kolejności (**Shuffle**).

### 4. 🕒 Zegary (Clocks)
5 unikalnych stylów zegara dopasowanych do każdego setupu:
- 🚀 **Cyberpunk Neon:** Pasek upływu sekund, dynamiczna data, styl sci-fi, wskaźnik statusu.
- ⏱️ **Cyfrowy Modern:** Duże, wyraziste cyfry o wysokim kontraście.
- 📟 **Retro Zielony LCD:** Klasyczny wygląd 7-segmentowego wyświetlacza ciekłokrystalicznego.
- 🔲 **Minimalistyczny:** Nowoczesna typografia w orientacji pionowej.
- 🕒 **Klasyczny Analogowy:** Cyferblat ze wskazówką godzinową, minutową i płynną sekundową.
- Wybór koloru akcentu: *Cyjan, Magenta, Szmaragdowy Matrix, Amber Gold, Czerwień, Biel*.

### 5. 📅 Kalendarz (Calendar)
- Pełny widok bieżącego miesiąca z wyróżnieniem dzisiejszego dnia.
- Oznaczenie dni roboczych oraz weekendów (Sobota, Niedziela).
- Wskaźnik numeru tygodnia wg standardu ISO.
- Opcjonalny mini-zegar cyfrowy w nagłówku.

### 6. 📊 Monitor Zużycia Zasobów (Performance & Usage)
- **CPU:** Precyzyjne obciążenie procesora (% per-core / ogólne).
- **RAM:** Zużycie pamięci operacyjnej w procentach i gigabajtach (`GB used / total`).
- **GPU:** Obciążenie karty graficznej (autodetekcja układów AMD Radeon / NVIDIA / Intel).
- **Sieć:** Prędkość pobierania (▼ RX) i wysyłania (▲ TX) w czasie rzeczywistym.
- Style wizualizacji: *Pierścienie Neon (Rings)* lub *Paski telemetryczne (Bars)*.

### 7. 🌡️ Monitor Temperatur Sprzętu (Hardware Thermals)
- **CPU Temp (°C):** Odczyt z czujników `k10temp`, `coretemp`, `zenpower`, `acpitz`.
- **GPU Temp (°C):** Odczyt z sensorów `amdgpu`, `nvidia`, `nouveau`.
- **NVMe SSD Temp (°C):** Odczyt z kontrolerów dysków półprzewodnikowych PCIe/NVMe.
- Trzypoziomowe kolorowanie stanu cieplnego:
  - 🟢 **Chłodny (<55°C):** Szmaragdowa zieleń.
  - 🟡 **Ciepły (55°C - 75°C):** Bursztyn / Pomarańcz.
  - 🔴 **Gorący (>75°C / Alarm):** Czerwień / Karmazyn.
- Możliwość dostosowania własnych progów ostrzegawczych w zakładce Zużycie/Temp.

### 8. 🧩 Panel Hybrydowy "Do wyboru" (Custom Multi-Widget Dashboard)
Elastyczny ekran pozwalający na skomponowanie własnego układu:
- [x] Kompaktowy zegar cyfrowy i data na górze
- [x] Pasek obciążenia procesora CPU (%)
- [x] Pasek obciążenia pamięci RAM (%)
- [x] Pasek obciążenia karty graficznej GPU (%)
- [x] Kafelki temperatur CPU, GPU i NVMe SSD (°C)
- [x] Wskaźnik transferu sieci
- **Wybór tła:** Ciemny gradient Cyberpunk, Czysta czerń OLED lub **własne zdjęcie/grafika w tle**!

---

## 🖥️ Podgląd na żywo & Komunikacja ze sprzętem

1. **Wirtualny podgląd LCD (Live Preview):**
   - Symulacja fizycznego ekranu klawiatury w czasie rzeczywistym (~30 FPS).
   - Przycisk zrzutu ekranu (**📸 Zrzut ekranu**) do zapisu wygenerowanej klatki.
2. **Serwer Telemetrii TCP (Wi-Fi):**
   - Kompatybilny z fabrycznym firmware Skyloong GK104 Pro (port `1648`).
   - Automatyczna transmisja pakietów telemetrycznych do ekranu po Wi-Fi.
3. **Połączenie USB-C (Serial CDC):**
   - Autodetekcja portów `/dev/ttyACM*` oraz `/dev/ttyUSB*`.
4. **Zasobnik systemowy (System Tray):**
   - Minimalizacja do paska zadań.
   - Tryb demona w tle (`--daemon`).

---

## 🚀 Szybki start i instalacja

### 1. Wymagania systemowe
- System Linux (CachyOS, Arch Linux, Ubuntu, Debian, Fedora, openSUSE)
- Python 3.10+
- Pakiety: `PySide6`, `psutil`, `Pillow`, `pyserial`

### 2. Uruchomienie aplikacji

```bash
# Wejdź do katalogu projektu
cd /home/kret/Pulpit/PROJEKTY/skyloong-lcd-controller

# Uruchom program
./run.sh
```

lub bezpośrednio przez Pythona:

```bash
python3 main.py
```

### 3. Uruchomienie w tle (tryb demona / autostart)

```bash
./run.sh --daemon
```

---

## 📁 Struktura projektu

```
skyloong-lcd-controller/
├── main.py                     # Główny punkt wejściowy aplikacji
├── run.sh                      # Skrypt uruchomieniowy
├── requirements.txt            # Zależności Python
├── README.md                   # Dokumentacja projektu
├── lcd_core/
│   ├── system_monitor.py       # Odczyt parametrów CPU, RAM, GPU i temperatur
│   ├── screen_renderer.py      # Silnik renderowania klatek (8 trybów)
│   ├── config_manager.py       # Zarządzanie ustawieniami (~/.config/skyloong_lcd/)
│   ├── network_server.py       # Serwer TCP telemetrii (port 1648)
│   └── serial_controller.py    # Komunikacja USB-C / Serial CDC
└── ui/
    ├── main_window.py          # Główne okno aplikacji PySide6
    ├── theme.py                # Motyw graficzny Dark Cyberpunk QSS
    └── widgets/
        ├── lcd_preview.py      # Wirtualny podgląd ekranu LCD 240x240
        ├── image_tab.py        # Zakładka zdjęć i filtrów
        ├── gif_tab.py          # Zakładka odtwarzacza GIF
        ├── slideshow_tab.py    # Zakładka pokazu slajdów
        ├── clock_tab.py        # Zakładka zegarów i stylów
        ├── calendar_tab.py     # Zakładka kalendarza
        ├── system_tab.py       # Zakładka zużycia i temperatur
        ├── custom_tab.py       # Zakładka "Do wyboru" (panel hybrydowy)
        └── settings_tab.py     # Zakładka ustawień sieci i połączeń
```

---

## 📜 Licencja

Projekt objęty licencją **MIT**.
