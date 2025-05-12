#!/usr/bin/env python3

import argparse
from PIL import Image, ImageDraw, ImageFont, ImageOps # Removed ImageFilter as outlines are not in this version

# --- Helper Functions ---
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError("Invalid hex color format. Use #RRGGBB.")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def generate_shades(base_rgb, num_total_shades, bg_brightness_factor=0.1):
    """
    Generates num_total_shades (including background).
    Shades[0] is background.
    base_rgb aims to be a mid-level foreground shade.
    """
    if num_total_shades < 2:
        raise ValueError("Total number of shades must be at least 2 (background + one foreground).")

    shades = []
    base_r, base_g, base_b = base_rgb

    # 1. Background shade
    bg_r = int(base_r * bg_brightness_factor)
    bg_g = int(base_g * bg_brightness_factor)
    bg_b = int(base_b * bg_brightness_factor)
    shades.append((bg_r, bg_g, bg_b))

    num_foreground_shades = num_total_shades - 1
    if num_foreground_shades == 0:
        return shades # Only background shade

    if num_foreground_shades == 1:
        shades.append(base_rgb)
    else:
        # Aim for base_rgb to be one of the foreground shades, around the middle.
        # fg_shades_indices: 0 to num_foreground_shades - 1
        base_target_fg_idx = (num_foreground_shades - 1) // 2 # Index for base_rgb within fg shades

        for i in range(num_foreground_shades):
            r, g, b = 0, 0, 0
            # Interpolate from a dark variant of base, through base, to a light variant of base
            dark_fg_start_r = int(bg_r + (base_r - bg_r) * 0.3) # Start a bit above pure background
            dark_fg_start_g = int(bg_g + (base_g - bg_g) * 0.3)
            dark_fg_start_b = int(bg_b + (base_b - bg_b) * 0.3)

            light_fg_end_r = int(base_r + (255 - base_r) * 0.85) # End a bit below pure white
            light_fg_end_g = int(base_g + (255 - base_g) * 0.85)
            light_fg_end_b = int(base_b + (255 - base_b) * 0.85)

            if i < base_target_fg_idx:
                # Interpolate from dark_fg_start to base_rgb
                # t goes from 0 to nearly 1 for this segment
                t = i / base_target_fg_idx if base_target_fg_idx > 0 else 0 # Avoid div by zero if base_target_fg_idx is 0
                r = int(dark_fg_start_r + (base_r - dark_fg_start_r) * t)
                g = int(dark_fg_start_g + (base_g - dark_fg_start_g) * t)
                b = int(dark_fg_start_b + (base_b - dark_fg_start_b) * t)
            elif i == base_target_fg_idx:
                r, g, b = base_r, base_g, base_b
            else: # i > base_target_fg_idx
                # Interpolate from base_rgb to light_fg_end
                # t goes from just above 0 to 1 for this segment
                # Number of steps in this segment: (num_foreground_shades - 1) - base_target_fg_idx
                steps_in_segment = (num_foreground_shades - 1) - base_target_fg_idx
                current_step_in_segment = i - base_target_fg_idx
                t = current_step_in_segment / steps_in_segment if steps_in_segment > 0 else 0
                r = int(base_r + (light_fg_end_r - base_r) * t)
                g = int(base_g + (light_fg_end_g - base_g) * t)
                b = int(base_b + (light_fg_end_b - base_b) * t)
            
            shades.append((
                min(max(0, r), 255),
                min(max(0, g), 255),
                min(max(0, b), 255)
            ))
    
    # print(f"Generated {len(shades)} shades: {shades}") # Keep for debugging if needed
    return shades


