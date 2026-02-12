"""
GS1 Barcode Generation Routes for SupplierComply
Handles GS1-128 (EAN/UCC-128) barcode generation with validation
"""

import io
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import cloudinary
import cloudinary.uploader
from app import db, Product, Activity

logger = logging.getLogger(__name__)
barcode_bp = Blueprint('barcode', __name__, url_prefix='/barcode')


def calculate_gs1_check_digit(gtin_without_check):
    """
    Calculate GS1 check digit using Modulo 10 algorithm.
    
    Args:
        gtin_without_check: GTIN without the check digit (13 digits for GTIN-14)
    
    Returns:
        Check digit (0-9)
    """
    if len(gtin_without_check) != 13:
        raise ValueError("GTIN-14 requires 13 digits before check digit")
    
    # Multiply odd positions by 3, even positions by 1
    total = 0
    for i, digit in enumerate(gtin_without_check):
        d = int(digit)
        if i % 2 == 0:  # Odd position (0-indexed)
            total += d * 3
        else:  # Even position
            total += d
    
    # Check digit is the number needed to round up to nearest 10
    check_digit = (10 - (total % 10)) % 10
    return check_digit


def validate_gtin(gtin):
    """
    Validate GTIN format and check digit.
    
    Args:
        gtin: Full GTIN with check digit
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not gtin:
        return False, "GTIN is required"
    
    # Remove any whitespace
    gtin = gtin.strip()
    
    # Check length (GTIN-14 is standard for GS1-128)
    if len(gtin) != 14:
        return False, "GTIN must be 14 digits"
    
    # Check all characters are digits
    if not gtin.isdigit():
        return False, "GTIN must contain only digits"
    
    # Validate check digit
    try:
        calculated_check = calculate_gs1_check_digit(gtin[:-1])
        if calculated_check != int(gtin[-1]):
            return False, f"Invalid check digit. Expected {calculated_check}"
    except Exception as e:
        return False, f"Check digit validation failed: {str(e)}"
    
    return True, None


def generate_gtin_14():
    """
    Generate a valid GTIN-14 barcode number.
    Uses indicator digit 0 (standard case) + 12-digit company prefix + item reference.
    For demo purposes, generates a random valid GTIN.
    
    Returns:
        Valid 14-digit GTIN string
    """
    import random
    
    # Indicator digit (0 = standard case, 1-8 = cases with different quantities, 9 = variable)
    indicator = '0'
    
    # Generate 12 random digits (in production, this would be based on company's GS1 prefix)
    random_digits = ''.join([str(random.randint(0, 9)) for _ in range(12)])
    
    # Combine for GTIN without check digit
    gtin_without_check = indicator + random_digits
    
    # Calculate check digit
    check_digit = calculate_gs1_check_digit(gtin_without_check)
    
    return gtin_without_check + str(check_digit)


def create_gs1_128_barcode(data, product_name, add_watermark=False):
    """
    Create GS1-128 barcode image with human-readable text.
    
    Args:
        data: The barcode data (GS1-128 encoded string)
        product_name: Product name to display below barcode
        add_watermark: Whether to add "Free" watermark
    
    Returns:
        PIL Image object
    """
    # Generate barcode using python-barcode library
    Code128 = barcode.get_barcode_class('code128')
    
    # Create barcode writer with custom options
    writer = ImageWriter()
    writer.set_options({
        'module_width': 0.5,  # Width of narrow module in mm
        'module_height': 15.0,  # Height of barcode in mm
        'quiet_zone': 6.5,  # Quiet zone on each side
        'font_size': 10,
        'text_distance': 5.0,
        'background': 'white',
        'foreground': 'black',
        'write_text': True,
        'center_text': True
    })
    
    # Generate barcode
    code = Code128(data, writer=writer)
    barcode_image = code.render()
    
    # Convert to RGB if necessary
    if barcode_image.mode != 'RGB':
        barcode_image = barcode_image.convert('RGB')
    
    # Create new image with extra space for product name
    width, height = barcode_image.size
    new_height = height + 60  # Extra space for product name and watermark
    
    final_image = Image.new('RGB', (width, new_height), 'white')
    final_image.paste(barcode_image, (0, 0))
    
    draw = ImageDraw.Draw(final_image)
    
    # Try to load a font, fallback to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Add product name
    product_text = product_name[:50]  # Limit length
    bbox = draw.textbbox((0, 0), product_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, height + 10), product_text, fill='black', font=font)
    
    # Add human-readable barcode data
    bbox = draw.textbbox((0, 0), data, font=small_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, height + 30), data, fill='black', font=small_font)
    
    # Add watermark for free tier
    if add_watermark:
        watermark_text = "SupplierComply Free"
        try:
            watermark_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            watermark_font = ImageFont.load_default()
        
        # Create semi-transparent overlay
        overlay = Image.new('RGBA', final_image.size, (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        bbox = overlay_draw.textbbox((0, 0), watermark_text, font=watermark_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (width - text_width) // 2
        text_y = (new_height - text_height) // 2
        
        overlay_draw.text((text_x, text_y), watermark_text, fill=(255, 0, 0, 128), font=watermark_font)
        
        # Composite overlay onto final image
        final_image = Image.alpha_composite(final_image.convert('RGBA'), overlay).convert('RGB')
    
    return final_image


def log_activity(user_id, action, details=None):
    """Log user activity."""
    try:
        activity = Activity(user_id=user_id, action=action, details=details)
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to log activity: {str(e)}")
        db.session.rollback()


@barcode_bp.route('/')
@login_required
def index():
    """Render barcode generator page."""
    return render_template('barcode.html')


@barcode_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """
    Generate GS1-128 barcode.
    
    Request body:
        - product_name: Product name (required)
        - batch_number: Batch/lot number (optional)
        - expiry_date: Expiry date YYYY-MM-DD (optional)
        - quantity: Quantity (optional)
        - gtin: GTIN-14 (optional, auto-generated if not provided)
    
    Returns:
        JSON with barcode URL and metadata
    """
    try:
        # Check if user can generate more barcodes
        if not current_user.is_paid():
            barcode_count = current_user.get_barcode_count_this_month()
            if barcode_count >= 10:
                return jsonify({
                    'success': False,
                    'error': 'Free tier limit reached. Upgrade to generate unlimited barcodes.',
                    'upgrade_required': True
                }), 403
        
        data = request.get_json()
        
        # Extract fields
        product_name = data.get('product_name', '').strip()
        batch_number = data.get('batch_number', '').strip()
        expiry_date_str = data.get('expiry_date', '').strip()
        quantity = data.get('quantity')
        gtin = data.get('gtin', '').strip()
        
        # Validate required fields
        if not product_name:
            return jsonify({'success': False, 'error': 'Product name is required'}), 400
        
        # Parse expiry date
        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                if expiry_date < datetime.now().date():
                    return jsonify({'success': False, 'error': 'Expiry date cannot be in the past'}), 400
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid expiry date format. Use YYYY-MM-DD'}), 400
        
        # Validate or generate GTIN
        if gtin:
            is_valid, error = validate_gtin(gtin)
            if not is_valid:
                return jsonify({'success': False, 'error': error}), 400
        else:
            gtin = generate_gtin_14()
        
        # Build GS1-128 data string with Application Identifiers
        # AI (01) = GTIN, (10) = Batch/Lot, (17) = Expiry Date, (30) = Count of items
        gs1_data = f"(01){gtin}"
        if batch_number:
            gs1_data += f"(10){batch_number}"
        if expiry_date:
            # GS1 format: YYMMDD
            expiry_formatted = expiry_date.strftime('%y%m%d')
            gs1_data += f"(17){expiry_formatted}"
        if quantity:
            gs1_data += f"(30){quantity}"
        
        # For barcode rendering, we need to encode without parentheses
        # The FNC1 character is used to separate AIs
        barcode_data = gtin
        if batch_number:
            barcode_data += batch_number
        if expiry_date:
            barcode_data += expiry_date.strftime('%y%m%d')
        if quantity:
            barcode_data += str(quantity)
        
        # Generate barcode image
        add_watermark = not current_user.is_paid()
        barcode_image = create_gs1_128_barcode(barcode_data, product_name, add_watermark)
        
        # Save to buffer
        img_buffer = io.BytesIO()
        barcode_image.save(img_buffer, format='PNG', dpi=(300, 300))
        img_buffer.seek(0)
        
        # Upload to Cloudinary
        try:
            upload_result = cloudinary.uploader.upload(
                img_buffer,
                folder=f"suppliercomply/barcodes/{current_user.id}",
                public_id=f"{gtin}_{int(datetime.utcnow().timestamp())}",
                resource_type="image"
            )
            barcode_url = upload_result['secure_url']
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {str(e)}")
            # Fallback: save locally (in production, you'd want better handling)
            return jsonify({'success': False, 'error': 'Failed to save barcode image'}), 500
        
        # Save product to database
        product = Product(
            user_id=current_user.id,
            name=product_name,
            batch_number=batch_number,
            expiry_date=expiry_date,
            quantity=quantity if quantity else None,
            gtin=gtin,
            barcode_url=barcode_url
        )
        db.session.add(product)
        db.session.commit()
        
        # Log activity
        log_activity(current_user.id, 'generated_barcode', f'Product: {product_name}, GTIN: {gtin}')
        
        # Get updated barcode count
        barcode_count = current_user.get_barcode_count_this_month()
        
        logger.info(f"Barcode generated for user {current_user.id}: {gtin}")
        
        return jsonify({
            'success': True,
            'barcode_url': barcode_url,
            'gtin': gtin,
            'gs1_data': gs1_data,
            'barcode_count_this_month': barcode_count,
            'free_tier_limit': 10 if not current_user.is_paid() else None,
            'watermarked': add_watermark
        }), 201
        
    except Exception as e:
        logger.error(f"Barcode generation error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Barcode generation failed. Please try again.'}), 500


@barcode_bp.route('/history')
@login_required
def history():
    """Get barcode generation history for current user."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        
        query = Product.query.filter_by(user_id=current_user.id)
        
        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        
        products = query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'products': [{
                'id': p.id,
                'name': p.name,
                'batch_number': p.batch_number,
                'expiry_date': p.expiry_date.isoformat() if p.expiry_date else None,
                'quantity': p.quantity,
                'gtin': p.gtin,
                'barcode_url': p.barcode_url,
                'created_at': p.created_at.isoformat()
            } for p in products.items],
            'total': products.total,
            'pages': products.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"History fetch error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch history'}), 500


