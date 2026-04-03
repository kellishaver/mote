# Known Issues — Waveshare ESP32-S3-Touch-AMOLED-1.91 + dobodu amoled driver

## 1. Display Enable Pin (TFT_CDE) — RESOLVED

The Waveshare 1.91" does **NOT** need a display-enable pin. GPIO 38 is not required (unlike the Lilygo 1.91" which uses it). No TCA9554 expander is present on the touch I2C bus. The display powers on with just the standard init sequence.

## 2. QSPIPanel Width/Height Are Swapped

The `QSPIPanel()` constructor takes `width` and `height` in **swapped order** relative to the physical display:
```python
# For a 536x240 display:
panel = amoled.QSPIPanel(..., width=240, height=536)
```
This is consistent across all configs in the repo. Rotation is then applied via `display.rotation()`.

## 3. Color Order — RGB (default)

The RM67162 defaults to **RGB** color order. The driver constructor accepts `color_space=rm67162.BGR` if colors appear wrong (red/blue swapped). The dobodu driver uses RGB by default. If colors look off, try `display.invert_color()` or rebuild with BGR.

## 4. Default Orientation

- **Rotation 0:** Portrait, 240x536 (narrow and tall)
- **Rotation 1:** Landscape, 536x240 (wide, normal reading orientation) — **recommended default**
- **Rotation 2:** Portrait inverted
- **Rotation 3:** Landscape inverted

## 5. Scrolling Does Not Work

Both repos state scrolling is non-functional on the RM67162. Do not rely on hardware scroll for UI elements.

## 6. Framebuffer RAM Usage

The display framebuffer consumes **536 x 240 x 2 = 257,280 bytes** (~251 KB). With 8 MB PSRAM this is fine, but be aware if allocating other large buffers.

## 7. Brightness Range

The `display.brightness()` method accepts **0–255** (not 0–100 as some docs suggest). Use `200` for comfortable brightness, `255` for max.

## 8. auto_refresh Behavior

By default, every draw call immediately pushes to the display. For complex scenes with many draw calls, consider:
```python
display = amoled.AMOLED(panel, type=0, reset=Pin(17), bpp=16, auto_refresh=False)
# ... draw everything ...
display.refresh()
```
This avoids visible partial rendering.

## 9. Font Usage — CRITICAL

**`display.text(None, ...)` causes a hard C-level crash.** Never pass `None` as a font argument.

Two working font systems:
- **Bitmap:** `import fonts.large as font` then `display.write(font, text, x, y, color)` — 31px tall
- **TTF:** `fnt = amoled.TTF(ttf="/fonts/test.ttf", xscale=N, yscale=N)` then `display.ttf_draw(fnt, text, x, y, color)` — scalable

Both require font files uploaded to `/fonts/` on the board:
```bash
mpremote connect $PORT mkdir /fonts
mpremote connect $PORT cp fonts/large.py :/fonts/large.py
mpremote connect $PORT cp fonts/test.ttf :/fonts/test.ttf
```

Always call `fnt.deinit()` after TTF use. Measure width with `display.write_len(font, text)` (bitmap) or `display.ttf_len(fnt, text)` (TTF).

## 10. SPI Bus Number

Must use `SPI(2)` — this is the HSPI bus on ESP32-S3. `SPI(1)` is reserved.

## 11. dc Pin Reuses QSPI_D1

The `dc=Pin(7)` parameter in `QSPIPanel()` reuses the same GPIO as QSPI_D1. This is intentional — the DC signal is not used as a separate line during QSPI transfers, but the constructor requires it.
