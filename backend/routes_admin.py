"""
Admin Dashboard Routes for SupplierComply
Handles admin views for user management and system monitoring
"""

import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db, User, Product, Payment, Activity

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to check if user is admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:  # Simple admin check - first user is admin
            return jsonify({'success': False, 'error': 'Unauthorized - Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Render admin dashboard."""
    return render_template('admin.html')


@admin_bp.route('/api/dashboard')
@login_required
@admin_required
def get_dashboard_stats():
    """Get admin dashboard statistics."""
    try:
        # User statistics
        total_users = User.query.count()
        paid_users = User.query.filter_by(payment_status='paid').count()
        trial_users = User.query.filter_by(payment_status='free_trial').count()
        pending_users = User.query.filter_by(payment_status='pending').count()
        
        # Today's new users
        today = datetime.utcnow().date()
        new_users_today = User.query.filter(
            func.date(User.created_at) == today
        ).count()
        
        # Barcode statistics
        total_barcodes = Product.query.count()
        barcodes_this_month = Product.query.filter(
            extract('month', Product.created_at) == datetime.utcnow().month,
            extract('year', Product.created_at) == datetime.utcnow().year
        ).count()
        
        # Payment statistics
        total_revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.status == 'confirmed'
        ).scalar() or 0
        
        pending_revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.status == 'pending'
        ).scalar() or 0
        
        # Recent activity
        recent_activities = Activity.query.order_by(
            Activity.created_at.desc()
        ).limit(10).all()
        
        # Expiring trials (next 3 days)
        expiring_trials = User.query.filter(
            User.payment_status == 'free_trial',
            User.trial_ends_at <= datetime.utcnow() + timedelta(days=3),
            User.trial_ends_at > datetime.utcnow()
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'users': {
                    'total': total_users,
                    'paid': paid_users,
                    'trial': trial_users,
                    'pending': pending_users,
                    'new_today': new_users_today,
                    'expiring_trials': expiring_trials
                },
                'barcodes': {
                    'total': total_barcodes,
                    'this_month': barcodes_this_month
                },
                'revenue': {
                    'total_confirmed': total_revenue,
                    'pending': pending_revenue
                }
            },
            'recent_activity': [{
                'id': a.id,
                'user_email': a.user.email if a.user else 'Unknown',
                'action': a.action,
                'details': a.details,
                'created_at': a.created_at.isoformat()
            } for a in recent_activities]
        }), 200
        
    except Exception as e:
        logger.error(f"Admin dashboard stats error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch dashboard stats'}), 500


@admin_bp.route('/api/users')
@login_required
@admin_required
def get_users():
    """Get all users with pagination and filtering."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        
        query = User.query
        
        # Search filter
        if search:
            query = query.filter(
                db.or_(
                    User.email.ilike(f'%{search}%'),
                    User.company_name.ilike(f'%{search}%'),
                    User.payment_code.ilike(f'%{search}%')
                )
            )
        
        # Status filter
        if status_filter:
            query = query.filter_by(payment_status=status_filter)
        
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'users': [{
                'id': u.id,
                'email': u.email,
                'company_name': u.company_name,
                'phone': u.phone,
                'payment_code': u.payment_code,
                'payment_status': u.payment_status,
                'trial_ends_at': u.trial_ends_at.isoformat() if u.trial_ends_at else None,
                'paid_until': u.paid_until.isoformat() if u.paid_until else None,
                'created_at': u.created_at.isoformat(),
                'barcode_count': len(u.products)
            } for u in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch users'}), 500


@admin_bp.route('/api/users/<int:user_id>')
@login_required
@admin_required
def get_user_detail(user_id):
    """Get detailed information about a specific user."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get user's products
        products = Product.query.filter_by(user_id=user_id).order_by(
            Product.created_at.desc()
        ).limit(10).all()
        
        # Get user's payments
        payments = Payment.query.filter_by(user_id=user_id).order_by(
            Payment.created_at.desc()
        ).all()
        
        # Get user's activities
        activities = Activity.query.filter_by(user_id=user_id).order_by(
            Activity.created_at.desc()
        ).limit(20).all()
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'company_name': user.company_name,
                'phone': user.phone,
                'payment_code': user.payment_code,
                'payment_status': user.payment_status,
                'trial_ends_at': user.trial_ends_at.isoformat() if user.trial_ends_at else None,
                'paid_until': user.paid_until.isoformat() if user.paid_until else None,
                'created_at': user.created_at.isoformat(),
                'is_paid': user.is_paid(),
                'is_trial_active': user.is_trial_active()
            },
            'products': [{
                'id': p.id,
                'name': p.name,
                'gtin': p.gtin,
                'batch_number': p.batch_number,
                'expiry_date': p.expiry_date.isoformat() if p.expiry_date else None,
                'created_at': p.created_at.isoformat()
            } for p in products],
            'payments': [{
                'id': p.id,
                'amount': p.amount,
                'payment_code': p.payment_code,
                'status': p.status,
                'created_at': p.created_at.isoformat(),
                'confirmed_at': p.confirmed_at.isoformat() if p.confirmed_at else None
            } for p in payments],
            'activities': [{
                'id': a.id,
                'action': a.action,
                'details': a.details,
                'created_at': a.created_at.isoformat()
            } for a in activities]
        }), 200
        
    except Exception as e:
        logger.error(f"Get user detail error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch user details'}), 500


@admin_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Update user information."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'company_name' in data:
            user.company_name = data['company_name'].strip()
        if 'phone' in data:
            user.phone = data['phone'].strip()
        if 'payment_status' in data:
            user.payment_status = data['payment_status']
        if 'trial_ends_at' in data:
            user.trial_ends_at = datetime.fromisoformat(data['trial_ends_at'])
        if 'paid_until' in data:
            user.paid_until = datetime.fromisoformat(data['paid_until'])
        
        db.session.commit()
        
        # Log activity
        activity = Activity(
            user_id=user_id,
            action='user_updated_by_admin',
            details=f'Updated by admin {current_user.id}'
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to update user'}), 500


@admin_bp.route('/api/activities')
@login_required
@admin_required
def get_all_activities():
    """Get all system activities."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        action_filter = request.args.get('action', '').strip()
        
        query = Activity.query
        
        if action_filter:
            query = query.filter(Activity.action.ilike(f'%{action_filter}%'))
        
        activities = query.order_by(Activity.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'activities': [{
                'id': a.id,
                'user_id': a.user_id,
                'user_email': a.user.email if a.user else 'Unknown',
                'action': a.action,
                'details': a.details,
                'created_at': a.created_at.isoformat()
            } for a in activities.items],
            'total': activities.total,
            'pages': activities.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"Get activities error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch activities'}), 500


@admin_bp.route('/api/search-payment-code')
@login_required
@admin_required
def search_payment_code():
    """Search for payment code in Equity statement."""
    try:
        code = request.args.get('code', '').strip().upper()
        
        if not code:
            return jsonify({'success': False, 'error': 'Payment code is required'}), 400
        
        # Find user by payment code
        user = User.query.filter_by(payment_code=code).first()
        
        if not user:
            return jsonify({
                'success': False,
                'error': f'No user found with payment code {code}'
            }), 404
        
        # Get pending payment for this user
        pending_payment = Payment.query.filter_by(
            user_id=user.id,
            status='pending'
        ).first()
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'company_name': user.company_name,
                'payment_code': user.payment_code,
                'payment_status': user.payment_status
            },
            'pending_payment': {
                'id': pending_payment.id,
                'amount': pending_payment.amount,
                'created_at': pending_payment.created_at.isoformat()
            } if pending_payment else None
        }), 200
        
    except Exception as e:
        logger.error(f"Search payment code error: {str(e)}")
        return jsonify({'success': False, 'error': 'Search failed'}), 500
