"""
Database models for 3D Printing E-commerce Platform
Using Supabase PostgreSQL
"""
from datetime import datetime
import json

class User:
    """User model"""
    TABLE_NAME = 'users'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(20),
            password_hash VARCHAR(500),
            full_name VARCHAR(255),
            otp_verified BOOLEAN DEFAULT FALSE,
            email_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            last_login TIMESTAMP
        );
        """


class Category:
    """Product Category model"""
    TABLE_NAME = 'categories'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS categories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) UNIQUE NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            image_url VARCHAR(500),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """


class Product:
    """Product model"""
    TABLE_NAME = 'products'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS products (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            category_id UUID NOT NULL REFERENCES categories(id),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            discount_price DECIMAL(10, 2),
            stock_quantity INTEGER DEFAULT 0,
            images JSONB,
            specifications JSONB,
            rating DECIMAL(3, 2) DEFAULT 0,
            total_reviews INTEGER DEFAULT 0,
            expected_delivery_date DATE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """


class Cart:
    """Shopping Cart model"""
    TABLE_NAME = 'carts'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS carts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id),
            product_id UUID NOT NULL REFERENCES products(id),
            quantity INTEGER DEFAULT 1,
            added_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, product_id)
        );
        """


class Order:
    """Order model"""
    TABLE_NAME = 'orders'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id),
            order_number VARCHAR(50) UNIQUE NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            discount_amount DECIMAL(10, 2) DEFAULT 0,
            payment_method VARCHAR(50) NOT NULL,
            payment_status VARCHAR(50) DEFAULT 'pending',
            order_status VARCHAR(50) DEFAULT 'pending',
            shipping_address JSONB NOT NULL,
            billing_address JSONB,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """


class OrderItem:
    """Order Items model"""
    TABLE_NAME = 'order_items'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS order_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL REFERENCES orders(id),
            product_id UUID NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            total_price DECIMAL(10, 2) NOT NULL
        );
        """


class Payment:
    """Payment model"""
    TABLE_NAME = 'payments'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS payments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL REFERENCES orders(id),
            transaction_id VARCHAR(100),
            amount DECIMAL(10, 2) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            payment_status VARCHAR(50) DEFAULT 'pending',
            payment_date TIMESTAMP DEFAULT NOW(),
            razorpay_payment_id VARCHAR(100),
            razorpay_order_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """


class Review:
    """Product Review model"""
    TABLE_NAME = 'reviews'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS reviews (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            product_id UUID NOT NULL REFERENCES products(id),
            user_id UUID NOT NULL REFERENCES users(id),
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            images JSONB,
            helpful_count INTEGER DEFAULT 0,
            is_verified_purchase BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(product_id, user_id)
        );
        """


class Support:
    """Customer Support Tickets model"""
    TABLE_NAME = 'support_tickets'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS support_tickets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id),
            ticket_number VARCHAR(50) UNIQUE NOT NULL,
            subject VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            status VARCHAR(50) DEFAULT 'open',
            priority VARCHAR(50) DEFAULT 'normal',
            category VARCHAR(100),
            contact_method VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """


class SupportMessage:
    """Support Ticket Messages model"""
    TABLE_NAME = 'support_messages'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS support_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ticket_id UUID NOT NULL REFERENCES support_tickets(id),
            sender_id UUID NOT NULL REFERENCES users(id),
            message TEXT NOT NULL,
            attachments JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """


class OTP:
    """OTP storage model"""
    TABLE_NAME = 'otps'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS otps (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            phone VARCHAR(20) NOT NULL,
            email VARCHAR(255),
            otp_code VARCHAR(6) NOT NULL,
            is_verified BOOLEAN DEFAULT FALSE,
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '5 minutes'
        );
        """


class ContactInfo:
    """Contact Information model"""
    TABLE_NAME = 'contact_info'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS contact_info (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            whatsapp VARCHAR(20),
            address TEXT,
            city VARCHAR(100),
            state VARCHAR(100),
            country VARCHAR(100),
            postal_code VARCHAR(20),
            business_hours JSONB,
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """


class SiteSettings:
    """Site-wide settings and theme configuration"""
    TABLE_NAME = 'site_settings'

    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS site_settings (
            id TEXT PRIMARY KEY,
            shop_name TEXT,
            hero_title TEXT,
            hero_subtitle TEXT,
            primary_color TEXT,
            accent_color TEXT,
            footer_text TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """


class Coupon:
    """Discount Coupon model"""
    TABLE_NAME = 'coupons'
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS coupons (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code VARCHAR(50) UNIQUE NOT NULL,
            description TEXT,
            discount_type VARCHAR(20) NOT NULL,
            discount_value DECIMAL(10, 2) NOT NULL,
            min_amount DECIMAL(10, 2),
            max_discount DECIMAL(10, 2),
            usage_limit INTEGER,
            usage_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            expiry_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """


# All models to create tables
ALL_MODELS = [
    User, Category, Product, Cart, Order, OrderItem,
    Payment, Review, Support, SupportMessage, OTP, ContactInfo, SiteSettings, Coupon
]