# --- Main Function ---
def image_to_ascii_art(
    image_path,
    hex_color,
    output_width_chars,
    charset,
    font_path=None,
    font_size=15,
    cell_width_px=None,
    cell_height_px=None,
    aspect_ratio_correction=0.5,
    posterize_bits=0,
    skip_lightest_char_if_space=False, # Changed default for clarity
    output_path="output.png"
):
    try:
        base_rgb = hex_to_rgb(hex_color)
    except ValueError as e:
        print(f"Error: {e}")
        return

    if not charset:
        print("Error: Character set cannot be empty.")
        return
    
    num_foreground_levels = len(charset)
    num_total_shades = num_foreground_levels + 1

    try:
        shades = generate_shades(base_rgb, num_total_shades)
    except ValueError as e:
        print(f"Error generating shades: {e}")
        return

    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            common_fonts = ["DejaVuSansMono.ttf", "Consolas", "Courier New", "Menlo", "LiberationMono-Regular.ttf"]
            loaded = False
            for fname in common_fonts:
                try:
                    font = ImageFont.truetype(fname, font_size)
                    # print(f"Using font: {fname}") # Less verbose
                    loaded = True
                    break
                except IOError:
                    continue
            if not loaded:
                print("Warning: Could not load a default monospaced font. Trying PIL's default bitmap font (may look suboptimal).")
                font = ImageFont.load_default()
    except IOError:
        print(f"Error: Could not load font from '{font_path}'. Ensure the .ttf file exists or is in system paths. Trying PIL's default.")
        font = ImageFont.load_default()
    except Exception as e:
        print(f"An unexpected error occurred while loading the font: {e}")
        return

    try:
        bbox = font.getbbox("M") # (left, top, right, bottom) for Pillow >= 9.1.0
        char_w_est = bbox[2] - bbox[0]
        ascent, descent = font.getmetrics() if hasattr(font, 'getmetrics') else (bbox[3] - bbox[1] - font.getbbox("g")[1] + bbox[1], font.getbbox("g")[1] - bbox[1]) # Crude fallback for getmetrics
        char_h_est = ascent + descent
    except AttributeError: # Fallback for older Pillow or basic font
        try:
            char_w_est, char_h_est = font.getsize("M") if hasattr(font, 'getsize') else (font_size // 2, font_size)
        except AttributeError: # Ultimate fallback for PIL default font
             char_w_est, char_h_est = font_size // 2, font_size


    actual_cell_width_px = cell_width_px if cell_width_px is not None else int(char_w_est * 1.0)
    actual_cell_height_px = cell_height_px if cell_height_px is not None else int(char_h_est * 1.0)
    if actual_cell_width_px <= 0: actual_cell_width_px = 1
    if actual_cell_height_px <= 0: actual_cell_height_px = 1
    # print(f"Using cell dimensions: {actual_cell_width_px}x{actual_cell_height_px} px")

    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        print(f"Error: Input image file not found at '{image_path}'")
        return
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    if posterize_bits > 0 and posterize_bits <= 8:
        img = ImageOps.posterize(img.convert("RGB"), posterize_bits)

    img_gray = img.convert("L")
    original_width_px, original_height_px = img_gray.size

    # Corrected aspect ratio calculation:
    # aspect_ratio_correction is cell_width / cell_height
    # We want the final pixel art to have the same aspect as the original image.
    # (output_width_chars * actual_cell_width_px) / (output_grid_height_chars * actual_cell_height_px) = original_width_px / original_height_px
    # output_grid_height_chars = output_width_chars * (actual_cell_width_px / actual_cell_height_px) * (original_height_px / original_width_px)
    # output_grid_height_chars = output_width_chars * (provided_aspect_ratio_correction) * (image_vertical_aspect)
    
    image_vertical_aspect = original_height_px / original_width_px if original_width_px > 0 else 1.0
    output_grid_height_chars = int(output_width_chars * image_vertical_aspect / aspect_ratio_correction)
    if output_grid_height_chars < 1: output_grid_height_chars = 1

    img_resized_gray = img_gray.resize((output_width_chars, output_grid_height_chars), Image.Resampling.LANCZOS)
    # print(f"Resized image to character grid: {output_width_chars}x{output_grid_height_chars}")

    final_img_width_px = output_width_chars * actual_cell_width_px
    final_img_height_px = output_grid_height_chars * actual_cell_height_px
    
    output_img = Image.new("RGB", (final_img_width_px, final_img_height_px), color=shades[0]) # Background
    draw = ImageDraw.Draw(output_img)

    grayscale_step = 256.0 / num_foreground_levels if num_foreground_levels > 0 else 256.0

    for y_char_idx in range(output_grid_height_chars):
        for x_char_idx in range(output_width_chars):
            brightness = img_resized_gray.getpixel((x_char_idx, y_char_idx))
            
            element_idx = 0
            if num_foreground_levels > 0:
                 element_idx = min(int(brightness / grayscale_step), num_foreground_levels - 1)
            
            char_to_draw = charset[element_idx] if num_foreground_levels > 0 else ' '
            color_for_char = shades[element_idx + 1] if num_foreground_levels > 0 else shades[0]

            if skip_lightest_char_if_space and element_idx == 0 and char_to_draw == ' ' and num_foreground_levels > 0:
                continue

            cell_center_x = (x_char_idx * actual_cell_width_px) + (actual_cell_width_px / 2)
            cell_center_y = (y_char_idx * actual_cell_height_px) + (actual_cell_height_px / 2)
            
            try:
                draw.text(
                    (cell_center_x, cell_center_y),
                    char_to_draw,
                    font=font,
                    fill=color_for_char,
                    anchor="mm"
                )
            except TypeError as e:
                if "anchor" in str(e).lower() or "keyword argument" in str(e).lower(): # Broader check for anchor issue
                    char_bbox = font.getbbox(char_to_draw) if hasattr(font, 'getbbox') else (0,0,0,0)
                    char_w = char_bbox[2] - char_bbox[0] if hasattr(font, 'getbbox') else font.getsize(char_to_draw)[0] if hasattr(font, 'getsize') else actual_cell_width_px / 2
                    char_h = char_bbox[3] - char_bbox[1] if hasattr(font, 'getbbox') else font.getsize(char_to_draw)[1] if hasattr(font, 'getsize') else actual_cell_height_px / 2
                    
                    # For y-centering with baseline, using ascent and descent is better.
                    ascent, descent = font.getmetrics() if hasattr(font, 'getmetrics') else (char_h * 0.75, char_h * 0.25) # Approx
                    text_x = cell_center_x - char_w / 2
                    # text_y calculation to align baseline to middle of cell is tricky without anchor='mm'
                    # A common approach is to position based on ascent for top-left.
                    # For centering, this is roughly:
                    text_y = cell_center_y - (ascent - descent) / 2 - descent # This is often closer for middle align
                    # A simpler one if the above is off: cell_center_y - char_h / 2
                    
                    # Simplified y for older Pillow:
                    text_y = cell_center_y - char_h / 2 + (char_bbox[1] if char_bbox else 0) # char_bbox[1] is often negative top bearing

                    draw.text((text_x, text_y), char_to_draw, font=font, fill=color_for_char)
                else:
                    raise e
            except Exception as e_draw: # Catch other potential drawing errors
                print(f"Warning: Error drawing character '{char_to_draw}' at ({x_char_idx},{y_char_idx}): {e_draw}")
                continue


    try:
        output_img.save(output_path, "PNG")
        print(f"ASCII-character style art saved to '{output_path}'")
    except Exception as e:
        print(f"Error saving image: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    RECOMMENDED_DEFAULT_CHARSET = " .:-=+*#%@$"

    parser = argparse.ArgumentParser(
        description="Generate low-res ASCII-character style art from an image.",
        formatter_class=argparse.RawTextHelpFormatter # To allow better formatting for charset help
    )
    parser.add_argument("image_path", help="Path to the input image file.")
    parser.add_argument("hex_color", help="Base hex color code for shades (e.g., '#44ccaa').")
    parser.add_argument("-cwid", "--width_chars", type=int, default=80,
                        help="Width of the output art in number of characters.")
    parser.add_argument("--charset", type=str, default=RECOMMENDED_DEFAULT_CHARSET,
                        help="String of characters to use, ordered from sparse (for light areas) to dense (for dark areas).\n"
                             "The number of characters determines the number of foreground shades.\n"
                             "IMPORTANT: If using special shell characters, enclose the string in SINGLE QUOTES.\n"
                             "Example: --charset ' .:-=+*#%@$'")
    parser.add_argument("--font_path", type=str, default=None,
                        help="Path to a .ttf font file. If not provided, attempts common system monospaced fonts.")
    parser.add_argument("--font_size", type=int, default=15,
                        help="Font size in points.")
    parser.add_argument("--cell_width_px", type=int, default=None,
                        help="Explicit width of each character cell in pixels. Overrides font-derived width.")
    parser.add_argument("--cell_height_px", type=int, default=None,
                        help="Explicit height of each character cell in pixels. Overrides font-derived height.")
    parser.add_argument("-ar", "--aspect_ratio_correction", type=float, default=2,
                        help="Aspect ratio of a single character cell (cell_width / cell_height).\n"
                             "This is used to sample the input image correctly to preserve its original visual aspect ratio.\n"
                             "E.g., 0.5 for cells that are twice as tall as they are wide (like 8px wide, 16px tall).\n"
                             "1.0 for square cells. 2.0 for cells twice as wide as tall.")
    parser.add_argument("--skip_lightest_if_space", action="store_true", default=True,
                        help="If the first character in charset is a space AND maps to the lightest image areas,\n"
                             "don't draw it, letting the true background show. (Default: draw the space).")
    parser.add_argument("-o", "--output", default="char_art_output.png",
                        help="Path to save the output PNG file.")

    args = parser.parse_args()

    image_to_ascii_art(
        args.image_path,
        args.hex_color,
        output_width_chars=args.width_chars,
        charset=args.charset,
        font_path=args.font_path,
        font_size=args.font_size,
        cell_width_px=args.cell_width_px,
        cell_height_px=args.cell_height_px,
        aspect_ratio_correction=args.aspect_ratio_correction,
        posterize_bits=args.posterize_bits,
        skip_lightest_char_if_space=args.skip_lightest_if_space,
        output_path=args.output
    )
