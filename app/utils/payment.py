"""
Payment utilities for COD payment methods
"""
from datetime import datetime, timezone, timedelta
import uuid
from config import get_config
from app.models import DatabaseOperations
from app.utils.common import get_utc_now

config = get_config()


class CouponManager:
    """Manage coupon rules for checkout discounts - fetched from database."""

    @staticmethod
    def normalize_coupon_code(coupon_code: str) -> str:
        return (coupon_code or '').strip().upper()

    @staticmethod
    def get_coupon_from_db(coupon_code: str) -> dict:
        """Fetch coupon details from database by code."""
        try:
            coupon = DatabaseOperations.select_one('coupons', {
                'code': coupon_code,
                'is_active': True
            })
            return coupon if coupon else None
        except Exception:
            return None

    @classmethod
    def validate_coupon(cls, coupon_code: str, subtotal: float) -> dict:
        normalized_code = cls.normalize_coupon_code(coupon_code)

        if not normalized_code:
            return {
                'valid': False,
                'coupon_code': '',
                'discount_amount': 0,
                'total_amount': round(float(subtotal or 0), 2),
                'message': 'Coupon code is required'
            }

        # Fetch coupon from database
        coupon = cls.get_coupon_from_db(normalized_code)
        if not coupon:
            return {
                'valid': False,
                'coupon_code': normalized_code,
                'discount_amount': 0,
                'total_amount': round(float(subtotal or 0), 2),
                'message': 'Invalid or expired coupon code'
            }

        # Check if coupon has expired
        if coupon.get('expiry_date'):
            from datetime import datetime as dt
            expiry = coupon['expiry_date']
            if isinstance(expiry, str):
                expiry = dt.fromisoformat(expiry.replace('Z', '+00:00'))
            if dt.now(expiry.tzinfo if hasattr(expiry, 'tzinfo') else None) > expiry:
                return {
                    'valid': False,
                    'coupon_code': normalized_code,
                    'discount_amount': 0,
                    'total_amount': round(float(subtotal or 0), 2),
                    'message': 'This coupon has expired'
                }

        # Check usage limit
        if coupon.get('usage_limit') and coupon.get('usage_count', 0) >= coupon['usage_limit']:
            return {
                'valid': False,
                'coupon_code': normalized_code,
                'discount_amount': 0,
                'total_amount': round(float(subtotal or 0), 2),
                'message': 'This coupon usage limit has been reached'
            }

        subtotal_value = float(subtotal or 0)
        min_amount = float(coupon.get('min_amount') or 0)
        if subtotal_value < min_amount:
            return {
                'valid': False,
                'coupon_code': normalized_code,
                'discount_amount': 0,
                'total_amount': round(subtotal_value, 2),
                'message': f"This coupon applies on orders above ₹{int(min_amount)}"
            }

        # Calculate discount based on type
        discount_type = coupon.get('discount_type', 'percent').lower()
        if discount_type == 'percent':
            discount_amount = subtotal_value * (float(coupon.get('discount_value', 0)) / 100.0)
            max_discount = float(coupon.get('max_discount') or 0)
            if max_discount > 0:
                discount_amount = min(discount_amount, max_discount)
        else:  # flat
            discount_amount = float(coupon.get('discount_value', 0))

        discount_amount = round(min(discount_amount, subtotal_value), 2)
        total_amount = round(max(0, subtotal_value - discount_amount), 2)

        return {
            'valid': True,
            'coupon_code': normalized_code,
            'coupon': coupon,
            'discount_amount': discount_amount,
            'subtotal_amount': round(subtotal_value, 2),
            'total_amount': total_amount,
            'message': f"Coupon {normalized_code} applied successfully"
        }

