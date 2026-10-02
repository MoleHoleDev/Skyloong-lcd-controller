#include <Arduino.h>
#include <driver/spi_master.h>
#include <esp_lcd_types.h>
#include <esp_lcd_panel_io.h>
#include <esp_lcd_panel_vendor.h>
#include <esp_lcd_panel_ops.h>
#include <TJpg_Decoder.h>

// Hardware Pin Definitions from JZ-Skyloong esp32_screen_module
#define PIN_DISPLAY_CS   10
#define PIN_DISPLAY_DC   11
#define PIN_DISPLAY_RST  7
#define PIN_DISPLAY_SCLK 9
#define PIN_DISPLAY_MOSI 8
#define PIN_DISPLAY_BL   14
#define PIN_DISPLAY_PWR  13

#define SCREEN_WIDTH     320
#define SCREEN_HEIGHT    240

// Protocol Magic & Commands
#define PROTOCOL_MAGIC_0 'S'
#define PROTOCOL_MAGIC_1 'K'
#define PROTOCOL_MAGIC_2 'Y'
#define PROTOCOL_MAGIC_3 'L'

#define CMD_DRAW_JPEG        0x01
#define CMD_DRAW_RAW565      0x02
#define CMD_SET_BRIGHTNESS   0x03
#define CMD_PING             0x04
#define CMD_SCREEN_POWER     0x05
#define CMD_CLEAR_SCREEN     0x06
#define CMD_RESET_BOOTLOADER 0x09

// Handles
static esp_lcd_panel_io_handle_t io_handle = NULL;
static esp_lcd_panel_handle_t panel_handle = NULL;

// Framebuffer & Statistics
static uint32_t frame_count = 0;
static uint32_t last_fps_time = 0;
static float current_fps = 0.0f;
static uint8_t current_brightness = 200;

// Full Frame Buffer in DMA memory (320x240x2 = 150 KB)
static uint16_t* frame_buffer = NULL;

// JPEG Buffer
#define MAX_JPEG_SIZE (64 * 1024)
static uint8_t jpeg_buffer[MAX_JPEG_SIZE];

// Callback for TJpg_Decoder: Copy decoded block into full frame buffer cleanly
static bool tjpg_output_callback(int16_t x, int16_t y, uint16_t w, uint16_t h, uint16_t* bitmap) {
    if (!frame_buffer) return 0;
    if (y >= SCREEN_HEIGHT || x >= SCREEN_WIDTH) return 0;

    int16_t copy_w = w;
    int16_t copy_h = h;
    if (x + copy_w > SCREEN_WIDTH) copy_w = SCREEN_WIDTH - x;
    if (y + copy_h > SCREEN_HEIGHT) copy_h = SCREEN_HEIGHT - y;

    for (int16_t row = 0; row < copy_h; row++) {
        uint16_t* dst_line = &frame_buffer[(y + row) * SCREEN_WIDTH + x];
        uint16_t* src_line = &bitmap[row * w];
        for (int16_t col = 0; col < copy_w; col++) {
            uint16_t pix = src_line[col];
            dst_line[col] = (pix >> 8) | (pix << 8); // Swap endianness for ST7789
        }
    }
    return 1;
}

