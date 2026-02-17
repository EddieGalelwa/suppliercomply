"""
Database Models for SupplierComply
"""

from datetime import datetime, timedelta
from extensions import db


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
    mpesa_confirmation_code = db.Column(db.String(20), nullable=True)  # ADDED THIS LINE
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