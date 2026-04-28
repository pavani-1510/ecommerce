"""
Payment utilities for QR Code and COD payment methods
"""
from datetime import datetime
import uuid
import qrcode
from io import BytesIO
import base64
from config import get_config
from app.models import DatabaseOperations

config = get_config()

class PaymentManager:
    """Manage payment processing"""
    
    PAYMENT_METHODS = {
        'qr': 'QR Code Payment',
        'cod': 'Cash on Delivery'
    }
    
    @staticmethod
    def generate_qr_code(order_id: str, amount: float) -> dict:
        """Generate QR code for payment"""
        try:
            # Create payment message with order ID and amount
            payment_message = f"Order:{order_id}|Amount:{amount}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(payment_message)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 string
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            return {
                'success': True,
                'qr_code': f"data:image/png;base64,{img_str}",
                'payment_message': payment_message,
                'order_id': order_id,
                'amount': amount
            }
        
        except Exception as e:
            print(f"Error generating QR code: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_payment_record(order_id: str, amount: float, payment_method: str) -> dict:
        """Create payment record in database"""
        try:
            payment_data = {
                'order_id': order_id,
                'amount': amount,
                'payment_method': payment_method,
                'payment_status': 'pending' if payment_method == 'qr' else 'pending',
                'created_at': datetime.now().isoformat()
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
                'updated_at': datetime.now().isoformat()
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
                'created_at': datetime.now().isoformat()
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
    def verify_qr_payment(order_id: str, transaction_id: str) -> dict:
        """Verify QR code payment (manual verification)"""
        try:
            result = PaymentManager.update_payment_status(order_id, 'completed', transaction_id)
            
            if result:
                return {
                    'success': True,
                    'message': 'Payment verified successfully',
                    'transaction_id': transaction_id
                }
            else:
                return {'success': False, 'error': 'Failed to verify payment'}
        
        except Exception as e:
            print(f"Error verifying QR payment: {str(e)}")
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
                    billing_address: dict = None, notes: str = None) -> tuple[bool, dict]:
        """Create new order"""
        try:
            # Calculate total
            total_amount = sum(item['price'] * item['quantity'] for item in items)
            
            order_data = {
                'user_id': user_id,
                'order_number': OrderManager.generate_order_number(),
                'total_amount': total_amount,
                'payment_method': 'pending',
                'payment_status': 'pending',
                'order_status': 'pending',
                'shipping_address': shipping_address,
                'billing_address': billing_address or shipping_address,
                'notes': notes,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
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
                'updated_at': datetime.now().isoformat()
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
