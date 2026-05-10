"""
Shopping Cart and Orders Routes
"""
from flask import Blueprint, request, jsonify, g
from app.utils.auth import login_required
from app.utils.payment import PaymentManager, OrderManager, CouponManager
from app.utils.common import get_utc_now
from app.utils.support import EmailService
from app.models import DatabaseOperations, Database, get_user_cart, get_user_orders, get_product_by_id
from datetime import datetime

orders_bp = Blueprint('orders', __name__, url_prefix='/api')


def calculate_cart_subtotal(cart_items: list) -> float:
    return round(
        sum(float(item['products']['price']) * int(item['quantity']) for item in cart_items),
        2
    )


@orders_bp.route('/coupons/validate', methods=['POST'])
def validate_coupon():
    """Validate a coupon code for a subtotal."""
    try:
        data = request.get_json() or {}
        coupon_code = data.get('coupon_code')
        subtotal = float(data.get('subtotal', 0) or 0)
        result = CouponManager.validate_coupon(coupon_code, subtotal)

        status_code = 200 if result.get('valid') else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500

@orders_bp.route('/cart', methods=['GET'])
@login_required
def get_cart():
    """Get user cart"""
    try:
        cart_items = get_user_cart(g.user_id)
        
        total_price = sum(item['products']['price'] * item['quantity'] for item in cart_items)
        
        return jsonify({
            'items': cart_items,
            'total': len(cart_items),
            'total_price': total_price
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/cart', methods=['POST'])
@login_required
def add_to_cart():
    """Add product to cart"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400
        
        # Check if product exists
        product = get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Check stock
        if product['stock_quantity'] < quantity:
            return jsonify({'error': 'Insufficient stock'}), 400
        
        # Check if already in cart
        existing = DatabaseOperations.select('carts', 
                                            filters={'user_id': g.user_id, 'product_id': product_id})
        
        if existing:
            # Update quantity
            new_quantity = existing[0]['quantity'] + quantity
            DatabaseOperations.update('carts', {'quantity': new_quantity}, 
                                     {'user_id': g.user_id, 'product_id': product_id})
        else:
            # Add to cart
            cart_data = {
                'user_id': g.user_id,
                'product_id': product_id,
                'quantity': quantity,
                'added_at': get_utc_now()
            }
            DatabaseOperations.insert('carts', cart_data)
        
        return jsonify({'message': 'Product added to cart'}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/cart/<product_id>', methods=['PUT'])
@login_required
def update_cart_item(product_id):
    """Update cart item quantity"""
    try:
        data = request.get_json()
        quantity = data.get('quantity')
        
        if not quantity or quantity < 1:
            return jsonify({'error': 'Invalid quantity'}), 400
        
        # Check product stock
        product = get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        if product['stock_quantity'] < quantity:
            return jsonify({'error': 'Insufficient stock'}), 400
        
        DatabaseOperations.update('carts', {'quantity': quantity}, 
                                 {'user_id': g.user_id, 'product_id': product_id})
        
        return jsonify({'message': 'Cart updated'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/cart/<product_id>', methods=['DELETE'])
@login_required
def remove_from_cart(product_id):
    """Remove product from cart"""
    try:
        DatabaseOperations.delete('carts', 
                                 {'user_id': g.user_id, 'product_id': product_id})
        
        return jsonify({'message': 'Product removed from cart'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/orders', methods=['GET'])
@login_required
def list_orders():
    """Get user orders"""
    try:
        orders = get_user_orders(g.user_id)
        
        return jsonify({
            'orders': orders,
            'total': len(orders)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/orders', methods=['POST'])
@login_required
def create_order():
    """Create new order"""
    try:
        data = request.get_json()
        
        shipping_address = data.get('shipping_address')
        billing_address = data.get('billing_address')
        payment_method = data.get('payment_method', 'cod')
        notes = data.get('notes')
        coupon_code = (data.get('coupon_code') or '').strip()
        
        if not shipping_address:
            return jsonify({'error': 'Shipping address is required'}), 400
        
        # Get cart items
        cart_items = get_user_cart(g.user_id)
        
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400

        subtotal_amount = calculate_cart_subtotal(cart_items)
        coupon_result = {'valid': False, 'discount_amount': 0, 'coupon_code': ''}
        if coupon_code:
            coupon_result = CouponManager.validate_coupon(coupon_code, subtotal_amount)
            if not coupon_result.get('valid'):
                return jsonify({'error': coupon_result.get('message', 'Invalid coupon code')}), 400

        discount_amount = float(coupon_result.get('discount_amount') or 0)

        if coupon_result.get('coupon_code'):
            coupon_note = f"Coupon applied: {coupon_result['coupon_code']}"
            notes = f"{notes}\n{coupon_note}" if notes else coupon_note
        
        # Prepare order items
        order_items = []
        for item in cart_items:
            order_items.append({
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'price': item['products']['price']
            })
        
        # Create order
        success, order = OrderManager.create_order(
            g.user_id, order_items, shipping_address, billing_address, notes, discount_amount=discount_amount
        )
        
        if not success:
            return jsonify({'error': 'Failed to create order'}), 500
        
        # Create payment record
        payment = PaymentManager.create_payment_record(
            order['id'], order['total_amount'], payment_method
        )
        
        # Update order with payment method
        DatabaseOperations.update('orders', {'payment_method': payment_method}, {'id': order['id']})
        
        # Clear cart
        db = Database.get_client()
        for cart_item in cart_items:
            db.table('carts').delete().eq('id', cart_item['id']).execute()
        
        # Send confirmation email
        user_email = g.user.get('email')
        user_name = g.user.get('full_name', 'Customer')
        EmailService.send_order_confirmation(user_email, user_name, order['order_number'], order['total_amount'])
        EmailService.send_order_notification(
            order['order_number'],
            user_name,
            user_email,
            order['total_amount'],
            payment_method,
            shipping_address
        )
        
        return jsonify({
            'message': 'Order created successfully',
            'order': order,
            'payment_method': payment_method,
            'subtotal_amount': subtotal_amount,
            'discount_amount': discount_amount,
            'coupon_code': coupon_result.get('coupon_code', '')
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/orders/buy-now', methods=['POST'])
@login_required
def buy_now_order():
    """Create order directly for a single product without using cart."""
    try:
        data = request.get_json() or {}
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        payment_method = data.get('payment_method', 'cod')
        coupon_code = (data.get('coupon_code') or '').strip()
        shipping_address = data.get('shipping_address') or {
            'full_name': g.user.get('full_name') or 'Customer',
            'email': g.user.get('email'),
            'phone': g.user.get('phone') or '',
            'address_line': 'Address to be updated',
            'city': 'NA',
            'state': 'NA',
            'postal_code': '000000',
            'country': 'India'
        }

        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400

        if quantity < 1:
            return jsonify({'error': 'Quantity must be at least 1'}), 400

        product = get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        if int(product.get('stock_quantity') or 0) < quantity:
            return jsonify({'error': 'Insufficient stock'}), 400

        unit_price = float(product.get('discount_price') or product.get('price') or 0)
        subtotal_amount = round(unit_price * quantity, 2)
        coupon_result = {'valid': False, 'discount_amount': 0, 'coupon_code': ''}
        if coupon_code:
            coupon_result = CouponManager.validate_coupon(coupon_code, subtotal_amount)
            if not coupon_result.get('valid'):
                return jsonify({'error': coupon_result.get('message', 'Invalid coupon code')}), 400

        discount_amount = float(coupon_result.get('discount_amount') or 0)
        order_items = [{
            'product_id': product_id,
            'quantity': quantity,
            'price': unit_price
        }]

        success, order = OrderManager.create_order(
            g.user_id,
            order_items,
            shipping_address,
            shipping_address,
            data.get('notes'),
            discount_amount=discount_amount
        )

        if not success:
            return jsonify({'error': order.get('error', 'Failed to create order')}), 500

        payment_record = PaymentManager.create_payment_record(order['id'], order['total_amount'], payment_method)
        if payment_record.get('error'):
            return jsonify({'error': payment_record['error']}), 500

        DatabaseOperations.update('orders', {'payment_method': payment_method}, {'id': order['id']})

        user_email = g.user.get('email')
        user_name = g.user.get('full_name', 'Customer')
        EmailService.send_order_confirmation(user_email, user_name, order['order_number'], order['total_amount'])
        EmailService.send_order_notification(
            order['order_number'],
            user_name,
            user_email,
            order['total_amount'],
            payment_method,
            shipping_address
        )

        return jsonify({
            'message': 'Order created successfully',
            'order': order,
            'payment_method': payment_method,
            'subtotal_amount': subtotal_amount,
            'discount_amount': discount_amount,
            'coupon_code': coupon_result.get('coupon_code', '')
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/orders/<order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """Get order details"""
    try:
        order = OrderManager.get_order_details(order_id)
        
        if not order or order['user_id'] != g.user_id:
            return jsonify({'error': 'Order not found'}), 404
        
        return jsonify({'order': order}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/orders/<order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    """Cancel order"""
    try:
        order = OrderManager.get_order_details(order_id)
        
        if not order or order['user_id'] != g.user_id:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['order_status'] not in ['pending', 'processing']:
            return jsonify({'error': 'Cannot cancel this order'}), 400
        
        # Update order status
        OrderManager.update_order_status(order_id, 'cancelled')
        
        # Update payment status
        PaymentManager.update_payment_status(order_id, 'cancelled')
        
        return jsonify({'message': 'Order cancelled successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500



