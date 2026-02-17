"""
Authentication Routes for SupplierComply
Handles user registration, login, logout, and password reset
"""

import re
import logging
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message

# Import from extensions and models (no circular import issue)
from extensions import db, mail
from models import User, Activity

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def generate_payment_code():
    """Generate unique sequential payment code (SC001, SC002, etc.)."""
    last_user = User.query.order_by(User.id.desc()).first()
    if last_user and last_user.payment_code:
        try:
            last_number = int(last_user.payment_code.replace('SC', ''))
            new_number = last_number + 1
        except ValueError:
            new_number = 1
    else:
        new_number = 1
    return f'SC{new_number:03d}'


def log_activity(user_id, action, details=None):
    """Log user activity."""
    try:
        activity = Activity(user_id=user_id, action=action, details=details)
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to log activity: {str(e)}")
        db.session.rollback()


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'GET':
        return render_template('auth.html', mode='register')
    
    try:
        data = request.get_json() or request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        company_name = data.get('company_name', '').strip()
        phone = data.get('phone', '').strip()
        
        # Validation
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        # Email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Password validation (min 8 characters)
        if len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        # Generate payment code
        payment_code = generate_payment_code()
        
        # Create user
        user = User(
            email=email,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
            company_name=company_name,
            phone=phone,
            payment_code=payment_code,
            payment_status='free_trial',
            trial_ends_at=datetime.utcnow() + timedelta(days=14)
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'user_registered', f'Company: {company_name}')
        
        # LOG USER IN IMMEDIATELY AFTER REGISTRATION
        login_user(user, remember=True)
        
        # Send welcome email
        try:
            msg = Message(
                'Welcome to SupplierComply - Your Payment Code',
                recipients=[email]
            )
            msg.body = f"""Welcome to SupplierComply!

Your account has been created successfully.

YOUR PAYMENT CODE: {payment_code}

IMPORTANT: Save this code! You will need it when making payments via M-Pesa.

Your 14-day free trial starts now. Upgrade anytime to unlock unlimited barcodes and premium features.

Get started: Login at suppliercomply.co.ke

Need help? Reply to this email or WhatsApp us.

Best regards,
The SupplierComply Team
"""
            mail.send(msg)
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
        
        logger.info(f"New user registered: {email} with payment code {payment_code}")
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'payment_code': payment_code,
            'redirect': url_for('dashboard.index')  # Redirect to dashboard, not login
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Registration failed. Please try again.'}), 500


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'GET':
        return render_template('auth.html', mode='login')
    
    try:
        data = request.get_json() or request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Check if account is locked (trial expired and not paid)
        if not user.can_access() and user.payment_status != 'pending':
            return jsonify({
                'success': False, 
                'error': 'Your account has expired. Please upgrade to continue.',
                'redirect': url_for('payment.upgrade')
            }), 403
        
        login_user(user, remember=remember)
        log_activity(user.id, 'user_login')
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect': url_for('dashboard.index')
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'success': False, 'error': 'Login failed. Please try again.'}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle user logout."""
    try:
        log_activity(current_user.id, 'user_logout')
        logout_user()
        return jsonify({'success': True, 'redirect': url_for('index')}), 200
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'success': False, 'error': 'Logout failed'}), 500


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Handle password reset request."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        # Always return success to prevent email enumeration
        if not user:
            return jsonify({'success': True, 'message': 'If the email exists, a reset link has been sent'}), 200
        
        # Generate reset token (simple implementation)
        reset_token = secrets.token_urlsafe(32)
        
        # Store token in session (in production, use Redis or database)
        session[f'reset_token_{user.id}'] = {
            'token': reset_token,
            'expires': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        # Send reset email
        reset_url = f"{request.host_url}auth/reset-password?token={reset_token}&user={user.id}"
        
        try:
            msg = Message(
                'Password Reset - SupplierComply',
                recipients=[email]
            )
            msg.body = f"""Hello,

You requested a password reset for your SupplierComply account.

Click the link below to reset your password:
{reset_url}

This link expires in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
The SupplierComply Team
"""
            mail.send(msg)
            logger.info(f"Password reset email sent to: {email}")
        except Exception as e:
            logger.error(f"Failed to send reset email: {str(e)}")
            return jsonify({'success': False, 'error': 'Failed to send reset email'}), 500
        
        return jsonify({'success': True, 'message': 'Password reset link sent to your email'}), 200
        
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return jsonify({'success': False, 'error': 'Request failed. Please try again.'}), 500


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Handle password reset."""
    if request.method == 'GET':
        token = request.args.get('token')
        user_id = request.args.get('user')
        return render_template('auth.html', mode='reset', token=token, user_id=user_id)
    
    try:
        data = request.get_json()
        token = data.get('token')
        user_id = data.get('user_id')
        new_password = data.get('new_password')
        
        if not token or not user_id or not new_password:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        
        # Verify token
        token_data = session.get(f'reset_token_{user_id}')
        if not token_data or token_data['token'] != token:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 400
        
        # Check expiration
        expires = datetime.fromisoformat(token_data['expires'])
        if expires < datetime.utcnow():
            return jsonify({'success': False, 'error': 'Token has expired'}), 400
        
        # Update password
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        
        # Clear token
        session.pop(f'reset_token_{user_id}', None)
        
        log_activity(user.id, 'password_reset')
        logger.info(f"Password reset successful for user: {user.email}")
        
        return jsonify({
            'success': True,
            'message': 'Password reset successful. Please login with your new password.',
            'redirect': url_for('auth.login')
        }), 200
        
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Reset failed. Please try again.'}), 500


@auth_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    """Get or update user profile."""
    if request.method == 'GET':
        return jsonify({
            'email': current_user.email,
            'company_name': current_user.company_name,
            'phone': current_user.phone,
            'payment_code': current_user.payment_code,
            'payment_status': current_user.payment_status,
            'trial_ends_at': current_user.trial_ends_at.isoformat() if current_user.trial_ends_at else None,
            'paid_until': current_user.paid_until.isoformat() if current_user.paid_until else None
        }), 200
    
    try:
        data = request.get_json()
        
        if 'company_name' in data:
            current_user.company_name = data['company_name'].strip()
        if 'phone' in data:
            current_user.phone = data['phone'].strip()
        
        db.session.commit()
        log_activity(current_user.id, 'profile_updated')
        
        return jsonify({'success': True, 'message': 'Profile updated'}), 200
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Update failed'}), 500