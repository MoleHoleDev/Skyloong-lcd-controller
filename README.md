# ⚡ Skyloong LCD Controller — GK104 Pro Studio (320x240)

Nowoczesna aplikacja graficzna **Python / PySide6 (Qt6)** do kompleksowego zarządzania i bezpośredniego strumieniowania obrazu w czasie rzeczywistym (do **60 FPS przez USB CDC**) na wyświetlacz LCD klawiatury **Skyloong GK104 Pro** (oraz kompatybilnych modułów Skyloong v3.0 z układem ESP32-S3 i rozdzielczością 320x240).

---

## 🚀 Nowy interfejs dwukolumnowy & Kafelki z podglądami

Aplikacja została zaprojektowana z myślą o prostocie, maksymalnej wydajności i komforcie użytkowania:

1. **Lewa kolumna (Galeria Kafelkowa & Podgląd na żywo):**
   - **Wirtualny ekran LCD 320x240:** wierne odwzorowanie fizycznego wyświetlacza z licznikiem FPS, wskaźnikiem aktywnego trybu i przyciskiem zrzutu ekranu (`PNG`).
   - **Kafelkowa galeria modułów z miniaturowymi podglądami:** 16 gotowych ekranów w siatce z renderowanymi miniaturami klatek, etykietami statusu (*GRYWALNY*, *NOWOŚĆ*, *POPULARNY*) i filtrami kategorii (*Wszystkie*, *Gry & Retro*, *Efektowne & HUD*, *Telemetria*, *Czas*, *Media*).
2. **Prawa kolumna (Szczegółowe ustawienia & Kontrolery gier):**
   - Dedykowany, przejrzysty panel konfiguracji dla aktualnie wybranego ekranu oraz interaktywne panele sterowania grami (D-Pad, przyciski akcji, ściągawka skrótów klawiaturowych).
   - Pasek parametrów strumienia USB: regulacja klatkażu (15 / 30 / 45 / 60 FPS), jakości kompresji JPEG (70–95%) oraz wybór portu `/dev/ttyACM*`.
3. **Pasek globalny:**
   - Przycisk 1-klik: **`🚀 Rozpocznij / ⏹ Zatrzymaj Strumieniowanie USB`**.
   - Suwak natychmiastowej regulacji jasności podświetlenia (`☀️ 10–255`).
   - Narzędzie wgrywania firmware ESP32-S3.

---

## 🎮 Interaktywne Ekrany Grywalne (Sterowane Klawiaturą)

1. **🍄 Super Mario Retro World & HUD:**
   - Autentyczny świat 8-bit NES Super Mario World z fizyką skoków, grawitacją, ruchomą kamerą i animacjami.
   - Pytajnikowe bloki `[?]` z monetami, cegiełki, zielone rury i spacerujące Goomby, które można rozdeptać!
   - Kule ognia (Fireballs) odbijające się od podłoża i eliminujące wrogów.
   - Pasek telemetrii w stylu arkadowym: `MARIO SCORE`, `COINS`, `CPU %`, `RAM %`, `TIME`.
   - **Sterowanie klawiaturą w systemie:**
     - `A / D` lub `← / →`: Bieg w lewo i prawo
     - `Spacja / W / ↑`: Skok
     - `S / ↓`: Kucnięcie
     - `Ctrl / F / J`: Strzał ognistą kulą
     - *Tryb Autoplay Demo:* Mario gra automatycznie, gdy przez 1.5s nie naciśniesz klawisza!

2. **💀 DOOM Classic 1993 (E1M1 View & Status Bar HUD):**
   - Korytarz 3D z perspektywicznymi ścianami, toksyczną mazią, demonami i krwawymi rozbryzgami.
   - Centralnie umieszczona strzelba (Shotgun / Chaingun) z animacją odrzutu, potężnym błyskiem wystrzału i screenshake.
   - Oryginalny, kultowy **DOOM Status Bar**:
     - Liczniki `AMMO`, `HEALTH`, `ARMOR` z klasycznymi czerwonymi cyframi DOOM.
     - **Animowana twarz Doomgaya:** rozgląda się na boki, szyderczo uśmiecha przy wystrzale i krwawi przy obrażeniach.
     - Zintegrowane karty telemetrii: `KILLS`, `CPU %`, `GPU %`.
   - **Sterowanie klawiaturą w systemie:**
     - `W / S` lub `↑ / ↓`: Ruch w przód / tył
     - `A / D` lub `← / →`: Obrót kamery
     - `Spacja / Ctrl / F / Enter`: Strzał z broni
     - `1 / 2 / 3`: Zmiana broni (Pięści, Shotgun, Chaingun)
     - *Tryb Autoplay Demo:* Doomguy patroluje i eliminuje demony automatycznie podczas bezczynności!

---

## 🎨 Katalog 16 Dostępnych Ekranów

### 🎮 Gry & Retro
1. **🍄 Super Mario Retro World** (Grywalny, fizyka, wrogowie, monety, CPU/RAM HUD)
2. **💀 DOOM Classic 1993** (Grywalny korytarz 3D, strzelba, demony, Doomguy Face Status Bar)

### ✨ Nowe ekrany efektowne & HUD
3. **🌆 Retro Synthwave HUD** (Grid neonowy, retro słońce, zegar cyberpunk, CPU/GPU/RAM)
4. **🟢 Matrix Digital Rain** (Deszcz glifów Matrix, cyfrowy terminal zegara i macierz zasobów)
5. **🎵 Audio Spectrum & VU Meter** (18-pasmowy analizator częstotliwości z Peak Hold i miernik CH-L/R)
6. **🏎️ Dual Racing Tachometers** (Analogowe zegary obrotomierza dla CPU i GPU oraz temperatury)
7. **⏱️ Pomodoro & Focus Timer** (Zegar sesji skupienia 25 min i przerw z licznikiem rund)
8. **🚀 Sci-Fi Starship HUD** (Panel dowodzenia z obrotowym radarem taktycznym i stanem reaktora)

### 📊 Telemetria i monitoring podzespołów
9. **🧩 Super Dashboard (Modułowy)** (Zegar, słupki CPU/RAM/GPU, temperatury i własne tło)
10. **📊 Telemetria Pierścienie** (Kołowe wskaźniki neonowe CPU, RAM, GPU z prędkością sieci)
11. **🌡️ Temperatury Sprzętu** (Karty temperatur CPU, GPU i NVMe SSD z 3-stopniowym systemem alertów)

### 🕒 Zegary i Narzędzia
12. **🕒 Zegar Cyfrowy i Analogowy** (5 stylów: Cyberpunk, Retro LCD, Modern, Minimal, Analog)
13. **📅 Kalendarz Miesięczny** (Pełny miesiąc z wyróżnionym dniem dzisiejszym i zegarem)

### 🖼️ Multimedia
14. **🖼️ Pojedyncze Zdjęcie** (PNG, JPG, BMP z kadrowaniem, jasnością i kontrastem)
15. **🎞️ Animowany GIF Player** (Płynne odtwarzanie animacji GIF z regulacją FPS)
16. **📋 Pokaz Slajdów** (Playlisty zdjęć z automatyczną rotacją i trybem losowym)

---

## 🛠️ Uruchomienie aplikacji

```bash
/home/kret/Pulpit/PROJEKTY/skyloong-lcd-controller/run.sh
```

Wszystkie zależności instalują się automatycznie w dedykowanym środowisku wirtualnym `.venv`.