class PaymentManager:
    """Manage payment processing"""
    
    PAYMENT_METHODS = {
        'cod': 'Cash on Delivery'
    }
    
    @staticmethod
    def create_payment_record(order_id: str, amount: float, payment_method: str) -> dict:
        """Create payment record in database"""
        try:
            payment_data = {
                'order_id': order_id,
                'amount': amount,
                'payment_method': payment_method,
                'payment_status': 'pending',
                'created_at': get_utc_now()
            }
            
            result = DatabaseOperations.insert('payments', payment_data)
            if not result:
                return {
                    'error': 'Failed to create payment record. Check payments table RLS/permissions.'
                }
            return result[0]
        
        except Exception as e:
            print(f"Error creating payment record: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def update_payment_status(order_id: str, status: str, transaction_id: str = None) -> bool:
        """Update payment status"""
        try:
            update_data = {
                'payment_status': status,
                'updated_at': get_utc_now()
            }
            
            if transaction_id:
                update_data['transaction_id'] = transaction_id
            
            DatabaseOperations.update('payments', update_data, {'order_id': order_id})
            return True
        
        except Exception as e:
            print(f"Error updating payment: {str(e)}")
            return False
    
    @staticmethod
    def process_cod(order_id: str, total_amount: float) -> dict:
        """Process Cash on Delivery"""
        try:
            payment_data = {
                'order_id': order_id,
                'amount': total_amount,
                'payment_method': 'cod',
                'payment_status': 'pending',
                'created_at': get_utc_now()
            }
            
            result = DatabaseOperations.insert('payments', payment_data)
            
            return {
                'success': True,
                'payment_id': result[0]['id'] if result else None,
                'message': 'Order placed successfully. Payment at delivery.'
            }
        
        except Exception as e:
            print(f"Error processing COD: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_payment_details(order_id: str) -> dict:
        """Get payment details for an order"""
        try:
            payments = DatabaseOperations.select('payments', filters={'order_id': order_id})
            return payments[0] if payments else None
        
        except Exception as e:
            print(f"Error getting payment details: {str(e)}")
            return None


class OrderManager:
    """Manage orders"""
    
    @staticmethod
    def generate_order_number() -> str:
        """Generate unique order number"""
        return f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    @staticmethod
    def create_order(user_id: str, items: list, shipping_address: dict, 
                    billing_address: dict = None, notes: str = None, discount_amount: float = 0) -> tuple[bool, dict]:
        """Create new order"""
        try:
            # Calculate total
            subtotal_amount = sum(item['price'] * item['quantity'] for item in items)
            discount_amount = round(float(discount_amount or 0), 2)
            total_amount = round(max(0, subtotal_amount - discount_amount), 2)
            
            order_data = {
                'user_id': user_id,
                'order_number': OrderManager.generate_order_number(),
                'total_amount': total_amount,
                'discount_amount': discount_amount,
                'payment_method': 'pending',
                'payment_status': 'pending',
                'order_status': 'pending',
                'shipping_address': shipping_address,
                'billing_address': billing_address or shipping_address,
                'notes': notes,
                'created_at': get_utc_now(),
                'updated_at': get_utc_now()
            }
            
            result = DatabaseOperations.insert('orders', order_data)
            order = result[0] if result else None
            
            if not order:
                return False, {'error': 'Failed to create order. Check orders table RLS/permissions.'}
            
            # Create order items
            for item in items:
                item_data = {
                    'order_id': order['id'],
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'total_price': item['price'] * item['quantity']
                }
                item_result = DatabaseOperations.insert('order_items', item_data)
                if not item_result:
                    return False, {'error': 'Failed to create order items. Check order_items table RLS/permissions.'}
            
            return True, order
        
        except Exception as e:
            print(f"Error creating order: {str(e)}")
            return False, {'error': str(e)}
    
    @staticmethod
    def update_order_status(order_id: str, status: str) -> bool:
        """Update order status"""
        try:
            DatabaseOperations.update('orders', {
                'order_status': status,
                'updated_at': get_utc_now()
            }, {'id': order_id})
            return True
        
        except Exception as e:
            print(f"Error updating order: {str(e)}")
            return False
    
    @staticmethod
    def get_order_details(order_id: str) -> dict:
        """Get order details with items"""
        try:
            from app.models import Database
            db = Database.get_client()
            
            result = db.table('orders').select('*, order_items(*, products(*))').eq('id', order_id).execute()
            return result.data[0] if result.data else None
        
        except Exception as e:
            print(f"Error getting order: {str(e)}")
            return None
