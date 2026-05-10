"""
Authentication utilities for OTP and Email login
"""
import random
import string
from datetime import datetime, timedelta
import hashlib
import hmac
from functools import wraps
from flask import request, jsonify, session, g
from config import get_config
from app.models import DatabaseOperations, get_user_by_email, get_user_by_id

try:
    import jwt
except ImportError:
    from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

    class _JWTFallback:
        ExpiredSignatureError = SignatureExpired
        InvalidTokenError = BadSignature

        @staticmethod
        def encode(payload, secret, algorithm=None):
            serializer = URLSafeTimedSerializer(secret, salt='mantra-made-3d-arts-jwt')
            return serializer.dumps(payload)

        @staticmethod
        def decode(token, secret, algorithms=None):
            serializer = URLSafeTimedSerializer(secret, salt='mantra-made-3d-arts-jwt')
            return serializer.loads(token, max_age=config.JWT_EXPIRATION_HOURS * 3600)

    jwt = _JWTFallback()

config = get_config()

class OTPManager:
    """Manage OTP generation and verification"""
    _mail_warning_logged = False
    _otp_fallback_warning_logged = False
    _in_memory_otps = {}
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate random OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def send_otp_email(email: str, otp: str) -> bool:
        """Send OTP via Email"""
        required_settings = [config.MAIL_SERVER, config.MAIL_USERNAME, config.MAIL_PASSWORD]
        placeholder_passwords = {'your_email_password', 'your_app_password', 'changeme', 'password'}
        mail_password = (config.MAIL_PASSWORD or '').strip()

        if (not all(required_settings)) or (mail_password.lower() in placeholder_passwords):
            if not OTPManager._mail_warning_logged:
                print('! OTP email disabled: configure valid MAIL_SERVER/MAIL_USERNAME/MAIL_PASSWORD in .env')
                OTPManager._mail_warning_logged = True
            return False

    @staticmethod
    def send_account_creation_email(email: str, full_name: str = None) -> bool:
        """Send account creation confirmation email"""
        required_settings = [config.MAIL_SERVER, config.MAIL_USERNAME, config.MAIL_PASSWORD]
        placeholder_passwords = {'your_email_password', 'your_app_password', 'changeme', 'password'}
        mail_password = (config.MAIL_PASSWORD or '').strip()

        if (not all(required_settings)) or (mail_password.lower() in placeholder_passwords):
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            name = full_name or 'Customer'

            msg = MIMEMultipart()
            msg['From'] = config.MAIL_USERNAME
            msg['To'] = email
            msg['Subject'] = 'Welcome to Mantra Made 3D Arts'

            body = f"""
            <html>
                <body>
                    <h2>Account Created Successfully</h2>
                    <p>Dear {name},</p>
                    <p>Your account has been created successfully.</p>
                    <p>You can now sign in with your email and password, or use OTP sign in from the login page.</p>
                    <p>Regards,<br>Mantra Made 3D Arts</p>
                </body>
            </html>
            """

            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(config.MAIL_SERVER, config.MAIL_PORT)
            if config.MAIL_USE_TLS:
                server.starttls()
            server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        except Exception:
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = config.MAIL_USERNAME
            msg['To'] = email
            msg['Subject'] = '3D Printing Store - Your OTP'
            
            body = f"""
            <html>
                <body>
                    <h2>Your OTP Code</h2>
                    <p>Your One-Time Password is: <strong>{otp}</strong></p>
                    <p>This code is valid for 5 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(config.MAIL_SERVER, config.MAIL_PORT)
            if config.MAIL_USE_TLS:
                server.starttls()
            server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True
        except smtplib.SMTPAuthenticationError:
            if not OTPManager._mail_warning_logged:
                print('! OTP email login failed: use a Gmail App Password in MAIL_PASSWORD')
                OTPManager._mail_warning_logged = True
            return False
        except Exception as e:
            if not OTPManager._mail_warning_logged:
                print(f"! OTP email unavailable: {str(e)}")
                OTPManager._mail_warning_logged = True
            return False
    
    @staticmethod
    def store_otp(email: str) -> str:
        """Store OTP in database"""
        otp = OTPManager.generate_otp()
        
        try:
            result = DatabaseOperations.insert('otps', {
                'email': email,
                'phone': None,
                'otp_code': otp,
                'is_verified': False,
                'attempts': 0,
                'expires_at': (datetime.now() + timedelta(minutes=5)).isoformat()
            })

            if not result:
                if config.DEBUG:
                    if not OTPManager._otp_fallback_warning_logged:
                        print('! OTP DB write blocked; using in-memory OTP fallback for development')
                        OTPManager._otp_fallback_warning_logged = True
                    OTPManager._in_memory_otps[email] = {
                        'otp_code': otp,
                        'attempts': 0,
                        'is_verified': False,
                        'expires_at': datetime.now() + timedelta(minutes=5)
                    }
                    return otp
                print('! OTP storage failed: database write returned no rows')
                return None
            return otp
        except Exception as e:
            if config.DEBUG:
                if not OTPManager._otp_fallback_warning_logged:
                    print('! OTP DB unavailable; using in-memory OTP fallback for development')
                    OTPManager._otp_fallback_warning_logged = True
                OTPManager._in_memory_otps[email] = {
                    'otp_code': otp,
                    'attempts': 0,
                    'is_verified': False,
                    'expires_at': datetime.now() + timedelta(minutes=5)
                }
                return otp
            print(f"Error storing OTP: {str(e)}")
            return None
    
    @staticmethod
    def verify_otp(email: str, otp_code: str) -> tuple[bool, str]:
        """Verify OTP"""
        try:
            otp_records = DatabaseOperations.select(
                'otps',
                filters={'email': email}
            )
            
            if not otp_records:
                fallback_record = OTPManager._in_memory_otps.get(email)
                if not fallback_record:
                    return False, "OTP not found"

                if fallback_record['expires_at'] < datetime.now():
                    OTPManager._in_memory_otps.pop(email, None)
                    return False, "OTP expired"

                if fallback_record['attempts'] >= 3:
                    return False, "Too many attempts"

                if fallback_record['otp_code'] == otp_code:
                    fallback_record['is_verified'] = True
                    fallback_record['attempts'] += 1
                    return True, "OTP verified successfully"

                fallback_record['attempts'] += 1
                return False, "Invalid OTP"
            
            otp_record = otp_records[-1]  # Get latest OTP
            
            # Check if expired
            if datetime.fromisoformat(otp_record['expires_at']) < datetime.now():
                return False, "OTP expired"
            
            # Check attempts
            if otp_record['attempts'] >= 3:
                return False, "Too many attempts"
            
            # Verify code
            if otp_record['otp_code'] == otp_code:
                DatabaseOperations.update('otps', {'is_verified': True, 'attempts': otp_record['attempts'] + 1}, {'id': otp_record['id']})
                return True, "OTP verified successfully"
            else:
                DatabaseOperations.update('otps', {'attempts': otp_record['attempts'] + 1}, {'id': otp_record['id']})
                return False, "Invalid OTP"
        
        except Exception as e:
            print(f"Error verifying OTP: {str(e)}")
            return False, str(e)


class PasswordManager:
    """Manage password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password"""
        return PasswordManager.hash_password(password) == password_hash


class JWTManager:
    """Manage JWT token generation and verification"""
    
    @staticmethod
    def generate_token(user_id: str, email: str) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'email': email,
            'iat': int(datetime.utcnow().timestamp()),
            'exp': int((datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)).timestamp())
        }
        return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


class AuthManager:
    """Manage user authentication"""
    
    @staticmethod
    def register_user(email: str, phone: str = None, full_name: str = None, password: str = None) -> tuple[bool, dict]:
        """Register new user"""
        try:
            # Check if user exists
            existing_user = get_user_by_email(email)
            if existing_user:
                return False, {'error': 'User already exists'}
            
            # Create new user
            user_data = {
                'email': email,
                'phone': phone,
                'is_admin': False,
                'full_name': full_name,
                'otp_verified': bool(password),
                'email_verified': bool(password),
            }

            if password:
                user_data['password_hash'] = PasswordManager.hash_password(password)
            
            result = DatabaseOperations.insert('users', user_data)
            if not result:
                return False, {'error': 'User registration failed. Check database write permissions.'}
            return True, result[0] if result else {}
        
        except Exception as e:
            print(f"Error registering user: {str(e)}")
            return False, {'error': str(e)}
    
    @staticmethod
    def login_with_otp(email: str, otp: str) -> tuple[bool, dict]:
        """Login with OTP"""
        # Verify OTP
        is_valid, message = OTPManager.verify_otp(email, otp)
        
        if not is_valid:
            return False, {'error': message}
        
        # Get or create user
        user = get_user_by_email(email)
        
        if not user:
            success, user = AuthManager.register_user(email)
            if not success:
                return False, user
        
        # Update user as verified
        DatabaseOperations.update('users', {
            'otp_verified': True,
            'email_verified': True,
            'last_login': datetime.now().isoformat()
        }, {'id': user['id']})
        
        # Generate token
        token = JWTManager.generate_token(user['id'], user['email'])
        
        return True, {
            'user': user,
            'token': token,
            'message': 'Login successful'
        }
    
    @staticmethod
    def login_with_email_password(email: str, password: str) -> tuple[bool, dict]:
        """Login with email and password"""
        try:
            user = get_user_by_email(email)
            
            if not user or not user.get('password_hash'):
                return False, {'error': 'Invalid email or password'}
            
            if not PasswordManager.verify_password(password, user['password_hash']):
                return False, {'error': 'Invalid email or password'}
            
            # Update last login
            DatabaseOperations.update('users', {
                'last_login': datetime.now().isoformat()
            }, {'id': user['id']})
            
            # Generate token
            token = JWTManager.generate_token(user['id'], user['email'])
            
            return True, {
                'user': user,
                'token': token,
                'message': 'Login successful'
            }
        
        except Exception as e:
            return False, {'error': str(e)}


def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Unauthorized'}), 401
        
        payload = JWTManager.verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Store user info in g object
        g.user_id = payload.get('user_id')
        g.email = payload.get('email')
        g.user = get_user_by_id(g.user_id)
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """Decorator to ensure the current user is an admin"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        from flask import g
        if not g.user or not g.user.get('is_admin'):
            return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)

    return decorated_function
