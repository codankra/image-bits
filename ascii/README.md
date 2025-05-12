# Image to ASCII-Character Art Generator

This Python script converts an input image into a stylized PNG representation using ASCII-like characters, rendered in multiple shades of a chosen base color. It's designed to create art reminiscent of terminal graphics or detailed character-based displays.

## Features

- Customizable base color and number of shades.
- User-defined character set for mapping image brightness.
- Support for TrueType fonts (`.ttf`).
- Adjustable output width (in characters).
- Optional explicit control over character cell dimensions.
- Aspect ratio correction to maintain the original image's proportions.
- Optional image posterization for a more "blocky" or "cartoonish" effect.
- Option to skip drawing the lightest character if it's a space, revealing the background.

## Dependencies

- **Python 3.x**
- **Pillow (PIL Fork)**: The Python Imaging Library.
  Install it using pip:
  ```bash
  pip install Pillow
  ```

## Usage

Run the script from your terminal:

```bash
python image_to_char_art.py <image_path> <hex_color> [options]
```

**Required Arguments:**

- `image_path`: Path to the input image file (e.g., `my_face.jpg`, `input/landscape.png`).
- `hex_color`: Base hex color code for the character shades (e.g., `'#44ccaa'`, `'#FF6600'`). **Remember to enclose in single quotes if it contains `#` to prevent shell interpretation.**

**Optional Arguments:**

- `-cwid`, `--width_chars <int>`:
  Width of the output art in number of characters. (Default: `80`)
- `--charset <string>`:
  String of characters to use, ordered from sparse (for light image areas) to dense (for dark image areas). The number of characters determines the number of foreground shades.
  (Default: `" .:-=+*#%@$"`)
  **IMPORTANT:** If your charset string contains special shell characters (e.g., `!`, `*`, `(`, `)`, `|`, `\`, `&`), you **MUST** enclose the entire string in **SINGLE QUOTES** on the command line.
  Example: `--charset ' ."`^\,:;!l~-\_+<>i?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao\*#MW&8%B@$'`
- `--font_path <path>`:
  Path to a `.ttf` font file. If not provided, the script attempts to use common system monospaced fonts (like DejaVuSansMono, Consolas, Courier New, Menlo).
- `--font_size <int>`:
  Font size in points. (Default: `15`)
- `--cell_width_px <int>`:
  Explicit width of each character cell in pixels. If not set, it's derived from the font.
- `--cell_height_px <int>`:
  Explicit height of each character cell in pixels. If not set, it's derived from the font.
- `-ar`, `--aspect_ratio_correction <float>`:
  Aspect ratio of a single character cell, defined as `cell_width / cell_height`. This is crucial for sampling the input image correctly to preserve its original visual aspect ratio in the final output.
  (Default: `0.5`)
  - `0.5`: For cells that are twice as tall as they are wide (e.g., a typical terminal font cell might be 8px wide by 16px tall).
  - `1.0`: For square cells.
  - `2.0`: For cells that are twice as wide as they are tall.
- `--posterize_bits <int>`:
  Number of bits (1-8) for color channel posterization of the input image _before_ converting to characters. Fewer bits lead to a more "blocky" or "cartoonish" look by reducing the number of distinct colors in the source. `0` disables posterization. (Default: `0`)
- `--skip_lightest_if_space`:
  If this flag is present AND the first character in your `--charset` is a space (`' '`), then for the very lightest parts of your image (that map to this first character), no character will be drawn. This leaves the pure background color visible, which can be a nice effect. (Default: The space character is drawn with the lightest foreground color).
- `-o`, `--output <path>`:
  Path to save the output PNG file. (Default: `char_art_output.png`)

## Examples

1.  **Basic usage with default settings:**

    ```bash
    python image_to_char_art.py portrait.jpg '#0099CC'
    ```

2.  **Smaller output width, custom short charset, specific font:**

    ```bash
    python image_to_char_art.py landscape.png '#FF8800' --width_chars 60 --charset ' .:o*@' --font_path '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf' --font_size 18
    ```

3.  **Using a long, complex charset (note the single quotes!) and posterization:**

    ```bash
    python image_to_char_art.py my_avatar.png '#33CC33' --width_chars 70 --charset ' ."`^\",:;!l~-_+<>i?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$' --posterize_bits 3 --output avatar_art.png
    ```

4.  **Making lightest parts true background (if first char is space):**

    ```bash
    python image_to_char_art.py my_face.jpg '#AA33BB' --charset " .:oO0@" --skip_lightest_if_space
    ```

5.  **Using block characters for a "pixelated" look (font choice is key):**
    ```bash
    python image_to_char_art.py icon.png '#777777' --width_chars 40 --charset ' ░▒▓█' --font_path 'DejaVuSansMono.ttf' --font_size 12 --aspect_ratio_correction 1.0
    ```
    (For block characters, an `aspect_ratio_correction` closer to `1.0` might be appropriate if the blocks render as roughly square).

## Tips for Good Results

- **Charset Choice:** The `charset` is critical. Experiment with different character ramps. The order (sparse to dense) directly impacts how brightness translates to visual density.
- **Font Selection:** A good monospaced font is usually best. The appearance of characters can vary significantly between fonts. Ensure the chosen font supports all characters in your `charset`.
- **Aspect Ratio:** Pay close attention to `--aspect_ratio_correction`. If your output looks stretched or squashed, this is the primary parameter to adjust. It depends on the visual aspect ratio of the characters _as rendered by your chosen font and size_ (or your explicit cell dimensions).
- **Width vs. Detail:** A smaller `--width_chars` will result in a more abstract, "chunky" look. A larger width allows for more detail.
- **Experiment!** The best way to get the look you want is to try different combinations of settings.
