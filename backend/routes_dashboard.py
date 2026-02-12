"""
Supplier Dashboard Routes for SupplierComply
Handles dashboard views, product management, and audit reports
"""

import io
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from sqlalchemy import extract, func
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from app import db, Product, Activity

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


def get_expiry_status(expiry_date):
    """
    Get expiry status color code.
    
    Args:
        expiry_date: Date object
    
    Returns:
        Tuple (status, color_class)
    """
    if not expiry_date:
        return 'unknown', 'gray'
    
    today = datetime.now().date()
    days_until_expiry = (expiry_date - today).days
    
    if days_until_expiry < 0:
        return 'expired', 'red'
    elif days_until_expiry <= 30:
        return 'critical', 'red'
    elif days_until_expiry <= 60:
        return 'warning', 'yellow'
    elif days_until_expiry <= 90:
        return 'attention', 'green'
    else:
        return 'good', 'green'


def create_audit_report_pdf(user, products, start_date, end_date):
    """
    Create PDF audit report for barcode generation history.
    
    Args:
        user: User object
        products: List of Product objects
        start_date: Report start date
        end_date: Report end date
    
    Returns:
        BytesIO buffer with PDF
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=20,
        alignment=1  # Center
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        alignment=1
    )
    
    # Title
    elements.append(Paragraph("SupplierComply - Barcode Audit Report", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Company info
    company_info = [
        ["Company:", user.company_name or "Not provided"],
        ["Email:", user.email],
        ["Phone:", user.phone or "Not provided"],
        ["Report Period:", f"{start_date} to {end_date}"],
        ["Payment Code:", user.payment_code],
        ["Status:", "Paid" if user.is_paid() else "Free Trial"]
    ]
    
    company_table = Table(company_info, colWidths=[2*inch, 4*inch])
    company_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary statistics
    total_products = len(products)
    products_with_expiry = [p for p in products if p.expiry_date]
    expiring_soon = [p for p in products_with_expiry if (p.expiry_date - datetime.now().date()).days <= 30]
    
    summary_data = [
        ["Summary Statistics", ""],
        ["Total Barcodes Generated:", str(total_products)],
        ["Products with Expiry Dates:", str(len(products_with_expiry))],
        ["Products Expiring in 30 Days:", str(len(expiring_soon))]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3f4f6')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Products table
    if products:
        elements.append(Paragraph("Generated Barcodes", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        table_data = [[
            "No.", "Product Name", "GTIN", "Batch", "Expiry Date", "Qty", "Generated"
        ]]
        
        for i, product in enumerate(products, 1):
            table_data.append([
                str(i),
                product.name[:30] + "..." if len(product.name) > 30 else product.name,
                product.gtin or "N/A",
                product.batch_number or "N/A",
                product.expiry_date.strftime('%Y-%m-%d') if product.expiry_date else "N/A",
                str(product.quantity) if product.quantity else "N/A",
                product.created_at.strftime('%Y-%m-%d')
            ])
        
        products_table = Table(table_data, colWidths=[0.4*inch, 1.8*inch, 1.2*inch, 0.8*inch, 0.9*inch, 0.5*inch, 0.9*inch])
        products_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
        ]))
        elements.append(products_table)
    else:
        elements.append(Paragraph("No barcodes generated in this period.", styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("This report was generated by SupplierComply - GS1 Barcode Compliance Platform", subtitle_style))
    elements.append(Paragraph("For support, contact: support@suppliercomply.co.ke", subtitle_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


@dashboard_bp.route('/')
@login_required
def index():
    """Render main dashboard."""
    return render_template('dashboard.html')


@dashboard_bp.route('/api/stats')
@login_required
def get_stats():
    """Get dashboard statistics."""
    try:
        # Basic stats
        total_products = Product.query.filter_by(user_id=current_user.id).count()
        this_month = current_user.get_barcode_count_this_month()
        
        # Payment status
        payment_status = {
            'status': current_user.payment_status,
            'is_paid': current_user.is_paid(),
            'is_trial_active': current_user.is_trial_active(),
            'trial_ends_at': current_user.trial_ends_at.isoformat() if current_user.trial_ends_at else None,
            'paid_until': current_user.paid_until.isoformat() if current_user.paid_until else None,
            'days_remaining': None
        }
        
        if current_user.is_paid() and current_user.paid_until:
            days = (current_user.paid_until - datetime.utcnow()).days
            payment_status['days_remaining'] = max(0, days)
        elif current_user.is_trial_active() and current_user.trial_ends_at:
            days = (current_user.trial_ends_at - datetime.utcnow()).days
            payment_status['days_remaining'] = max(0, days)
        
        # Expiry alerts (paid only)
        expiry_alerts = None
        if current_user.is_paid():
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
            
            expired = Product.query.filter(
                Product.user_id == current_user.id,
                Product.expiry_date < today
            ).count()
            
            expiry_alerts = {
                'expired': expired,
                '30_days': expiring_30,
                '60_days': expiring_60,
                '90_days': expiring_90
            }
        
        return jsonify({
            'success': True,
            'stats': {
                'total_barcodes': total_products,
                'this_month': this_month,
                'free_tier_limit': 10 if not current_user.is_paid() else None
            },
            'payment_status': payment_status,
            'expiry_alerts': expiry_alerts
        }), 200
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch stats'}), 500


@dashboard_bp.route('/api/products')
@login_required
def get_products():
    """Get paginated product list."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        expiry_filter = request.args.get('expiry_filter', '').strip()
        
        query = Product.query.filter_by(user_id=current_user.id)
        
        # Search filter
        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        
        # Expiry filter (paid only)
        if expiry_filter and current_user.is_paid():
            today = datetime.now().date()
            if expiry_filter == 'expired':
                query = query.filter(Product.expiry_date < today)
            elif expiry_filter == '30_days':
                query = query.filter(
                    Product.expiry_date <= today + timedelta(days=30),
                    Product.expiry_date >= today
                )
            elif expiry_filter == '60_days':
                query = query.filter(
                    Product.expiry_date <= today + timedelta(days=60),
                    Product.expiry_date > today + timedelta(days=30)
                )
            elif expiry_filter == '90_days':
                query = query.filter(
                    Product.expiry_date <= today + timedelta(days=90),
                    Product.expiry_date > today + timedelta(days=60)
                )
        
        products = query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        product_list = []
        for p in products.items:
            status, color = get_expiry_status(p.expiry_date)
            product_list.append({
                'id': p.id,
                'name': p.name,
                'batch_number': p.batch_number,
                'expiry_date': p.expiry_date.isoformat() if p.expiry_date else None,
                'quantity': p.quantity,
                'gtin': p.gtin,
                'barcode_url': p.barcode_url,
                'created_at': p.created_at.isoformat(),
                'expiry_status': {
                    'status': status,
                    'color': color
                } if current_user.is_paid() else None
            })
        
        return jsonify({
            'success': True,
            'products': product_list,
            'total': products.total,
            'pages': products.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"Products fetch error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch products'}), 500


@dashboard_bp.route('/api/expiring')
@login_required
def get_expiring_products():
    """Get products expiring within specified days."""
    try:
        if not current_user.is_paid():
            return jsonify({
                'success': False,
                'error': 'Expiry alerts are a paid feature',
                'upgrade_required': True
            }), 403
        
        days = request.args.get('days', 30, type=int)
        today = datetime.now().date()
        expiry_threshold = today + timedelta(days=days)
        
        products = Product.query.filter(
            Product.user_id == current_user.id,
            Product.expiry_date <= expiry_threshold,
            Product.expiry_date >= today
        ).order_by(Product.expiry_date).all()
        
        return jsonify({
            'success': True,
            'products': [{
                'id': p.id,
                'name': p.name,
                'batch_number': p.batch_number,
                'expiry_date': p.expiry_date.isoformat(),
                'days_remaining': (p.expiry_date - today).days,
                'gtin': p.gtin,
                'barcode_url': p.barcode_url
            } for p in products]
        }), 200
        
    except Exception as e:
        logger.error(f"Expiring products error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch expiring products'}), 500


@dashboard_bp.route('/api/audit-report', methods=['POST'])
@login_required
def generate_audit_report():
    """Generate PDF audit report."""
    try:
        if not current_user.is_paid():
            return jsonify({
                'success': False,
                'error': 'Audit reports are a paid feature',
                'upgrade_required': True
            }), 403
        
        data = request.get_json()
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        
        # Default to last 30 days if not specified
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = (datetime.now() - timedelta(days=30)).date()
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = datetime.now().date()
        
        # Get products in date range
        products = Product.query.filter(
            Product.user_id == current_user.id,
            func.date(Product.created_at) >= start_date,
            func.date(Product.created_at) <= end_date
        ).order_by(Product.created_at.desc()).all()
        
        # Generate PDF
        pdf_buffer = create_audit_report_pdf(
            current_user, products, 
            start_date.strftime('%Y-%m-%d'), 
            end_date.strftime('%Y-%m-%d')
        )
        
        # Log activity
        activity = Activity(
            user_id=current_user.id,
            action='audit_report_generated',
            details=f'Period: {start_date} to {end_date}, Products: {len(products)}'
        )
        db.session.add(activity)
        db.session.commit()
        
        filename = f"Audit_Report_{current_user.company_name or 'Supplier'}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Audit report error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to generate audit report'}), 500


@dashboard_bp.route('/api/activities')
@login_required
def get_activities():
    """Get user activity log."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        activities = Activity.query.filter_by(user_id=current_user.id).order_by(
            Activity.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'activities': [{
                'id': a.id,
                'action': a.action,
                'details': a.details,
                'created_at': a.created_at.isoformat()
            } for a in activities.items],
            'total': activities.total,
            'pages': activities.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"Activities fetch error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch activities'}), 500
