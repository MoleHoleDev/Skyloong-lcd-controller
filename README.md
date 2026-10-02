# ⚡ Skyloong LCD Controller — GK104 Pro Studio (320x240)

Nowoczesna aplikacja graficzna **Python / PySide6 (Qt6)** do kompleksowego zarządzania i bezpośredniego strumieniowania obrazu w czasie rzeczywistym (do **60 FPS przez USB CDC**) na wyświetlacz LCD klawiatury **Skyloong GK104 Pro** (oraz kompatybilnych modułów Skyloong v3.0 z układem ESP32-S3 i rozdzielczością 320x240).

---

## 🚀 Nowy, prosty interfejs dwukolumnowy

Aplikacja została gruntownie przebudowana z myślą o prostocie, maksymalnej wydajności i komforcie użytkowania:

1. **Lewa kolumna (Galeria Ekranów & Podgląd na żywo):**
   - **Wirtualny ekran LCD 320x240:** wierne odwzorowanie fizycznego wyświetlacza z licznikiem FPS, wskaźnikiem aktywnego trybu i przyciskiem zrzutu ekranu (`PNG`).
   - **Katalog interaktywnych kart:** 14 gotowych ekranów z filtrowaniem kategorii (*Wszystkie*, *Kreatywne & HUD*, *Telemetria*, *Czas*, *Media*). Kliknięcie karty natychmiast przełącza widok.
2. **Prawa kolumna (Szczegółowe ustawienia):**
   - Dedykowany, przejrzysty panel konfiguracji dla aktualnie wybranego ekranu.
   - Pasek parametrów strumienia USB: regulacja klatkażu (15 / 30 / 45 / 60 FPS), jakości kompresji JPEG (70–95%) oraz wybór portu `/dev/ttyACM*`.
3. **Pasek globalny:**
   - Przycisk 1-klik: **`🚀 Rozpocznij / ⏹ Zatrzymaj Strumieniowanie USB`**.
   - Suwak natychmiastowej regulacji jasności podświetlenia (`☀️ 10–255`).
   - Narzędzie wgrywania firmware ESP32-S3.

---

## 🎨 Katalog 14 Dostępnych Ekranów

### ✨ Nowe ekrany kreatywne & HUD
1. **🌆 Retro Synthwave HUD:**
   - Animowany, perspektywiczny grid neonowy i retro słońce z poziomymi pasami.
   - Duży cyberpunkowy zegar cyfrowy, data i wskaźniki obciążenia CPU, GPU, RAM oraz temperatur.
   - Wybór palet kolorów (*Neon Sunset*, *Cyber Grid*, *Outrun Purple*, *Laser Blue*) i edycja własnego napisu.
2. **🟢 Matrix Digital Rain:**
   - Spływający kaskadowo deszcz zielonych znaków Matrix / hex.
   - Konsola terminala z cyfrowym zegarem czasu rzeczywistego i macierzą zużycia zasobów komputera.
   - Motywy kolorystyczne: *Classic Green*, *Amber CRT*, *Cyber Cyan*, *Red Alert*.
3. **🎵 Audio Spectrum & VU Meter:**
   - 18-pasmowy dynamiczny spektrogram częstotliwości audio ze wskaźnikami wartości szczytowych (*Peak Hold*).
   - Stereofoniczny podwójny miernik poziomu sygnału (CH-L / CH-R) z podziałem decybelowym (Zielony/Żółty/Czerwony).
4. **🏎️ Dual Racing Tachometers (Zegary obrotomierza):**
   - Podwójne analogowe wskaźniki zegarowe dla obciążenia CPU i GPU ze wskazówkami i strefą czerwonego pola (*Redline*).
   - Środkowy cyfrowy blok odczytu temperatur podzespołów oraz dolny pasek pamięci RAM i dysku NVMe.
5. **⏱️ Pomodoro & Focus Timer:**
   - Okrągły wskaźnik postępu sesji głębokiej pracy (*Deep Work - 25 min*) i przerw regeneracyjnych (*Break - 5 min*).
   - Przyciski Start / Pauza / Reset oraz licznik zrealizowanych rund.
6. **🚀 Sci-Fi Starship HUD:**
   - Panel dowodzenia rodem z mostka statku kosmicznego z obrotowym radarem taktycznym (Sweep radar).
   - Wskaźniki stanu rdzenia reaktora (CPU), silników warp (GPU) i osłon (RAM).

### 📊 Telemetria i monitoring podzespołów
7. **🧩 Super Dashboard (Modułowy):**
   - Dowolne łączenie elementów: zegar, słupki CPU/RAM/GPU, temperatury podzespołów i własne zdjęcie w tle.
8. **📊 Telemetria PC (Pierścienie Neon):**
   - Trzy kołowe wskaźniki zegarowe CPU, RAM i GPU z prędkością transferu sieci.
9. **🌡️ Temperatury Podzespołów (Thermals):**
   - Szczegółowy monitoring temperatur CPU, GPU i dysku NVMe SSD z 3-stopniowym systemem alertów barwnych.

### 🕒 Zegary i Narzędzia
10. **🕒 Zegary Stylizowane:**
    - 5 stylów: *Cyberpunk Neon*, *Cyfrowy Modern*, *Retro Zielony LCD (Casio)*, *Minimalistyczny*, *Klasyczny Analogowy*.
11. **📅 Kalendarz Miesięczny:**
    - Pełny miesiąc z wyróżnionym dniem dzisiejszym, dniami wolnymi od pracy i zegarem.

### 🖼️ Multimedia
12. **🖼️ Zdjęcia i Grafiki:**
    - Obsługa PNG, JPG, BMP, WebP z dopasowaniem kadru (*Cover*, *Contain*, *Stretch*), jasnością i kontrastem.
13. **🎞️ Animowany GIF Player:**
    - Odtwarzanie GIF-ów z suwakiem prędkości klatek (0.25x – 3.0x).
14. **📋 Pokaz Slajdów:**
    - Playlisty zdjęć z automatyczną rotacją i trybem losowym (*Shuffle*).

---

## 🛠️ Uruchomienie aplikacji

```bash
/home/kret/Pulpit/PROJEKTY/skyloong-lcd-controller/run.sh
```

Wszystkie zależności instalują się automatycznie w dedykowanym środowisku wirtualnym `.venv`.