@barcode_bp.route('/download/<int:product_id>')
@login_required
def download(product_id):
    """Download barcode image for a specific product."""
    try:
        product = Product.query.filter_by(id=product_id, user_id=current_user.id).first()
        
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Redirect to Cloudinary URL for download
        return redirect(product.barcode_url)
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'success': False, 'error': 'Download failed'}), 500


@barcode_bp.route('/stats')
@login_required
def stats():
    """Get barcode generation statistics."""
    try:
        total_barcodes = Product.query.filter_by(user_id=current_user.id).count()
        this_month = current_user.get_barcode_count_this_month()
        
        # Expiring products (if paid)
        expiring_30 = 0
        expiring_60 = 0
        expiring_90 = 0
        
        if current_user.is_paid():
            from datetime import timedelta
            today = datetime.now().date()
            
            expiring_30 = Product.query.filter(
                Product.user_id == current_user.id,
                Product.expiry_date <= today + timedelta(days=30),
                Product.expiry_date >= today
            ).count()
            
            expiring_60 = Product.query.filter(
                Product.user_id == current_user.id,
                Product.expiry_date <= today + timedelta(days=60),
                Product.expiry_date > today + timedelta(days=30)
            ).count()
            
            expiring_90 = Product.query.filter(
                Product.user_id == current_user.id,
                Product.expiry_date <= today + timedelta(days=90),
                Product.expiry_date > today + timedelta(days=60)
            ).count()
        
        return jsonify({
            'success': True,
            'total_barcodes': total_barcodes,
            'this_month': this_month,
            'free_tier_limit': 10 if not current_user.is_paid() else None,
            'expiring_products': {
                '30_days': expiring_30,
                '60_days': expiring_60,
                '90_days': expiring_90
            } if current_user.is_paid() else None
        }), 200
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch stats'}), 500
