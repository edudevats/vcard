import os
import secrets
import io
import base64
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename
import qrcode
from qrcode.image.pil import PilImage

# Configuración de seguridad para uploads
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB máximo
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
ALLOWED_PIL_FORMATS = {'JPEG', 'PNG', 'WEBP'}

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_content(file):
    """
    Validate file content for security:
    - Check file size
    - Verify it's a valid image using PIL
    - Ensure format matches extension
    Returns: (is_valid, error_message)
    """
    if not file:
        return False, "No se proporcionó archivo"
    
    # Reset file pointer to beginning
    file.seek(0)
    
    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        return False, f"El archivo es demasiado grande. Máximo permitido: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if size == 0:
        return False, "El archivo está vacío"
    
    # Try to open with PIL to ensure it's a valid image
    try:
        img = Image.open(file)
        
        # Check if detected format is allowed
        if img.format not in ALLOWED_PIL_FORMATS:
            return False, f"Formato de imagen no permitido. Se detectó: {img.format}"
        
        # Verify it's a valid image
        img.verify()
        file.seek(0)  # Reset after verify
        
        # Re-open for format check (verify() closes the image)
        img = Image.open(file)
        
        # Additional security check: ensure image format matches extension
        if not filename_extension_matches_format(file.filename, img.format):
            return False, "La extensión del archivo no coincide con el formato de imagen"
        
        file.seek(0)  # Reset to beginning
            
    except Exception as e:
        return False, f"El archivo no es una imagen válida: {str(e)}"
    
    return True, "OK"

def filename_extension_matches_format(filename, image_format):
    """Check if file extension matches PIL detected format"""
    if not filename or not image_format:
        return False
        
    ext = filename.rsplit('.', 1)[1].lower()
    format_ext_map = {
        'JPEG': ['jpg', 'jpeg'],
        'PNG': ['png'],
        'WEBP': ['webp']
    }
    
    expected_extensions = format_ext_map.get(image_format, [])
    return ext in expected_extensions

def sanitize_image(image):
    """
    Remove potentially malicious metadata from image
    and convert to safe format
    """
    try:
        # Convert to RGB if needed (removes transparency and metadata)
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                rgb_image.paste(image, mask=image.split()[-1])
            elif image.mode == 'P' and 'transparency' in image.info:
                image = image.convert('RGBA')
                rgb_image.paste(image, mask=image.split()[-1])
            else:
                rgb_image.paste(image)
            image = rgb_image
        
        # Create new image without metadata
        clean_image = Image.new(image.mode, image.size)
        clean_image.paste(image)
        
        return clean_image
    except Exception:
        return image  # Return original if sanitization fails

def save_image(file, folder, max_size=(800, 800), thumbnail_size=(150, 150)):
    """
    Save an uploaded image with resizing and thumbnail generation
    Returns: (filename, thumbnail_filename) or (None, None) if error
    """
    if not file or not allowed_file(file.filename):
        return None, None
    
    # Validate file content for security
    is_valid, error_msg = validate_file_content(file)
    if not is_valid:
        print(f"File validation error: {error_msg}")
        return None, None
    
    # Generate secure filename
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    filename = f"{secrets.token_hex(16)}{ext}"
    
    # Create paths
    upload_path = os.path.join(current_app.root_path, folder)
    thumbnail_folder = folder.replace('uploads', 'thumbs')
    thumbnail_path = os.path.join(current_app.root_path, thumbnail_folder)
    
    # Ensure directories exist
    os.makedirs(upload_path, exist_ok=True)
    os.makedirs(thumbnail_path, exist_ok=True)
    
    file_path = os.path.join(upload_path, filename)
    thumbnail_file_path = os.path.join(thumbnail_path, filename)
    
    try:
        # Open and process the image
        image = Image.open(file.stream)
        
        # Sanitize image (remove metadata and potential threats)
        image = sanitize_image(image)
        
        # Resize main image
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        image.save(file_path, 'JPEG', quality=85, optimize=True)
        
        # Create thumbnail
        thumbnail = image.copy()
        thumbnail.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        thumbnail.save(thumbnail_file_path, 'JPEG', quality=80, optimize=True)
        
        return filename, filename
    
    except Exception as e:
        print(f"Error saving image: {e}")
        # Clean up any created files on error
        for path in [file_path, thumbnail_file_path]:
            if os.path.exists(path):
                os.remove(path)
        return None, None

