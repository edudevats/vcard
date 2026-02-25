import qrcode
from PIL import Image, ImageDraw
import os

def create_qr_with_logo(website_url, logo_path, output_path="qr_with_logo.png"):
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    # Add website URL to QR code
    qr.add_data(website_url)
    qr.make(fit=True)
    
    # Create basic QR code image (without rounded modules)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
    
    # Calculate center area for logo (about 1/3 of QR code size)
    qr_width, qr_height = qr_img.size
    logo_size = min(qr_width, qr_height) // 3
    
    # Create a transparent square in the center
    draw = ImageDraw.Draw(qr_img)
    center_x = (qr_width - logo_size) // 2
    center_y = (qr_height - logo_size) // 2
    draw.rectangle(
        [(center_x, center_y), (center_x + logo_size, center_y + logo_size)],
        fill=(255, 255, 255, 0)  # Transparent
    )
    
    # Round the outer corners of the QR code
    mask = Image.new('L', qr_img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [(0, 0), qr_img.size],
        radius=20,  # Adjust this value for more/less rounding
        fill=255
    )
    qr_img.putalpha(mask)
    
    # Open and prepare logo
    try:
        logo = Image.open(logo_path).convert('RGBA')
        # Remove logo background if it exists
        if logo.mode == 'RGBA':
            # Create a transparent background
            new_logo = Image.new('RGBA', logo.size, (0,0,0,0))
            # Paste logo preserving transparency
            new_logo.paste(logo, (0,0), logo)
            logo = new_logo
    except FileNotFoundError:
        print(f"Error: Logo file not found at {logo_path}")
        return
    
    # Resize logo to fit the transparent area
    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
    
    # Calculate position to center the logo
    logo_position = (center_x, center_y)
    
    # Paste logo into the transparent center
    qr_img.paste(logo, logo_position, logo)
    
    # Save the final QR code
    try:
        qr_img.save(output_path)
        print(f"QR code saved successfully as {output_path}")
    except Exception as e:
        print(f"Error saving QR code: {e}")

# Example usage
if __name__ == "__main__":
    # Replace these with your actual website URL and logo path
    my_website = "https://www.thecybernetwork.com.br"
    my_logo = "/home/kalicat/Pictures/logo.png"  # Can be .png or .jpg
    
    # Check if logo file exists
    if not os.path.exists(my_logo):
        print("Please provide a valid path to your logo file")
    else:
        create_qr_with_logo(
            website_url=my_website,
            logo_path=my_logo,
            output_path="my_website_qr.png"
        )