// Display initialization matching JZ-Skyloong esp32_screen_module
void init_display() {
    // Power on display logic
    pinMode(PIN_DISPLAY_PWR, OUTPUT);
    digitalWrite(PIN_DISPLAY_PWR, HIGH);

    // Backlight PWM on GPIO 14 (16 kHz, 8-bit)
    ledcSetup(7, 16000, 8);
    ledcAttachPin(PIN_DISPLAY_BL, 7);
    ledcWrite(7, current_brightness);

    // SPI Bus Configuration (DMA mode enabled)
    spi_bus_config_t buscfg;
    memset(&buscfg, 0, sizeof(spi_bus_config_t));
    buscfg.mosi_io_num = PIN_DISPLAY_MOSI;
    buscfg.miso_io_num = -1;
    buscfg.sclk_io_num = PIN_DISPLAY_SCLK;
    buscfg.quadwp_io_num = -1;
    buscfg.quadhd_io_num = -1;
    buscfg.max_transfer_sz = SCREEN_WIDTH * SCREEN_HEIGHT * 2;
    ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &buscfg, SPI_DMA_CH_AUTO));

    // Panel IO (80 MHz SPI Clock)
    esp_lcd_panel_io_spi_config_t io_config;
    memset(&io_config, 0, sizeof(esp_lcd_panel_io_spi_config_t));
    io_config.cs_gpio_num = PIN_DISPLAY_CS;
    io_config.dc_gpio_num = PIN_DISPLAY_DC;
    io_config.spi_mode = 0;
    io_config.pclk_hz = 80000000;
    io_config.trans_queue_depth = 4;
    io_config.lcd_cmd_bits = 8;
    io_config.lcd_param_bits = 8;
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi((esp_lcd_spi_bus_handle_t)SPI2_HOST, &io_config, &io_handle));

    // ST7789 Panel Config
    esp_lcd_panel_dev_config_t panel_config;
    memset(&panel_config, 0, sizeof(esp_lcd_panel_dev_config_t));
    panel_config.reset_gpio_num = PIN_DISPLAY_RST;
    panel_config.color_space = ESP_LCD_COLOR_SPACE_RGB;
    panel_config.bits_per_pixel = 16;
    ESP_ERROR_CHECK(esp_lcd_new_panel_st7789(io_handle, &panel_config, &panel_handle));

    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel_handle));
    delay(10);

    // Official ST7789 Registers from Skyloong firmware
    uint8_t data_buffer[24];
    data_buffer[0] = 0x00;
    esp_lcd_panel_io_tx_param(io_handle, 0x36, data_buffer, 1);
    data_buffer[0] = 0x55;
    esp_lcd_panel_io_tx_param(io_handle, 0x3A, data_buffer, 1);
    esp_lcd_panel_io_tx_param(io_handle, 0x21, NULL, 0);
    data_buffer[0] = 0x00;
    esp_lcd_panel_io_tx_param(io_handle, 0xB0, data_buffer, 1);
    data_buffer[0] = 0x05; data_buffer[1] = 0x05; data_buffer[2] = 0x00; data_buffer[3] = 0x33; data_buffer[4] = 0x33;
    esp_lcd_panel_io_tx_param(io_handle, 0xB2, data_buffer, 5);
    data_buffer[0] = 0x75;
    esp_lcd_panel_io_tx_param(io_handle, 0xB7, data_buffer, 1);
    data_buffer[0] = 0x22;
    esp_lcd_panel_io_tx_param(io_handle, 0xBB, data_buffer, 1);
    data_buffer[0] = 0x2C;
    esp_lcd_panel_io_tx_param(io_handle, 0xC0, data_buffer, 1);
    data_buffer[0] = 0x01;
    esp_lcd_panel_io_tx_param(io_handle, 0xC2, data_buffer, 1);
    data_buffer[0] = 0x13;
    esp_lcd_panel_io_tx_param(io_handle, 0xC3, data_buffer, 1);
    data_buffer[0] = 0x20;
    esp_lcd_panel_io_tx_param(io_handle, 0xC4, data_buffer, 1);
    data_buffer[0] = 0x05;
    esp_lcd_panel_io_tx_param(io_handle, 0xC6, data_buffer, 1);
    data_buffer[0] = 0xA4; data_buffer[1] = 0xA1;
    esp_lcd_panel_io_tx_param(io_handle, 0xD0, data_buffer, 2);
    data_buffer[0] = 0xA1;
    esp_lcd_panel_io_tx_param(io_handle, 0xD6, data_buffer, 1);
    data_buffer[0] = 0xD0; data_buffer[1] = 0x05; data_buffer[2] = 0x0A; data_buffer[3] = 0x09;
    data_buffer[4] = 0x08; data_buffer[5] = 0x05; data_buffer[6] = 0x2E; data_buffer[7] = 0x44;
    data_buffer[8] = 0x45; data_buffer[9] = 0x0F; data_buffer[10] = 0x17; data_buffer[11] = 0x16;
    data_buffer[12] = 0x2B; data_buffer[13] = 0x33;
    esp_lcd_panel_io_tx_param(io_handle, 0xE0, data_buffer, 14);
    data_buffer[0] = 0xD0; data_buffer[1] = 0x05; data_buffer[2] = 0x0A; data_buffer[3] = 0x09;
    data_buffer[4] = 0x08; data_buffer[5] = 0x05; data_buffer[6] = 0x2E; data_buffer[7] = 0x43;
    data_buffer[8] = 0x45; data_buffer[9] = 0x0F; data_buffer[10] = 0x16; data_buffer[11] = 0x16;
    data_buffer[12] = 0x2B; data_buffer[13] = 0x33;
    esp_lcd_panel_io_tx_param(io_handle, 0xE1, data_buffer, 14);

    // Frame column/row window setup (0..239 x 0..319 before swap_xy)
    data_buffer[0] = 0x00; data_buffer[1] = 0x00; data_buffer[2] = 0x00; data_buffer[3] = 0xEF;
    esp_lcd_panel_io_tx_param(io_handle, 0x2A, data_buffer, 4);
    data_buffer[0] = 0x00; data_buffer[1] = 0x00; data_buffer[2] = 0x01; data_buffer[3] = 0x3F;
    esp_lcd_panel_io_tx_param(io_handle, 0x2B, data_buffer, 4);

    esp_lcd_panel_io_tx_param(io_handle, 0x11, NULL, 0); // Sleep out
    delay(100);
    esp_lcd_panel_io_tx_param(io_handle, 0x29, NULL, 0); // Display on
    esp_lcd_panel_io_tx_param(io_handle, 0x2C, NULL, 0); // Memory write

    ESP_ERROR_CHECK(esp_lcd_panel_swap_xy(panel_handle, true));
    ESP_ERROR_CHECK(esp_lcd_panel_invert_color(panel_handle, true));
    ESP_ERROR_CHECK(esp_lcd_panel_mirror(panel_handle, false, true));

    // Initialize TJpg_Decoder
    TJpgDec.setJpgScale(1);
    TJpgDec.setSwapBytes(false); // Done inside callback
    TJpgDec.setCallback(tjpg_output_callback);
}

