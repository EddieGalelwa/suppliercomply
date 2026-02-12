-- SupplierComply Database Schema
-- GS1 Barcode Compliance Platform for Kenya Medical Suppliers
-- PostgreSQL Database

-- Enable UUID extension (optional, for future use)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (suppliers)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    phone VARCHAR(20),
    payment_code VARCHAR(10) UNIQUE NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'free_trial', -- free_trial, pending, paid
    trial_ends_at TIMESTAMP,
    paid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on payment_code for faster lookups
CREATE INDEX idx_users_payment_code ON users(payment_code);
CREATE INDEX idx_users_payment_status ON users(payment_status);
CREATE INDEX idx_users_email ON users(email);

-- Products table (barcode generation history)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    batch_number VARCHAR(100),
    expiry_date DATE,
    quantity INTEGER,
    gtin VARCHAR(14),
    barcode_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for product queries
CREATE INDEX idx_products_user_id ON products(user_id);
CREATE INDEX idx_products_expiry_date ON products(expiry_date);
CREATE INDEX idx_products_created_at ON products(created_at);

-- Payments log table
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL, -- in KSh (15000)
    payment_code VARCHAR(10) NOT NULL,
    reference_used VARCHAR(50), -- What user entered in M-Pesa
    status VARCHAR(20) DEFAULT 'pending', -- pending, confirmed, failed
    confirmed_by INTEGER, -- admin user who confirmed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP
);

-- Create indexes for payment queries
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_payment_code ON payments(payment_code);
CREATE INDEX idx_payments_created_at ON payments(created_at);

-- Activity log table
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for activity queries
CREATE INDEX idx_activities_user_id ON activities(user_id);
CREATE INDEX idx_activities_created_at ON activities(created_at);
CREATE INDEX idx_activities_action ON activities(action);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert admin user (first user - will be ID 1)
-- Password should be changed immediately after first login
-- Default password: Admin123! (bcrypt hashed)
INSERT INTO users (
    email, 
    password_hash, 
    company_name, 
    phone, 
    payment_code, 
    payment_status,
    paid_until
) VALUES (
    'admin@suppliercomply.co.ke',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6G', -- Admin123!
    'SupplierComply Admin',
    '+254700000000',
    'SC000',
    'paid',
    '2099-12-31'::timestamp
);

-- Comments for documentation
COMMENT ON TABLE users IS 'Medical suppliers registered on the platform';
COMMENT ON TABLE products IS 'Products with generated GS1 barcodes';
COMMENT ON TABLE payments IS 'Payment transactions via Equity Paybill 247247';
COMMENT ON TABLE activities IS 'Audit log of user activities';

COMMENT ON COLUMN users.payment_code IS 'Unique code for M-Pesa payments (SC001, SC002, etc.)';
COMMENT ON COLUMN users.payment_status IS 'Current subscription status: free_trial, pending, paid';
COMMENT ON COLUMN products.gtin IS 'GS1 GTIN-14 barcode number';
COMMENT ON COLUMN products.barcode_url IS 'Cloudinary URL of generated barcode image';
COMMENT ON COLUMN payments.payment_code IS 'Payment code used for this transaction';
COMMENT ON COLUMN payments.reference_used IS 'Reference entered by user in M-Pesa';