def save_avatar(file, square_size=(300, 300), rect_size=(600, 400)):
    """
    Save avatar image creating two optimized versions:
    1. Square version: Intelligently fitted for circular/square avatars
    2. Rectangular version: Preserves aspect ratio for logo/rectangular avatars
    
    Args:
        file: The uploaded file
        square_size: Maximum dimensions for square version
        rect_size: Maximum dimensions for rectangular version
    
    Returns:
        tuple: (square_filename, rect_filename) or (None, None) if error
    """
    if not file or not allowed_file(file.filename):
        return None, None
    
    # Validate file content for security
    is_valid, error_msg = validate_file_content(file)
    if not is_valid:
        print(f"Avatar validation error: {error_msg}")
        return None, None
    
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    base_name = f"avatar_{secrets.token_hex(16)}"
    
    square_filename = f"{base_name}_square.jpg"
    rect_filename = f"{base_name}_rect.jpg"
    
    upload_path = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_path, exist_ok=True)
    
    square_path = os.path.join(upload_path, square_filename)
    rect_path = os.path.join(upload_path, rect_filename)
    
    try:
        # Open and prepare the original image
        original_image = Image.open(file.stream)
        
        # Sanitize image (remove metadata and potential threats)
        original_image = sanitize_image(original_image)
        
        # Create SQUARE version (for circle, rounded, square avatars)
        square_image = original_image.copy()
        width, height = square_image.size
        
        # Smart square fitting: if image is already roughly square, just resize
        aspect_ratio = width / height
        if 0.8 <= aspect_ratio <= 1.2:  # Almost square (within 20%)
            # Just resize maintaining aspect ratio
            square_image.thumbnail(square_size, Image.Resampling.LANCZOS)
            
            # If needed, pad to make it perfectly square
            w, h = square_image.size
            if w != h:
                size = max(w, h)
                square_bg = Image.new('RGB', (size, size), (255, 255, 255))
                offset = ((size - w) // 2, (size - h) // 2)
                square_bg.paste(square_image, offset)
                square_image = square_bg
        else:
            # For very rectangular images, crop to square from center
            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            square_image = square_image.crop((left, top, left + size, top + size))
            square_image = square_image.resize(square_size, Image.Resampling.LANCZOS)
        
        # Create RECTANGULAR version (preserves original aspect ratio)
        rect_image = original_image.copy()
        rect_image.thumbnail(rect_size, Image.Resampling.LANCZOS)
        
        # Save both versions
        square_image.save(square_path, 'JPEG', quality=90, optimize=True)
        rect_image.save(rect_path, 'JPEG', quality=90, optimize=True)
        
        return square_filename, rect_filename
    
    except Exception as e:
        print(f"Error saving avatar: {e}")
        # Clean up any created files on error
        for path in [square_path, rect_path]:
            if os.path.exists(path):
                os.remove(path)
        return None, None

def delete_file(file_path):
    """Safely delete a file if it exists"""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    from flask import abort
    from flask_login import current_user
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def get_user_card_or_404(card_id):
    """Get user's card by ID or return 404"""
    from flask_login import current_user
    from flask import abort
    from .models import Card
    
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first()
    if not card:
        abort(404)
    return card

def cleanup_files(file_paths):
    """Clean up multiple files safely"""
    if not file_paths:
        return
    
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    
    for file_path in file_paths:
        if file_path:
            try:
                full_path = os.path.join(current_app.root_path, 'static', 'uploads', file_path)
                delete_file(full_path)
            except Exception:
                pass  # Ignore cleanup errors

def validate_email_unique(email, exclude_user_id=None):
    """Validate email uniqueness across users (case-insensitive)"""
    from .models import User
    
    # Normalize email for case-insensitive comparison
    normalized_email = email.lower().strip() if email else email
    
    query = User.query.filter_by(email=normalized_email)
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    
    return query.first() is None

def generate_qr_code(data, size=(300, 300), border=4, fill_color="black", back_color="white", error_correction="M"):
    """
    Generate QR code for given data
    Returns: PIL Image object
    """
    # Set error correction level
    error_levels = {
        "L": qrcode.constants.ERROR_CORRECT_L,  # ~7% correction
        "M": qrcode.constants.ERROR_CORRECT_M,  # ~15% correction
        "Q": qrcode.constants.ERROR_CORRECT_Q,  # ~25% correction
        "H": qrcode.constants.ERROR_CORRECT_H,  # ~30% correction (best for logos)
    }
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=error_levels.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
        box_size=10,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color=fill_color, back_color=back_color, image_factory=PilImage)
    
    # Resize to desired size
    qr_img = qr_img.resize(size, Image.Resampling.LANCZOS)
    
    return qr_img

