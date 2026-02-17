"""
Barcode Generation Routes for SupplierComply
Handles GS1 barcode generation and Cloudinary upload
"""

import logging
import time
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from barcode import Code128
from barcode.writer import ImageWriter
from io import BytesIO
import cloudinary.uploader

# Import from extensions and models (no circular import issue)
from extensions import db
from models import Product, Activity

logger = logging.getLogger(__name__)
barcode_bp = Blueprint('barcode', __name__, url_prefix='/barcode')


@barcode_bp.route('/')
@login_required
def index():
    """Render barcode generation page."""
    if not current_user.can_access():
        return jsonify({'success': False, 'error': 'Subscription required'}), 403
    return render_template('barcode.html')


@barcode_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """Generate GS1 barcode."""
    if not current_user.can_access():
        return jsonify({'success': False, 'error': 'Subscription required'}), 403
    
    try:
        # Try to get JSON data first, fallback to form data
        data = request.get_json()
        if data is None:
            # Fallback to form data
            data = request.form
        
        # FIX: Use 'product_name' to match frontend, fallback to 'name' for compatibility
        name = data.get('product_name', '').strip() or data.get('name', '').strip()
        batch_number = data.get('batch_number', '').strip()
        expiry_date = data.get('expiry_date')
        quantity = data.get('quantity', 1)
        
        # Convert quantity to int if it's a string
        if isinstance(quantity, str):
            quantity = int(quantity) if quantity.isdigit() else 1
        
        if not name:
            return jsonify({'success': False, 'error': 'Product name is required'}), 400
        
        # Generate GTIN (14 digits)
        gtin = generate_gtin(current_user.id)
        
        # Generate barcode
        barcode_value = f"(01){gtin}(10){batch_number}(17){expiry_date.replace('-', '') if expiry_date else ''}"
        
        # Create barcode image
        code128 = Code128(barcode_value, writer=ImageWriter())
        buffer = BytesIO()
        code128.write(buffer)
        buffer.seek(0)
        
        # Upload to Cloudinary
        try:
            upload_result = cloudinary.uploader.upload(
                buffer,
                folder=f"barcodes/user_{current_user.id}",
                public_id=f"barcode_{gtin}"
            )
            barcode_url = upload_result['secure_url']
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {str(e)}")
            return jsonify({'success': False, 'error': 'Failed to upload barcode image'}), 500
        
        # Save to database
        product = Product(
            user_id=current_user.id,
            name=name,
            batch_number=batch_number,
            expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None,
            quantity=quantity,
            gtin=gtin,
            barcode_url=barcode_url
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Log activity
        activity = Activity(
            user_id=current_user.id,
            action='barcode_generated',
            details=f'Product: {name}, GTIN: {gtin}'
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Barcode generated successfully',
            'barcode_url': barcode_url,
            'gtin': gtin
        }), 201
        
    except Exception as e:
        logger.error(f"Barcode generation error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to generate barcode'}), 500
        
        # Save to database
        product = Product(
            user_id=current_user.id,
            name=name,
            batch_number=batch_number,
            expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None,
            quantity=quantity,
            gtin=gtin,
            barcode_url=barcode_url
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Log activity
        activity = Activity(
            user_id=current_user.id,
            action='barcode_generated',
            details=f'Product: {name}, GTIN: {gtin}'
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Barcode generated successfully',
            'barcode_url': barcode_url,
            'gtin': gtin
        }), 201
        
    except Exception as e:
        logger.error(f"Barcode generation error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to generate barcode'}), 500


def generate_gtin(user_id):
    """Generate unique 14-digit GTIN."""
    # Simple GTIN generation: prefix (2) + user_id (4) + timestamp (6) + check digit (2)
    timestamp = int(time.time()) % 1000000
    gtin_base = f"2{user_id:04d}{timestamp:06d}"
    
    # Calculate check digit (simplified)
    check_digit = calculate_check_digit(gtin_base)
    return f"{gtin_base}{check_digit}"


def calculate_check_digit(gtin_base):
    """Calculate GTIN-14 check digit."""
    total = 0
    for i, digit in enumerate(gtin_base):
        if i % 2 == 0:
            total += int(digit) * 3
        else:
            total += int(digit)
    
    check_digit = (10 - (total % 10)) % 10
    return check_digit


@barcode_bp.route('/history')
@login_required
def history():
    """Get barcode generation history."""
    if not current_user.can_access():
        return jsonify({'success': False, 'error': 'Subscription required'}), 403
    
    try:
        products = Product.query.filter_by(user_id=current_user.id).order_by(Product.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'products': [{
                'id': p.id,
                'name': p.name,
                'batch_number': p.batch_number,
                'expiry_date': p.expiry_date.isoformat() if p.expiry_date else None,
                'gtin': p.gtin,
                'barcode_url': p.barcode_url,
                'created_at': p.created_at.isoformat()
            } for p in products]
        }), 200
        
    except Exception as e:
        logger.error(f"History fetch error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch history'}), 500


@barcode_bp.route('/stats')
@login_required
def stats():
    """Get barcode usage statistics."""
    try:
        from sqlalchemy import extract
        
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        monthly_count = Product.query.filter(
            Product.user_id == current_user.id,
            extract('month', Product.created_at) == current_month,
            extract('year', Product.created_at) == current_year
        ).count()
        
        total_count = Product.query.filter_by(user_id=current_user.id).count()
        
        return jsonify({
            'success': True,
            'monthly_count': monthly_count,
            'total_count': total_count,
            'limit': 10 if not current_user.is_paid() else None
        }), 200
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to load stats'}), 500