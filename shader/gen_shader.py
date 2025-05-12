#!/usr/bin/env python3

import argparse
import math
from PIL import Image, ImageDraw, ImageOps

def hex_to_rgb(hex_color):
    """Converts a hex color string (e.g., '#RRGGBB') to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError("Invalid hex color format. Use #RRGGBB.")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def generate_shades(base_rgb, num_shades=5, bg_brightness_factor=0.1):
    """
    Generates a list of RGB color shades based on the base color.
    Includes a dark background shade and progressively lighter shades up to near white.
    """
    if num_shades < 2:
        raise ValueError("Number of shades must be at least 2.")

    shades = []
    base_r, base_g, base_b = base_rgb

    # 1. Background shade (very dark version of base color)
    bg_r = int(base_r * bg_brightness_factor)
    bg_g = int(base_g * bg_brightness_factor)
    bg_b = int(base_b * bg_brightness_factor)
    shades.append((bg_r, bg_g, bg_b))

    # 2. Intermediate shades from background to base color
    # We need num_shades - 2 intermediate steps + the base color itself
    steps_to_base = (num_shades - 1) // 2 
    if steps_to_base > 0:
        for i in range(1, steps_to_base + 1):
            factor = i / (steps_to_base + 1) # Interpolation factor towards base
            r = int(bg_r + (base_r - bg_r) * factor)
            g = int(bg_g + (base_g - bg_g) * factor)
            b = int(bg_b + (base_b - bg_b) * factor)
            shades.append((r, g, b))

    # 3. Base color itself (if num_shades is odd, this is the middle)
    shades.append(base_rgb)
    
    # 4. Intermediate shades from base color to near white
    steps_to_white = num_shades - len(shades)
    if steps_to_white > 0:
        for i in range(1, steps_to_white + 1):
            factor = i / (steps_to_white + 1) # Interpolation factor towards white
            r = int(base_r + (255 - base_r) * factor)
            g = int(base_g + (255 - base_g) * factor)
            b = int(base_b + (255 - base_b) * factor)
            # Clamp values to 255
            shades.append((min(r, 255), min(g, 255), min(b, 255)))
            
    # Ensure the final list has exactly num_shades
    # This logic might slightly over/undershoot depending on num_shades even/odd
    # Let's refine the distribution slightly to be more even across the spectrum
    
    shades = []
    # Calculate shades from dark to light linearly based on brightness factor
    # Shade 0 = darkest, Shade N-1 = lightest
    for i in range(num_shades):
        # Interpolate brightness factor from bg_brightness_factor to ~1.8 (allows going lighter than base)
        # Adjust the range/curve as needed. This aims for base color around the middle.
        
        # Let's try a simpler approach: Interpolate between black, base, and white
        # Shade 0: Darkest (derived from base)
        # Shade mid: Base
        # Shade N-1: Lightest (derived from base, towards white)
        
        # Simplified Linear Interpolation: Dark -> Base -> Light
        mid_point_index = (num_shades - 1) / 2.0 
        
        if i < mid_point_index:
            # Interpolate between background and base
            factor = i / mid_point_index
            r = int(bg_r + (base_r - bg_r) * factor)
            g = int(bg_g + (base_g - bg_g) * factor)
            b = int(bg_b + (base_b - bg_b) * factor)
        elif i > mid_point_index:
             # Interpolate between base and white
            factor = (i - mid_point_index) / (num_shades - 1 - mid_point_index)
            r = int(base_r + (255 - base_r) * factor)
            g = int(base_g + (255 - base_g) * factor)
            b = int(base_b + (255 - base_b) * factor)
        else: # i == mid_point_index (only if num_shades is odd)
            r, g, b = base_r, base_g, base_b

        shades.append((min(max(r, 0), 255), min(max(g, 0), 255), min(max(b, 0), 255)))

    # Ensure the background shade is distinctly dark
    shades[0] = (int(base_r * bg_brightness_factor), 
                 int(base_g * bg_brightness_factor), 
                 int(base_b * bg_brightness_factor))

    print(f"Generated {len(shades)} shades: {shades}")
    return shades

def image_to_ascii_art(image_path, hex_color, width=80, num_shades=5, cell_width=8, cell_height=16, output_path="output.png", aspect_ratio_correction=0.5):
    """
    Generates ASCII-style art PNG from an image.
    """
    try:
        base_rgb = hex_to_rgb(hex_color)
    except ValueError as e:
        print(f"Error: {e}")
        return

    try:
        shades = generate_shades(base_rgb, num_shades)
    except ValueError as e:
        print(f"Error: {e}")
        return

    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        print(f"Error: Input image file not found at '{image_path}'")
        return
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # Convert to grayscale for brightness analysis
    img_gray = img.convert("L")

    # Calculate target height based on width and aspect ratio correction
    original_width, original_height = img_gray.size
    aspect_ratio = original_height / original_width
    # Adjust height based on character aspect ratio (terminals are often ~2:1 height:width)
    height = int(width * aspect_ratio * aspect_ratio_correction)
    if height < 1: height = 1 # Ensure height is at least 1

    # Resize the image to the target low resolution
    img_resized = img_gray.resize((width, height), Image.Resampling.LANCZOS)

    # --- Create the output PNG canvas ---
    output_img_width = width * cell_width
    output_img_height = height * cell_height
    
    # Use the darkest shade as the image background
    output_img = Image.new("RGB", (output_img_width, output_img_height), color=shades[0])
    draw = ImageDraw.Draw(output_img)

    # --- Draw the "pixels" ---
    grayscale_step = 256 / num_shades

    for y in range(height):
        for x in range(width):
            # Get the brightness of the pixel (0-255)
            brightness = img_resized.getpixel((x, y))

            # Determine which shade corresponds to the brightness
            # Brighter pixels get higher shade index
            shade_index = min(int(brightness / grayscale_step), num_shades - 1)
            
            # Get the color for this shade
            color = shades[shade_index]

            # Calculate the drawing position
            draw_x = x * cell_width
            draw_y = y * cell_height

            # Draw the rectangle (representing the character cell)
            # Don't draw if it's the background color (optimization/effect)
            if shade_index > 0: 
                 draw.rectangle(
                    [draw_x, draw_y, draw_x + cell_width -1, draw_y + cell_height -1], # Subtract 1 for slight gap? Optional.
                    fill=color
                 )
                 # To draw circles instead (like your example):
                 # draw.ellipse(
                 #    [draw_x, draw_y, draw_x + cell_width -1, draw_y + cell_height -1],
                 #    fill=color
                 # )


    # Save the final image
    try:
        output_img.save(output_path, "PNG")
        print(f"ASCII-style art saved to '{output_path}'")
    except Exception as e:
        print(f"Error saving image: {e}")

# --- Main execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate low-res ASCII-style shaded art from an image.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Shows default values
    )
    parser.add_argument("image_path", help="Path to the input image file.")
    parser.add_argument("hex_color", help="Base hex color code (e.g., '#44ccaa').")
    parser.add_argument("-w", "--width", type=int, default=80,
                        help="Width of the output art in 'character' cells.")
    parser.add_argument("-s", "--shades", type=int, default=5,
                        help="Number of color shades to use (including background).")
    parser.add_argument("-cw", "--cell_width", type=int, default=10,
                        help="Width of each character cell in pixels.")
    parser.add_argument("-ch", "--cell_height", type=int, default=16,
                        help="Height of each character cell in pixels.")
    parser.add_argument("-ar", "--aspect_ratio_correction", type=float, default=0.6,
                        help="Correction factor for character height vs width (0.6 is typical for terminals).")                    
    parser.add_argument("-o", "--output", default="ascii_art_output.png",
                        help="Path to save the output PNG file.")

    args = parser.parse_args()

    image_to_ascii_art(
        args.image_path,
        args.hex_color,
        width=args.width,
        num_shades=args.shades,
        cell_width=args.cell_width,
        cell_height=args.cell_height,
        output_path=args.output,
        aspect_ratio_correction=args.aspect_ratio_correction
    )