def generate_qr_code_with_logo(data, logo_path=None, size=(300, 300)):
    """
    Generate high-quality QR code with optional logo in the center
    Based on the qrejemplo.py implementation
    Returns: PIL Image object
    """
    from PIL import ImageDraw
    
    # Generate QR with high error correction for logo compatibility
    qr_img = generate_qr_code(data, size=size, back_color="white", fill_color="black", 
                             border=4, error_correction="H")
    
    if not logo_path or not os.path.exists(logo_path):
        return qr_img
    
    try:
        # Convert QR to RGBA for transparency support
        qr_img = qr_img.convert('RGBA')
        
        # Calculate center area for logo (about 1/3 of QR code size) - exact same as example
        qr_width, qr_height = qr_img.size
        logo_size = min(qr_width, qr_height) // 3
        
        # Create a transparent square in the center - exact same as example
        draw = ImageDraw.Draw(qr_img)
        center_x = (qr_width - logo_size) // 2
        center_y = (qr_height - logo_size) // 2
        draw.rectangle(
            [(center_x, center_y), (center_x + logo_size, center_y + logo_size)],
            fill=(255, 255, 255, 0)  # Transparent
        )
        
        # Round the outer corners of the QR code - exact same as example
        mask = Image.new('L', qr_img.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [(0, 0), qr_img.size],
            radius=20,  # Fixed radius like your example
            fill=255
        )
        qr_img.putalpha(mask)
        
        # Open and prepare logo - simplified like your example
        logo = Image.open(logo_path).convert('RGBA')
        
        # Remove logo background if it exists - exact same logic as your example
        if logo.mode == 'RGBA':
            # Create a transparent background
            new_logo = Image.new('RGBA', logo.size, (0, 0, 0, 0))
            # Paste logo preserving transparency
            new_logo.paste(logo, (0, 0), logo)
            logo = new_logo
        
        # Resize logo to fit the transparent area - exact same as example
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Calculate position to center the logo - exact same as example
        logo_position = (center_x, center_y)
        
        # Paste logo into the transparent center - exact same as example
        qr_img.paste(logo, logo_position, logo)
        
    except Exception as e:
        print(f"Error adding logo to QR code: {e}")
        # Return basic QR on error
        return generate_qr_code(data, size=size, back_color="white", fill_color="black")
    
    return qr_img

