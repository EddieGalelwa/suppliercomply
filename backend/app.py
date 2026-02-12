"""
SupplierComply - GS1 Barcode Compliance Platform for Kenya Medical Suppliers
Main Flask Application Entry Point
"""

from dotenv import load_dotenv
load_dotenv()

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__, 
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/suppliercomply')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file upload
    
    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
    
    # Cloudinary configuration
    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET')
    )
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    CORS(app)
    
    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdnjs.cloudflare.com fonts.googleapis.com; font-src 'self' fonts.gstatic.com cdnjs.cloudflare.com; img-src 'self' data: res.cloudinary.com; connect-src 'self';"
        return response
    
    # Register blueprints
    from routes_auth import auth_bp
    from routes_barcode import barcode_bp
    from routes_kemsa import kemsa_bp
    from routes_dashboard import dashboard_bp
    from routes_payment import payment_bp
    from routes_admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(barcode_bp)
    app.register_blueprint(kemsa_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(admin_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error(f"Internal server error: {str(error)}")
        return render_template('500.html'), 500
    
    # Landing page
    @app.route('/')
    def index():
        """Render landing page."""
        return render_template('index.html')
    
    # Health check
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
    
    return app


# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()


# Database Models
class User(db.Model):
    """User model for medical suppliers."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    payment_code = db.Column(db.String(10), unique=True, nullable=False)
    payment_status = db.Column(db.String(20), default='free_trial')
    trial_ends_at = db.Column(db.DateTime)
    paid_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='user', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy=True)
    activities = db.relationship('Activity', backref='user', lazy=True)
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    def is_paid(self):
        """Check if user has active paid subscription."""
        if self.payment_status == 'paid' and self.paid_until:
            return self.paid_until > datetime.utcnow()
        return False
    
    def is_trial_active(self):
        """Check if user's trial is still active."""
        if self.payment_status == 'free_trial' and self.trial_ends_at:
            return self.trial_ends_at > datetime.utcnow()
        return False
    
    def can_access(self):
        """Check if user can access the platform."""
        return self.is_paid() or self.is_trial_active()
    
    def get_barcode_count_this_month(self):
        """Get number of barcodes generated this month."""
        from sqlalchemy import extract
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return Product.query.filter(
            Product.user_id == self.id,
            Product.created_at >= start_of_month
        ).count()
    
    def get_expiring_products(self, days):
        """Get products expiring within specified days."""
        if not self.is_paid():
            return []
        expiry_threshold = datetime.utcnow().date() + timedelta(days=days)
        return Product.query.filter(
            Product.user_id == self.id,
            Product.expiry_date <= expiry_threshold,
            Product.expiry_date >= datetime.utcnow().date()
        ).all()


class Product(db.Model):
    """Product model for barcode generation."""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    batch_number = db.Column(db.String(100))
    expiry_date = db.Column(db.Date)
    quantity = db.Column(db.Integer)
    gtin = db.Column(db.String(14))
    barcode_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Payment(db.Model):
    """Payment log model."""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    payment_code = db.Column(db.String(10), nullable=False)
    reference_used = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    confirmed_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)


class Activity(db.Model):
    """Activity log model."""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Create app instance
app = create_app()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
