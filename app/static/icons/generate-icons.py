#!/usr/bin/env python3
"""
Script to generate PWA SVG icons for ATSCARD
Uses existing logo SVG files and adapts them for different icon sizes
"""
import os
import re

# Icon sizes for PWA
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

def read_svg_file(file_path):
    """Read SVG file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def modify_svg_for_size(svg_content, target_size, scale_content=False):
    """Modify SVG content to fit target size"""

    if scale_content:
        # For logos that need to be scaled to fit properly
        # Extract current width and height from SVG attributes
        width_match = re.search(r'width="([^"]*)"', svg_content)
        height_match = re.search(r'height="([^"]*)"', svg_content)

        if width_match and height_match:
            # Extract numeric values
            orig_width_str = width_match.group(1).replace('px', '')
            orig_height_str = height_match.group(1).replace('px', '')

            try:
                orig_width = float(orig_width_str)
                orig_height = float(orig_height_str)
            except ValueError:
                # Fallback if parsing fails
                orig_width = orig_height = 512

            # Calculate scale factor to fit within target size with some padding
            padding_factor = 0.9  # 90% of target size to leave some padding
            target_with_padding = target_size * padding_factor

            scale_factor = min(target_with_padding / orig_width, target_with_padding / orig_height)

            # Calculate new dimensions and centering offset
            new_width = orig_width * scale_factor
            new_height = orig_height * scale_factor
            offset_x = (target_size - new_width) / 2
            offset_y = (target_size - new_height) / 2

            # Find the opening <svg> tag and its content
            svg_start_match = re.search(r'(<svg[^>]*>)(.*)(</svg>)', svg_content, re.DOTALL)
            if svg_start_match:
                svg_opening = svg_start_match.group(1)
                svg_inner_content = svg_start_match.group(2)
                svg_closing = svg_start_match.group(3)

                # Update the svg opening tag
                svg_opening = re.sub(r'width="[^"]*"', f'width="{target_size}"', svg_opening)
                svg_opening = re.sub(r'height="[^"]*"', f'height="{target_size}"', svg_opening)
                svg_opening = re.sub(r'viewBox="[^"]*"', f'viewBox="0 0 {target_size} {target_size}"', svg_opening)

                # Wrap inner content with scaling and centering transform
                transformed_content = f'<g transform="translate({offset_x},{offset_y}) scale({scale_factor})">{svg_inner_content}</g>'

                svg_content = svg_opening + transformed_content + svg_closing
    else:
        # Simple resize for logos that don't need scaling
        # Update viewBox to match target size (keep original proportions)
        svg_content = re.sub(
            r'viewBox="[^"]*"',
            f'viewBox="0 0 {target_size} {target_size}"',
            svg_content
        )

        # Update width and height attributes
        svg_content = re.sub(
            r'width="[^"]*"',
            f'width="{target_size}"',
            svg_content
        )
        svg_content = re.sub(
            r'height="[^"]*"',
            f'height="{target_size}"',
            svg_content
        )

    return svg_content

def generate_icon_from_logo(logo_path, size, output_path, scale_content=False):
    """Generate an icon of specific size from logo"""
    svg_content = read_svg_file(logo_path)
    if not svg_content:
        return False

    # Modify SVG for the target size
    modified_svg = modify_svg_for_size(svg_content, size, scale_content)

    # Write the modified SVG
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(modified_svg)
        return True
    except Exception as e:
        print(f"Error writing {output_path}: {e}")
        return False

def convert_logo_to_icons():
    """Convert existing ATSCARD logos to PWA icon formats"""
    base_dir = os.path.dirname(__file__)
    logo_with_text_path = os.path.join(base_dir, '../logo/logosinletras.svg')
    logo_without_text_path = os.path.join(base_dir, '../logo/logosinletras.svg')

    # Check if logos exist
    if not os.path.exists(logo_with_text_path):
        print(f"Logo with text not found at: {logo_with_text_path}")
        return False

    if not os.path.exists(logo_without_text_path):
        print(f"Logo without text not found at: {logo_without_text_path}")
        return False

    print("Generating SVG icons from existing ATSCARD logos...")

    try:
        # Generate icons for each size
        for size in ICON_SIZES:
            # Use logo without text for small sizes (72x72 and 96x96)
            if size <= 96:
                logo_path = logo_without_text_path
                scale_content = True  # Scale the logo without text to fit properly
                print(f"Using logo without text for {size}x{size} (with scaling)")
            else:
                logo_path = logo_with_text_path
                scale_content = True  # Also scale the logo with text to fit properly
                print(f"Using logo with text for {size}x{size} (with scaling)")

            # Generate the icon
            output_path = os.path.join(base_dir, f'icon-{size}x{size}.svg')

            if generate_icon_from_logo(logo_path, size, output_path, scale_content):
                print(f'Created icon-{size}x{size}.svg')
            else:
                print(f'Failed to create icon-{size}x{size}.svg')
                return False

        return True

    except Exception as e:
        print(f"Error creating SVG icons: {e}")
        return False

def generate_icons():
    """Generate all PWA icons from existing logos"""
    print("ATSCARD PWA Icon Generator")
    print("=" * 30)

    if convert_logo_to_icons():
        print("\nAll PWA SVG icons generated successfully!")
        print("\nGenerated files:")

        base_dir = os.path.dirname(__file__)
        for size in ICON_SIZES:
            svg_file = f'icon-{size}x{size}.svg'
            if os.path.exists(os.path.join(base_dir, svg_file)):
                print(f"  {svg_file}")
    else:
        print("\nFailed to generate icons. Please check that logo files exist.")

if __name__ == '__main__':
    generate_icons()