def generate_qr_code_with_logo_themed(data, logo_path=None, card_theme=None, size=(300, 300)):
    """
    Generate high-quality QR code with logo and theme colors
    Returns: PIL Image object
    """
    # Use theme colors with validation
    fill_color = "black"  # default fallback
    
    if card_theme and card_theme.primary_color:
        hex_color = card_theme.primary_color.strip()
        if hex_color.startswith('#') and len(hex_color) == 7:
            try:
                int(hex_color[1:], 16)
                fill_color = hex_color
            except ValueError:
                fill_color = "black"
        elif hex_color.startswith('#') and len(hex_color) == 4:
            try:
                hex_expanded = '#' + ''.join([c*2 for c in hex_color[1:]])
                int(hex_expanded[1:], 16)
                fill_color = hex_expanded
            except ValueError:
                fill_color = "black"
    
    # Generate themed QR code with high error correction
    qr_img = generate_qr_code(data, size=size, back_color="white", fill_color=fill_color, 
                             border=4, error_correction="H")
    
    if logo_path and os.path.exists(logo_path):
        try:
            from PIL import ImageDraw
            
            # Convert QR to RGBA for transparency support
            qr_img = qr_img.convert('RGBA')
            
            # Calculate center area for logo (about 1/3 of QR code size) - same as example
            qr_width, qr_height = qr_img.size
            logo_size = min(qr_width, qr_height) // 3
            
            # Create a transparent square in the center - same as example
            draw = ImageDraw.Draw(qr_img)
            center_x = (qr_width - logo_size) // 2
            center_y = (qr_height - logo_size) // 2
            draw.rectangle(
                [(center_x, center_y), (center_x + logo_size, center_y + logo_size)],
                fill=(255, 255, 255, 0)  # Transparent
            )
            
            # Round the outer corners of the QR code - same as example
            mask = Image.new('L', qr_img.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle(
                [(0, 0), qr_img.size],
                radius=20,  # Fixed radius like example
                fill=255
            )
            qr_img.putalpha(mask)
            
            # Open and prepare logo - same logic as example
            logo = Image.open(logo_path).convert('RGBA')
            
            # Remove logo background if it exists - same as example
            if logo.mode == 'RGBA':
                # Create a transparent background
                new_logo = Image.new('RGBA', logo.size, (0, 0, 0, 0))
                # Paste logo preserving transparency
                new_logo.paste(logo, (0, 0), logo)
                logo = new_logo
            
            # Resize logo to fit the transparent area - same as example
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Calculate position to center the logo - same as example
            logo_position = (center_x, center_y)
            
            # Paste logo into the transparent center - same as example
            qr_img.paste(logo, logo_position, logo)
            
        except Exception as e:
            print(f"Error adding themed logo to QR code: {e}")
    
    return qr_img

def generate_styled_qr_code(data, card_theme, size=(300, 300)):
    """
    Generate QR code with card theme colors
    Returns: PIL Image object
    """
    # Use theme colors with proper validation
    fill_color = "black"  # default fallback
    
    if card_theme and card_theme.primary_color:
        # Validate hex color format
        hex_color = card_theme.primary_color.strip()
        if hex_color.startswith('#') and len(hex_color) == 7:
            try:
                # Test if it's a valid hex color
                int(hex_color[1:], 16)
                fill_color = hex_color
            except ValueError:
                fill_color = "black"
        elif hex_color.startswith('#') and len(hex_color) == 4:
            # Convert short hex to full hex (e.g., #abc to #aabbcc)
            try:
                hex_expanded = '#' + ''.join([c*2 for c in hex_color[1:]])
                int(hex_expanded[1:], 16)
                fill_color = hex_expanded
            except ValueError:
                fill_color = "black"
    
    qr_img = generate_qr_code(data, size=size, fill_color=fill_color, back_color="white")
    
    return qr_img

def qr_to_base64(qr_img, format='PNG'):
    """
    Convert PIL Image to base64 string for inline display
    Returns: base64 string
    """
    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format=format)
    img_buffer.seek(0)
    
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    return f"data:image/{format.lower()};base64,{img_base64}"

def save_qr_code(qr_img, filename, folder='static/qr_codes'):
    """
    Save QR code image to disk
    Returns: file path or None if error
    """
    try:
        # Create folder if it doesn't exist
        folder_path = os.path.join(current_app.root_path, folder)
        os.makedirs(folder_path, exist_ok=True)
        
        # Generate secure filename
        secure_name = secure_filename(filename)
        if not secure_name.endswith('.png'):
            secure_name += '.png'
        
        file_path = os.path.join(folder_path, secure_name)
        
        # Save image
        qr_img.save(file_path, 'PNG')
        
        # Return relative path
        return os.path.join(folder, secure_name).replace('\\', '/')
        
    except Exception as e:
        print(f"Error saving QR code: {e}")
        return None