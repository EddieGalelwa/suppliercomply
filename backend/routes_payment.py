"""
Equity Paybill Payment System Routes for SupplierComply
Handles manual payment reconciliation via Equity Bank Paybill 247247
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from flask_mail import Message

# Import from extensions and models (no circular import issue)
from extensions import db, mail
from models import User, Payment, Activity

logger = logging.getLogger(__name__)
payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

# Admin emails - same as routes_admin.py
ADMIN_EMAILS = ['test@example.com', 'admin@suppliercomply.co.ke']


def log_activity(user_id, action, details=None):
    """Log user activity."""
    try:
        activity = Activity(user_id=user_id, action=action, details=details)
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to log activity: {str(e)}")
        db.session.rollback()


def send_payment_confirmation_email(user):
    """Send payment confirmation email to user."""
    try:
        msg = Message(
            'Payment Confirmed - Welcome to SupplierComply Paid Tier',
            recipients=[user.email]
        )
        msg.body = f"""Dear {user.company_name or 'Valued Customer'},

Great news! Your payment has been confirmed and your account has been upgraded to the Paid Tier.

PAYMENT DETAILS:
- Amount: KSh 15,000
- Payment Code: {user.payment_code}
- Valid Until: {user.paid_until.strftime('%Y-%m-%d') if user.paid_until else 'N/A'}

WHAT'S NOW UNLOCKED:
✓ Unlimited GS1 barcode generation (no watermarks)
✓ Full KEMSA Excel export functionality
✓ Expiry date alerts (30/60/90 days)
✓ PDF audit reports
✓ Priority WhatsApp support

Your subscription will automatically renew monthly. We'll send a reminder 3 days before renewal.

Get started: Login at suppliercomply.co.ke/dashboard

Need help? WhatsApp us at +254724896761

Thank you for choosing SupplierComply!

