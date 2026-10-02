# Skyloong GK104 Pro — USB LCD Frame Streamer & Custom Firmware

Kompletne, niezależne oprogramowanie i firmware dla modułu ekranu LCD klawiatury **Skyloong GK104 Pro (ESP32-S3 + ST7789)** umożliwiające **100% bezpośrednie strumieniowanie obrazu i telemetrii przez kabel USB (USB CDC Serial)** z prędkością do **60 FPS** bez konieczności dotykania Wi-Fi!

---

## 🚀 Kluczowe Cechy

- **100% USB CDC Streaming:** Brak problemów z konfiguracją Wi-Fi, brak konieczności łączenia z punktem dostępowym czy otwierania portów w routerze.
- **Wysoka Wydajność (do 60 FPS):** Sprzętowo akcelerowany dekoder JPEG (`TJpgDec`) na ESP32-S3 + magistrala SPI DMA 80 MHz do matrycy ST7789.
- **Kompatybilność z Widokami Programu:** Możliwość strumieniowania dowolnych kompozycji z `skyloong-lcd-controller`:
  - 🧩 Hybrydowe widżety (zegar + statystyki + temperatury + tło)
  - 📊 Pełna telemetria (CPU %, RAM %, GPU %, temperatury CPU/GPU/NVMe)
  - 🕒 5 unikalnych stylów zegara (Cyberpunk Neon, Modern, Retro LCD, itd.)
  - 📅 Widok kalendarza
  - 🖼️ Zdjęcia i tapety
  - 🎞️ Animowane GIFy i wideo
  - 📋 Pokaz slajdów
- **Sprzętowe sterowanie ekranem:** Płynna regulacja jasności PWM (0-100%) oraz wygaszanie/włączanie ekranu przez USB.
- **Dwa tryby użycia:**
  1. Graficzny panel w aplikacji `skyloong-lcd-controller` (zakładka `⚡ USB Stream`).
  2. Samodzielny skrypt CLI `usb_streamer_cli.py` (idealny do pracy w tle lub na serwerach).

---

## 📁 Zawartość Podfolderu

```
usb_stream_firmware/
├── platformio.ini         # Konfiguracja kompilacji PlatformIO dla ESP32-S3
├── src/
│   └── main.cpp           # Źródło firmware ESP32-S3 (sterownik ST7789, DMA, JPEG dekoder, USB CDC)
├── bin/                   # Gotowe, skompilowane pliki binarne do natychmiastowego wgrania
│   ├── bootloader.bin     # Bootloader ESP-IDF (offset 0x0)
│   ├── partitions.bin     # Tabela partycji (offset 0x8000)
│   └── firmware.bin       # Główny wsad USB Streamera (offset 0x10000)
├── flash_firmware.py      # Automatyczny skrypt wgrywający wsad przez esptool (1-klik)
├── build_and_flash.sh     # Skrypt kompilujący i wgrywający wsad
├── usb_streamer_cli.py    # Samodzielny program CLI do streamowania z konsoli
└── README.md              # Niniejsza dokumentacja
```

---

## ⚡ Wgrywanie Firmware do Modułu Ekranu (1-Klik)

### Metoda A: Z poziomu aplikacji graficznej
1. Uruchom program:
   ```bash
   /home/kret/Pulpit/PROJEKTY/skyloong-lcd-controller/run.sh
   ```
2. Przejdź do zakładki **⚡ USB Stream**.
3. W sekcji *4. Oprogramowanie USB Streamera* kliknij **⚡ Wgraj firmware USB do modułu (1-klik)**.

### Metoda B: Bezpośrednio ze skryptu w terminalu
Wepnij ekran kablem USB-C do komputera i wykonaj:
```bash
./flash_firmware.py /dev/ttyACM0
```
*(Skrypt automatycznie użyje `esptool` i wgra gotowe pliki binarne z katalogu `bin/` w ciągu kilku sekund).*

---

## 🎮 Uruchomienie Strumieniowania Klatek

### 1. W aplikacji GUI `skyloong-lcd-controller`:
- Wybierz interesujący Cię widok (np. *Do wyboru*, *Zużycie i Temp*, *Zegar*, *GIFy*).
- W zakładce **⚡ USB Stream** kliknij **▶ Rozpocznij Strumieniowanie USB**.
- Ustaw suwakiem docelowy klatkaż (np. **30 FPS** lub **60 FPS**) oraz jasność ekranu.

### 2. Za pomocą samodzielnego narzędzia CLI:
- **Monitoring podzespołów PC (CPU, RAM, Zegar):**
  ```bash
  ./usb_streamer_cli.py --mode system --fps 30
  ```
- **Strumieniowanie animowanego GIF-a:**
  ```bash
  ./usb_streamer_cli.py --mode gif --file /sciezka/do/animacji.gif --fps 30
  ```
- **Wyświetlanie zdjęcia:**
  ```bash
  ./usb_streamer_cli.py --mode image --file /sciezka/do/zdjecia.png
  ```

---

## 🔌 Protokół Komunikacji USB CDC (`SKYL`)

Transmisja odbywa się po wirtualnym porcie szeregowym USB (`/dev/ttyACM0`):

| Bajty | Pole | Opis |
| :--- | :--- | :--- |
| `0..3` | **Magic Header** | `b'SKYL'` (`0x53, 0x4B, 0x59, 0x4C`) |
| `4` | **Command Byte** | `0x01` (Draw JPEG), `0x02` (Draw RAW565), `0x03` (Set Brightness), `0x04` (Ping), `0x05` (Power) |
| `5..8` | **Payload Length** | `uint32_t` (Little-Endian) |
| `9..N` | **Data Payload** | Surowe dane klatki JPEG lub RGB565 |

Po pomyślnym odebraniu i narysowaniu klatki moduł ESP32 odsyła 1-bajtowe potwierdzenie `ACK` (`0x06`).
