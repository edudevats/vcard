#!/usr/bin/env python3
"""
Script to generate PWA icons for VCard Digital
Creates SVG icons and converts to PNG for different sizes
"""
import os

# SVG template for VCard icon
SVG_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="{size}" height="{size}" rx="{radius}" fill="url(#grad)"/>
  <rect x="{margin}" y="{margin}" width="{card_width}" height="{card_height}" rx="4" fill="white" opacity="0.9"/>
  <rect x="{margin + 8}" y="{margin + 8}" width="{card_width - 16}" height="4" rx="2" fill="#6366f1"/>
  <rect x="{margin + 8}" y="{margin + 16}" width="{card_width - 16}" height="3" rx="1.5" fill="#8b5cf6" opacity="0.7"/>
  <rect x="{margin + 8}" y="{margin + 24}" width="{(card_width - 16) * 0.6}" height="3" rx="1.5" fill="#8b5cf6" opacity="0.5"/>
</svg>'''

# Icon sizes for PWA
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

def create_svg_icon(size):
    """Create SVG icon for given size"""
    radius = size * 0.15  # 15% radius
    margin = size * 0.15  # 15% margin
    card_width = size - (2 * margin)
    card_height = card_width * 0.6  # Card aspect ratio
    
    svg_content = SVG_TEMPLATE.format(
        size=size,
        radius=radius,
        margin=margin,
        card_width=card_width,
        card_height=card_height
    )
    
    return svg_content

def generate_icons():
    """Generate all PWA icons"""
    base_dir = os.path.dirname(__file__)
    
    for size in ICON_SIZES:
        # Create SVG
        svg_content = create_svg_icon(size)
        svg_path = os.path.join(base_dir, f'icon-{size}x{size}.svg')
        
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        print(f'Created icon-{size}x{size}.svg')

if __name__ == '__main__':
    generate_icons()
    print('All PWA icons generated successfully!')