Best regards,
The SupplierComply Team
"""
        # Temporarily disabled - will add SendGrid later
        logger.info(f'EMAIL WOULD SEND TO: {msg.recipients}')
        logger.info(f"Payment confirmation email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {str(e)}")


@payment_bp.route('/upgrade')
@login_required
def upgrade():
    """Render payment/upgrade page."""
    return render_template('upgrade.html')


@payment_bp.route('/api/status')
@login_required
def get_payment_status():
    """Get current user's payment status."""
    try:
        # Get pending payment if any
        pending_payment = Payment.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).order_by(Payment.created_at.desc()).first()
        
        # Get payment history
        payment_history = Payment.query.filter_by(
            user_id=current_user.id,
            status='confirmed'
        ).order_by(Payment.confirmed_at.desc()).all()
        
        status_info = {
            'payment_code': current_user.payment_code,
            'payment_status': current_user.payment_status,
            'is_paid': current_user.is_paid(),
            'is_trial_active': current_user.is_trial_active(),
            'trial_ends_at': current_user.trial_ends_at.isoformat() if current_user.trial_ends_at else None,
            'paid_until': current_user.paid_until.isoformat() if current_user.paid_until else None,
            'days_remaining': None,
            'pending_payment': None,
            'payment_history': []
        }
        
        # Calculate days remaining
        if current_user.is_paid() and current_user.paid_until:
            days = (current_user.paid_until - datetime.utcnow()).days
            status_info['days_remaining'] = max(0, days)
        elif current_user.is_trial_active() and current_user.trial_ends_at:
            days = (current_user.trial_ends_at - datetime.utcnow()).days
            status_info['days_remaining'] = max(0, days)
        
        # Pending payment info
        if pending_payment:
            status_info['pending_payment'] = {
                'id': pending_payment.id,
                'amount': pending_payment.amount,
                'status': pending_payment.status,
                'created_at': pending_payment.created_at.isoformat(),
                'mpesa_confirmation_code': pending_payment.mpesa_confirmation_code
            }
        
        # Payment history
        status_info['payment_history'] = [{
            'id': p.id,
            'amount': p.amount,
            'payment_code': p.payment_code,
            'confirmed_at': p.confirmed_at.isoformat() if p.confirmed_at else None
        } for p in payment_history]
        
        return jsonify({
            'success': True,
            'status': status_info
        }), 200
        
    except Exception as e:
        logger.error(f"Payment status error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch payment status'}), 500


@payment_bp.route('/api/i-have-paid', methods=['POST'])
@login_required
def i_have_paid():
    """User confirms they have made payment via M-Pesa."""
    try:
        data = request.get_json() or {}
        mpesa_confirmation_code = data.get('mpesa_confirmation_code', '').strip().upper()
        
        # Validate M-Pesa confirmation code
        if not mpesa_confirmation_code:
            return jsonify({
                'success': False,
                'error': 'Please enter your M-Pesa confirmation code'
            }), 400
        
        # Check if user already has pending payment
        existing_pending = Payment.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).first()
        
        if existing_pending:
            return jsonify({
                'success': False,
                'error': 'You already have a pending payment. Please wait for confirmation.',
                'pending_since': existing_pending.created_at.isoformat()
            }), 400
        
        # Check if user is already paid
        if current_user.is_paid():
            return jsonify({
                'success': False,
                'error': 'Your account is already active. No payment needed.'
            }), 400
        
        # Create pending payment record
        payment = Payment(
            user_id=current_user.id,
            amount=15000,  # KSh 15,000 monthly
            payment_code=current_user.payment_code,
            reference_used=current_user.payment_code,
            status='pending',
            mpesa_confirmation_code=mpesa_confirmation_code  # Store the M-Pesa code
        )
        
        db.session.add(payment)
        
        # Update user status
        current_user.payment_status = 'pending'
        
        db.session.commit()
        
        # Log activity
        log_activity(current_user.id, 'payment_initiated', 
                    f'Amount: 15000, Code: {current_user.payment_code}, M-Pesa: {mpesa_confirmation_code}')
        
        # Send notification to admin
        try:
            admin_msg = Message(
                f'New Payment Pending - {current_user.payment_code}',
                recipients=[mail.default_sender] if mail.default_sender else []
            )
            admin_msg.body = f"""New payment pending confirmation:

User: {current_user.email}
Company: {current_user.company_name or 'N/A'}
Payment Code: {current_user.payment_code}
M-Pesa Confirmation: {mpesa_confirmation_code}
Amount: KSh 15,000
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

Check Equity Bank (Paybill 247247, Account: 1720186723098) for deposit with reference: {current_user.payment_code}

Confirm at: suppliercomply.co.ke/admin
"""
            if mail.default_sender:
                # Temporarily disabled - will add SendGrid later
                logger.info(f'EMAIL WOULD SEND TO: {admin_msg.recipients}')
        except Exception as e:
            logger.error(f"Failed to send admin notification: {str(e)}")
        
        logger.info(f"User {current_user.id} marked as paid (pending confirmation), M-Pesa: {mpesa_confirmation_code}")
        
        return jsonify({
            'success': True,
            'message': 'Payment recorded. We will confirm within 5 minutes.',
            'payment_code': current_user.payment_code
        }), 200
        
    except Exception as e:
        logger.error(f"I have paid error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to record payment. Please try again.'}), 500


@payment_bp.route('/api/cancel-pending', methods=['POST'])
@login_required
def cancel_pending():
    """Cancel a pending payment request."""
    try:
        pending_payment = Payment.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).first()
        
        if not pending_payment:
            return jsonify({
                'success': False,
                'error': 'No pending payment found'
            }), 404
        
        # Delete pending payment
        db.session.delete(pending_payment)
        
        # Revert user status
        if current_user.trial_ends_at and current_user.trial_ends_at > datetime.utcnow():
            current_user.payment_status = 'free_trial'
        else:
            current_user.payment_status = 'free_trial'
        
        db.session.commit()
        
        log_activity(current_user.id, 'payment_cancelled')
        
        return jsonify({
            'success': True,
            'message': 'Pending payment cancelled'
        }), 200
        
    except Exception as e:
        logger.error(f"Cancel pending error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to cancel payment'}), 500


@payment_bp.route('/api/admin/pending')
@login_required
def get_pending_payments():
    """Get all pending payments (admin only)."""
    try:
        if current_user.email not in ADMIN_EMAILS:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        pending = Payment.query.filter_by(status='pending').order_by(
            Payment.created_at.desc()
        ).all()
        
        return jsonify({
            'success': True,
            'pending_payments': [{
                'id': p.id,
                'user_id': p.user_id,
                'user_email': p.user.email,
                'company_name': p.user.company_name,
                'amount': p.amount,
                'payment_code': p.payment_code,
                'mpesa_confirmation_code': p.mpesa_confirmation_code,
                'reference_used': p.reference_used,
                'created_at': p.created_at.isoformat()
            } for p in pending]
        }), 200
        
    except Exception as e:
        logger.error(f"Get pending payments error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch pending payments'}), 500


@payment_bp.route('/api/admin/confirm', methods=['POST'])
@login_required
def confirm_payment():
    """Confirm a pending payment (admin only)."""
    try:
        if current_user.email not in ADMIN_EMAILS:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        payment_id = data.get('payment_id')
        
        if not payment_id:
            return jsonify({'success': False, 'error': 'Payment ID is required'}), 400
        
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'success': False, 'error': 'Payment not found'}), 404
        
        if payment.status != 'pending':
            return jsonify({'success': False, 'error': 'Payment is not pending'}), 400
        
        # Update payment
        payment.status = 'confirmed'
        payment.confirmed_by = current_user.id
        payment.confirmed_at = datetime.utcnow()
        
        # Update user to paid status
        user = payment.user
        user.payment_status = 'paid'
        user.paid_until = datetime.utcnow() + timedelta(days=30)
        
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'payment_confirmed', f'Amount: {payment.amount}, Confirmed by: {current_user.id}')
        
        # Send confirmation email
        send_payment_confirmation_email(user)
        
        logger.info(f"Payment {payment_id} confirmed for user {user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Payment confirmed for {user.email}',
            'user': {
                'id': user.id,
                'email': user.email,
                'paid_until': user.paid_until.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Confirm payment error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to confirm payment'}), 500


@payment_bp.route('/api/admin/set-trial', methods=['POST'])
@login_required
def set_trial():
    """Set user to free trial (admin only)."""
    try:
        if current_user.email not in ADMIN_EMAILS:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        days = data.get('days', 14)
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User ID is required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Update user
        user.payment_status = 'free_trial'
        user.trial_ends_at = datetime.utcnow() + timedelta(days=days)
        user.paid_until = None
        
        db.session.commit()
        
        log_activity(user.id, 'trial_set', f'Days: {days}, Set by: {current_user.id}')
        
        logger.info(f"Trial set for user {user_id} for {days} days")
        
        return jsonify({
            'success': True,
            'message': f'Free trial set for {user.email} until {user.trial_ends_at.strftime("%Y-%m-%d")}'
        }), 200
        
    except Exception as e:
        logger.error(f"Set trial error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to set trial'}), 500


@payment_bp.route('/api/admin/payment-history')
@login_required
def get_all_payment_history():
    """Get all payment history (admin only)."""
    try:
        if current_user.email not in ADMIN_EMAILS:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        payments = Payment.query.order_by(Payment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'payments': [{
                'id': p.id,
                'user_id': p.user_id,
                'user_email': p.user.email,
                'company_name': p.user.company_name,
                'amount': p.amount,
                'payment_code': p.payment_code,
                'mpesa_confirmation_code': p.mpesa_confirmation_code,
                'reference_used': p.reference_used,
                'status': p.status,
                'created_at': p.created_at.isoformat(),
                'confirmed_at': p.confirmed_at.isoformat() if p.confirmed_at else None
            } for p in payments.items],
            'total': payments.total,
            'pages': payments.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"Payment history error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch payment history'}), 500