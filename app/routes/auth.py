"""
Authentication Routes
"""
from flask import Blueprint, request, jsonify
from app.utils.auth import (
    OTPManager, AuthManager, JWTManager, PasswordManager, login_required
)
from app.models import get_user_by_email, DatabaseOperations
from datetime import datetime
from config import get_config
import json

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
config = get_config()

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user with password-only flow"""
    try:
        data = request.get_json()
        full_name = (data.get('full_name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        phone = (data.get('phone') or '').strip() or None

        if not full_name:
            return jsonify({'error': 'Name is required'}), 400

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        if '@' not in email or '.' not in email.split('@')[-1]:
            return jsonify({'error': 'Enter a valid email address'}), 400

        if not password or not confirm_password:
            return jsonify({'error': 'Password and confirm password are required'}), 400

        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        # Register user
        success, result = AuthManager.register_user(
            email=email,
            phone=phone,
            full_name=full_name,
            password=password
        )
        
        if not success:
            return jsonify(result), 400

        OTPManager.send_account_creation_email(email, full_name)

        # Immediately issue token for password-only signup flow.
        token = JWTManager.generate_token(result['id'], result['email'])

        return jsonify({
            'message': 'Account created successfully',
            'user': {
                'id': result.get('id'),
                'email': result.get('email'),
                'full_name': result.get('full_name'),
                'is_admin': result.get('is_admin', False),
                'phone': result.get('phone')
            },
            'token': token
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to email or phone"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Generate and store OTP
        otp = OTPManager.store_otp(email=email)
        
        if not otp:
            return jsonify({'error': 'Failed to generate OTP'}), 500
        
        # Send OTP via email
        email_sent = OTPManager.send_otp_email(email, otp)

        response = {
            'message': 'OTP sent successfully to email' if email_sent else 'Email OTP unavailable; use OTP from response in development',
            'email_sent': email_sent
        }

        if config.DEBUG:
            response['otp'] = otp
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and login"""
    try:
        data = request.get_json()
        email = data.get('email')
        otp_code = data.get('otp')
        
        if not otp_code:
            return jsonify({'error': 'OTP is required'}), 400
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Login with OTP
        success, result = AuthManager.login_with_otp(email, otp_code)
        
        if not success:
            return jsonify(result), 401
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': result['user']['id'],
                'email': result['user']['email'],
                'full_name': result['user'].get('full_name'),
                'is_admin': result['user'].get('is_admin', False),
                'phone': result['user'].get('phone')
            },
            'token': result['token']
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email and password"""
    try:
        data = request.get_json()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        success, result = AuthManager.login_with_email_password(email, password)
        
        if not success:
            return jsonify(result), 401
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': result['user']['id'],
                'email': result['user']['email'],
                'full_name': result['user'].get('full_name'),
                'is_admin': result['user'].get('is_admin', False),
                'phone': result['user'].get('phone')
            },
            'token': result['token']
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/set-password', methods=['POST'])
def set_password():
    """Set password for user (OTP verified)"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if not email or not password or not confirm_password:
            return jsonify({'error': 'Email, password, and confirm password are required'}), 400
        
        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Hash password
        password_hash = PasswordManager.hash_password(password)
        
        # Update user
        DatabaseOperations.update('users', {
            'password_hash': password_hash,
            'updated_at': datetime.now().isoformat()
        }, {'email': email})
        
        return jsonify({'message': 'Password set successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get user profile"""
    try:
        from flask import g
        user = g.user
        
        return jsonify({
            'user': {
                'id': user['id'],
                'email': user['email'],
                'full_name': user.get('full_name'),
                'is_admin': user.get('is_admin', False),
                'phone': user.get('phone'),
                'email_verified': user.get('email_verified'),
                'otp_verified': user.get('otp_verified'),
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login')
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        from flask import g
        
        data = request.get_json()
        user_id = g.user_id
        
        update_data = {
            'updated_at': datetime.now().isoformat()
        }
        
        # Update allowed fields
        allowed_fields = ['full_name', 'phone']
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        DatabaseOperations.update('users', update_data, {'id': user_id})
        
        return jsonify({'message': 'Profile updated successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    # In JWT-based auth, client should delete token locally
    return jsonify({'message': 'Logged out successfully'}), 200