void clear_display(uint16_t color) {
    if (!frame_buffer) return;
    uint16_t swapped = (color >> 8) | (color << 8);
    for (int i = 0; i < SCREEN_WIDTH * SCREEN_HEIGHT; i++) {
        frame_buffer[i] = swapped;
    }
    esp_lcd_panel_draw_bitmap(panel_handle, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, frame_buffer);
}

void draw_splash_screen() {
    clear_display(0x0821); // Dark navy
}

void setup() {
    Serial.begin(115200);
    Serial.setRxBufferSize(32768); // Large USB RX buffer
    
    // Allocate full 320x240 frame buffer (150 KB)
    frame_buffer = (uint16_t*)heap_caps_malloc(SCREEN_WIDTH * SCREEN_HEIGHT * sizeof(uint16_t), MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
    if (!frame_buffer) {
        frame_buffer = (uint16_t*)malloc(SCREEN_WIDTH * SCREEN_HEIGHT * sizeof(uint16_t));
    }
    
    init_display();
    draw_splash_screen();
    last_fps_time = millis();
}

static size_t read_bytes_exact(uint8_t* buffer, size_t length, uint32_t timeout_ms = 500) {
    size_t total = 0;
    uint32_t start = millis();
    while (total < length && (millis() - start) < timeout_ms) {
        int avail = Serial.available();
        if (avail > 0) {
            size_t to_read = min((size_t)avail, length - total);
            size_t r = Serial.readBytes((char*)buffer + total, to_read);
            total += r;
        } else {
            delayMicroseconds(50);
        }
    }
    return total;
}

void loop() {
    // Check for Magic Header 'SKYL'
    if (Serial.available() >= 4) {
        if (Serial.peek() == PROTOCOL_MAGIC_0) {
            uint8_t magic[4];
            if (read_bytes_exact(magic, 4, 100) == 4) {
                if (magic[0] == PROTOCOL_MAGIC_0 &&
                    magic[1] == PROTOCOL_MAGIC_1 &&
                    magic[2] == PROTOCOL_MAGIC_2 &&
                    magic[3] == PROTOCOL_MAGIC_3) {
                    
                    // Read Command Byte (1 byte)
                    uint8_t cmd = 0;
                    if (read_bytes_exact(&cmd, 1, 100) != 1) return;

                    switch (cmd) {
                        case CMD_DRAW_JPEG: {
                            // Length (4 bytes, little-endian)
                            uint32_t payload_len = 0;
                            if (read_bytes_exact((uint8_t*)&payload_len, 4, 100) != 4) return;
                            if (payload_len > 0 && payload_len <= MAX_JPEG_SIZE) {
                                if (read_bytes_exact(jpeg_buffer, payload_len, 1000) == payload_len) {
                                    TJpgDec.drawJpg(0, 0, jpeg_buffer, payload_len);
                                    if (frame_buffer) {
                                        esp_lcd_panel_draw_bitmap(panel_handle, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, frame_buffer);
                                    }
                                    frame_count++;
                                    Serial.write((uint8_t)0x06); // Send ACK (0x06)
                                } else {
                                    Serial.write((uint8_t)0x15); // NAK
                                }
                            }
                            break;
                        }
                        case CMD_DRAW_RAW565: {
                            // x(2), y(2), w(2), h(2), len(4)
                            uint16_t x = 0, y = 0, w = 0, h = 0;
                            uint32_t len = 0;
                            if (read_bytes_exact((uint8_t*)&x, 2, 100) != 2) return;
                            if (read_bytes_exact((uint8_t*)&y, 2, 100) != 2) return;
                            if (read_bytes_exact((uint8_t*)&w, 2, 100) != 2) return;
                            if (read_bytes_exact((uint8_t*)&h, 2, 100) != 2) return;
                            if (read_bytes_exact((uint8_t*)&len, 4, 100) != 4) return;

                            uint8_t* raw_buf = (uint8_t*)heap_caps_malloc(len, MALLOC_CAP_DMA);
                            if (raw_buf) {
                                if (read_bytes_exact(raw_buf, len, 1000) == len) {
                                    esp_lcd_panel_draw_bitmap(panel_handle, x, y, x + w, y + h, (uint16_t*)raw_buf);
                                    frame_count++;
                                    Serial.write((uint8_t)0x06); // ACK
                                } else {
                                    Serial.write((uint8_t)0x15); // NAK
                                }
                                free(raw_buf);
                            }
                            break;
                        }
                        case CMD_SET_BRIGHTNESS: {
                            uint8_t bright = 200;
                            if (read_bytes_exact(&bright, 1, 100) == 1) {
                                current_brightness = bright;
                                ledcWrite(7, current_brightness);
                                Serial.write((uint8_t)0x06); // ACK
                            }
                            break;
                        }
                        case CMD_PING: {
                            // Send Pong stats packet: [0x53, 0x4B, 0x50, 0x47] + FPS(float) + Brightness(uint8) + Uptime(uint32)
                            uint8_t pong[13];
                            pong[0] = 'S'; pong[1] = 'K'; pong[2] = 'P'; pong[3] = 'G';
                            memcpy(&pong[4], &current_fps, 4);
                            pong[8] = current_brightness;
                            uint32_t upt = millis();
                            memcpy(&pong[9], &upt, 4);
                            Serial.write(pong, 13);
                            break;
                        }
                        case CMD_SCREEN_POWER: {
                            uint8_t pwr = 1;
                            if (read_bytes_exact(&pwr, 1, 100) == 1) {
                                if (pwr) {
                                    digitalWrite(PIN_DISPLAY_PWR, HIGH);
                                    ledcWrite(7, current_brightness);
                                } else {
                                    ledcWrite(7, 0);
                                    digitalWrite(PIN_DISPLAY_PWR, LOW);
                                }
                                Serial.write((uint8_t)0x06); // ACK
                            }
                            break;
                        }
                        case CMD_CLEAR_SCREEN: {
                            uint16_t clr = 0;
                            if (read_bytes_exact((uint8_t*)&clr, 2, 100) == 2) {
                                clear_display(clr);
                                Serial.write((uint8_t)0x06); // ACK
                            }
                            break;
                        }
                        case CMD_RESET_BOOTLOADER: {
                            Serial.write((uint8_t)0x06);
                            delay(50);
                            esp_restart();
                            break;
                        }
                        default:
                            break;
                    }
                }
            }
        } else {
            // Discard unaligned byte
            Serial.read();
        }
    }

    // Calculate FPS every 1 second
    uint32_t now = millis();
    if (now - last_fps_time >= 1000) {
        current_fps = (float)frame_count * 1000.0f / (float)(now - last_fps_time);
        frame_count = 0;
        last_fps_time = now;
    }
}
