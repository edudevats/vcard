#!/usr/bin/env python3
"""
Script to update all ATSCARD PWA icon sizes with the new design
"""

import os

# ATSCARD SVG template with dynamic sizing
def generate_atscard_svg(size):
    # Calculate proportional values based on size
    radius = size * 0.234375  # 45/192 ratio
    inner_radius = size * 0.1979  # 38/192 ratio
    center = size / 2
    text_y = size * 0.859375  # 165/192 ratio
    font_size = size * 0.09375  # 18/192 ratio
    stroke_width = max(1, size * 0.03125)  # 6/192 ratio, minimum 1

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">
  <defs>
    <!-- Background gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6FB7FF;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#8B5CF6;stop-opacity:1" />
    </linearGradient>

    <!-- Circle gradient matching logo -->
    <linearGradient id="circleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#2C3E86;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#17A2B8;stop-opacity:1" />
    </linearGradient>

    <!-- Text gradient -->
    <linearGradient id="textGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#2C3E86;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#17A2B8;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#20C997;stop-opacity:1" />
    </linearGradient>
  </defs>

  <!-- Background with rounded corners -->
  <rect width="{size}" height="{size}" rx="{size * 0.167}" fill="url(#bgGrad)"/>

  <!-- Central circle badge -->
  <circle cx="{center}" cy="{center * 0.885}" r="{radius}" fill="white" opacity="0.95"/>
  <circle cx="{center}" cy="{center * 0.885}" r="{inner_radius}" fill="none" stroke="url(#circleGrad)" stroke-width="{stroke_width}"/>

  <!-- Main content group -->
  <g transform="translate({center},{center * 0.885})">
    <!-- Business cards stack -->
    <g transform="translate({-size * 0.042},{-size * 0.0625})">
      <!-- Back card -->
      <rect x="{size * 0.0104}" y="{size * 0.0104}" width="{size * 0.104}" height="{size * 0.0625}" rx="{size * 0.0104}" fill="#20C997" opacity="0.7"/>
      <!-- Middle card -->
      <rect x="{size * 0.0052}" y="{size * 0.0052}" width="{size * 0.104}" height="{size * 0.0625}" rx="{size * 0.0104}" fill="#17A2B8"/>
      <!-- Front card -->
      <rect x="0" y="0" width="{size * 0.104}" height="{size * 0.0625}" rx="{size * 0.0104}" fill="white" stroke="#2C3E86" stroke-width="{max(0.5, size * 0.0052)}"/>

      <!-- Card details -->
      <rect x="{size * 0.0104}" y="{size * 0.0104}" width="{size * 0.0625}" height="{size * 0.0078}" fill="#2C3E86" opacity="0.7"/>
      <rect x="{size * 0.0104}" y="{size * 0.0234}" width="{size * 0.042}" height="{size * 0.0052}" fill="#17A2B8" opacity="0.7"/>
      <rect x="{size * 0.0104}" y="{size * 0.0338}" width="{size * 0.052}" height="{size * 0.0052}" fill="#20C997" opacity="0.7"/>
    </g>

    <!-- Tools/wrench icon -->
    <g transform="translate({size * 0.042},{-size * 0.042})">
      <!-- Main wrench body -->
      <path d="M0,0 L{size * 0.0104},0 L{size * 0.0104},{size * 0.0625} L0,{size * 0.0625} Z" fill="#2C3E86"/>
      <path d="M{-size * 0.0052},{size * 0.052} L{size * 0.0156},{size * 0.052} L{size * 0.0156},{size * 0.0625} L{-size * 0.0052},{size * 0.0625} Z" fill="#2C3E86"/>

      <!-- Wrench head -->
      <circle cx="{size * 0.0052}" cy="{-size * 0.0104}" r="{size * 0.0156}" fill="none" stroke="#2C3E86" stroke-width="{max(0.8, size * 0.0078)}"/>
      <circle cx="{size * 0.0052}" cy="{-size * 0.0104}" r="{size * 0.0078}" fill="#17A2B8"/>

      <!-- Small tool -->
      <path d="M{size * 0.031},{size * 0.0104} L{size * 0.042},0 L{size * 0.052},{size * 0.0104} L{size * 0.042},{size * 0.021} Z" fill="#20C997"/>
      <line x1="{size * 0.042}" y1="{size * 0.0104}" x2="{size * 0.042}" y2="{size * 0.042}" stroke="#20C997" stroke-width="{max(0.5, size * 0.0052)}"/>
    </g>

    <!-- WiFi/connection symbol -->
    <g transform="translate({size * 0.094},{-size * 0.026})">
      <path d="M0,0 Q{size * 0.021},{-size * 0.021} {size * 0.042},0" stroke="#17A2B8" stroke-width="{max(0.8, size * 0.0078)}" fill="none" opacity="0.8"/>
      <path d="M{size * 0.0052},{size * 0.0104} Q{size * 0.021},{-size * 0.0052} {size * 0.0365},{size * 0.0104}" stroke="#17A2B8" stroke-width="{max(0.6, size * 0.00625)}" fill="none" opacity="0.8"/>
      <circle cx="{size * 0.021}" cy="{size * 0.021}" r="{max(0.5, size * 0.0052)}" fill="#17A2B8" opacity="0.8"/>
    </g>
  </g>

  <!-- App name with gradient -->
  <text x="{center}" y="{text_y}" text-anchor="middle" fill="url(#textGrad)" font-family="Arial Black, sans-serif" font-size="{font_size}" font-weight="900">ATSCARD</text>
</svg>'''

# Icon sizes to generate
icon_sizes = [72, 96, 128, 144, 152, 192, 384, 512]

# Generate all icon files
current_dir = os.path.dirname(os.path.abspath(__file__))

for size in icon_sizes:
    filename = f"icon-{size}x{size}.svg"
    filepath = os.path.join(current_dir, filename)

    svg_content = generate_atscard_svg(size)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    print(f"Generated: {filename}")

print("\nAll ATSCARD PWA icons have been updated!")