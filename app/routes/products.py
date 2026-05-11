"""
Product Routes
"""
from flask import Blueprint, request, jsonify
from app.models import DatabaseOperations, Database, get_products_by_category, get_all_categories, get_product_by_id, get_product_reviews
from app.utils.auth import login_required, admin_required
from app.utils.common import get_utc_now
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid
import re
import json

products_bp = Blueprint('products', __name__, url_prefix='/api/products')

@products_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all product categories"""
    try:
        categories = get_all_categories()
        return jsonify({
            'categories': categories,
            'total': len(categories)
        }), 200
    
    except Exception as e:
        return jsonify({
            'categories': [],
            'total': 0,
            'fallback': True
        }), 200


def slugify_category(value: str) -> str:
    value = (value or '').strip().lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    return value.strip('-')


def save_uploaded_media(uploaded_file, folder_name: str) -> str:
    if not uploaded_file or not getattr(uploaded_file, 'filename', ''):
        return ''

    uploads_root = Path(__file__).resolve().parents[1] / 'static' / 'uploads' / folder_name
    uploads_root.mkdir(parents=True, exist_ok=True)

    safe_name = secure_filename(uploaded_file.filename)
    suffix = Path(safe_name).suffix or '.bin'
    file_name = f"{uuid.uuid4().hex}{suffix}"
    file_path = uploads_root / file_name
    uploaded_file.save(file_path)

    return f"/static/uploads/{folder_name}/{file_name}"


def normalize_product_images(product: dict) -> dict:
    """Ensure product.images is always a list for frontend rendering."""
    if not isinstance(product, dict):
        return product

    images_value = product.get('images')
    if isinstance(images_value, list):
        return product

    if isinstance(images_value, str):
        try:
            parsed_images = json.loads(images_value)
            if isinstance(parsed_images, list):
                product['images'] = parsed_images
            elif images_value:
                product['images'] = [images_value]
            else:
                product['images'] = []
        except Exception:
            product['images'] = [images_value] if images_value else []
        return product

    product['images'] = []
    return product


def normalize_images_input(images_value) -> list:
    """Normalize incoming images payload to a list of URLs/paths."""
    if isinstance(images_value, list):
        return [img for img in images_value if img]

    if isinstance(images_value, str):
        try:
            parsed = json.loads(images_value)
            if isinstance(parsed, list):
                return [img for img in parsed if img]
        except Exception:
            return [images_value] if images_value else []

        return [images_value] if images_value else []

    return []


@products_bp.route('/categories/admin', methods=['POST', 'PUT'])
@login_required
@admin_required
def manage_category():
    """Create or update categories from the admin dashboard"""
    try:
        data = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
        category_id = data.get('id')
        name = (data.get('name') or '').strip()
        slug = (data.get('slug') or '').strip() or slugify_category(name)
        description = data.get('description')
        image_file = request.files.get('image_file')
        image_url = save_uploaded_media(image_file, 'categories') if image_file and image_file.filename else data.get('image_url')

        if not name:
            return jsonify({'error': 'Category name is required'}), 400

        if request.method == 'POST':
            if DatabaseOperations.select_one('categories', {'slug': slug}):
                slug = f"{slug}-{str(uuid.uuid4())[:4]}"

            category_data = {
                'id': str(uuid.uuid4()),
                'name': name,
                'slug': slug,
                'description': description,
                'image_url': image_url,
                'created_at': get_utc_now()
            }

            result = DatabaseOperations.insert('categories', category_data)
            return jsonify({
                'message': 'Category created successfully',
                'category': result[0] if result else category_data
            }), 201

        if not category_id:
            return jsonify({'error': 'Category id is required'}), 400

        existing = DatabaseOperations.select_one('categories', {'id': category_id})
        if not existing:
            return jsonify({'error': 'Category not found'}), 404

        duplicate = DatabaseOperations.select_one('categories', {'slug': slug})
        if duplicate and duplicate.get('id') != category_id:
            return jsonify({'error': 'Category slug already exists'}), 400

        update_data = {
            'name': name,
            'slug': slug,
            'description': description,
            'image_url': image_url or existing.get('image_url'),
            'updated_at': get_utc_now()
        }
        DatabaseOperations.update('categories', update_data, {'id': category_id})

        return jsonify({
            'message': 'Category updated successfully',
            'category': {**existing, **update_data}
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/categories/<category_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_category(category_id):
    """Delete a category if no products are using it."""
    try:
        category = DatabaseOperations.select_one('categories', {'id': category_id})
        if not category:
            return jsonify({'error': 'Category not found'}), 404

        linked_products = DatabaseOperations.select('products', filters={'category_id': category_id})
        if linked_products:
            return jsonify({
                'error': 'Delete or move products in this category first',
                'linked_products': len(linked_products)
            }), 400

        DatabaseOperations.delete('categories', {'id': category_id})
        return jsonify({'message': 'Category deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/category/<category_id>', methods=['GET'])
def get_category(category_id):
    """Get single category"""
    try:
        category = DatabaseOperations.select_one('categories', {'id': category_id})
        
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        return jsonify({'category': category}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/', methods=['GET'])
def list_products():
    """List all products with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        category_id = request.args.get('category_id')
        search = request.args.get('search')
        sort_by = request.args.get('sort_by', 'created_at')
        
        db = Database.get_client()
        
        # Start query
        query = db.table('products').select('*')
        
        # Apply filters
        if category_id:
            query = query.eq('category_id', category_id)
        
        if search:
            # Note: Full-text search requires specific setup in Supabase
            # For now, we'll filter by name
            query = query.ilike('name', f'%{search}%')
        
        # Filter active products
        query = query.eq('is_active', True)
        
        # Order and pagination
        if sort_by == 'price_low':
            query = query.order('price', desc=False)
        elif sort_by == 'price_high':
            query = query.order('price', desc=True)
        elif sort_by == 'name':
            query = query.order('name', desc=False)
        else:
            query = query.order('rating', desc=True)

        query = query.range((page-1)*limit, page*limit-1)
        
        result = query.execute()
        products = result.data or []
        products = [normalize_product_images(product) for product in products]

        if sort_by == 'rating':
            products = sorted(
                products,
                key=lambda item: (float(item.get('rating') or 0), int(item.get('total_reviews') or 0)),
                reverse=True
            )
        elif sort_by == 'price_low':
            products = sorted(products, key=lambda item: float(item.get('discount_price') or item.get('price') or 0))
        elif sort_by == 'price_high':
            products = sorted(products, key=lambda item: float(item.get('discount_price') or item.get('price') or 0), reverse=True)
        elif sort_by == 'name':
            products = sorted(products, key=lambda item: (item.get('name') or '').lower())
        
        return jsonify({
            'products': products,
            'page': page,
            'limit': limit,
            'total': len(products)
        }), 200
    
    except Exception as e:
        return jsonify({
            'products': [],
            'page': request.args.get('page', 1, type=int),
            'limit': request.args.get('limit', 20, type=int),
            'total': 0,
            'fallback': True
        }), 200


@products_bp.route('/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details"""
    try:
        product = get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        category = None
        if product.get('category_id'):
            category = DatabaseOperations.select_one('categories', {'id': product.get('category_id')})
        product['categories'] = {'name': category.get('name')} if category else {'name': 'Uncategorized'}

        product = normalize_product_images(product)

        # Get reviews
        reviews = get_product_reviews(product_id) or []

        # Calculate average rating
        if reviews:
            rating_values = [float(r.get('rating', 0)) for r in reviews if r.get('rating') is not None]
            avg_rating = (sum(rating_values) / len(rating_values)) if rating_values else 0
            product['average_rating'] = round(avg_rating, 2)

        product['reviews'] = reviews

        return jsonify({'product': product}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/<product_id>/similar', methods=['GET'])
def get_similar_products(product_id):
    """Get similar products for product detail page."""
    try:
        limit = request.args.get('limit', 6, type=int)
        current = get_product_by_id(product_id)
        if not current:
            return jsonify({'error': 'Product not found'}), 404

        category_id = current.get('category_id')
        if category_id:
            candidates = DatabaseOperations.select('products', filters={'category_id': category_id, 'is_active': True})
        else:
            candidates = DatabaseOperations.select('products', filters={'is_active': True})

        filtered = [p for p in (candidates or []) if p.get('id') != product_id]
        filtered = [normalize_product_images(p) for p in filtered]
        filtered = sorted(
            filtered,
            key=lambda item: (float(item.get('rating') or 0), int(item.get('total_reviews') or 0)),
            reverse=True
        )

        return jsonify({'products': filtered[:max(1, limit)], 'total': len(filtered)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/<product_id>/reviews', methods=['GET'])
def get_product_reviews_route(product_id):
    """Get product reviews"""
    try:
        reviews = get_product_reviews(product_id)
        
        return jsonify({
            'reviews': reviews,
            'total': len(reviews)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/<product_id>/reviews', methods=['POST'])
@login_required
def add_review(product_id):
    """Add product review"""
    try:
        from flask import g
        
        data = request.get_json() or {}
        rating = int(data.get('rating', 0))
        review_text = (data.get('review_text') or data.get('comment') or '').strip()
        
        if not rating or not (1 <= rating <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Check if user already reviewed this product
        existing_review = DatabaseOperations.select('reviews', 
                                                   filters={'product_id': product_id, 'user_id': g.user_id})
        
        if existing_review:
            return jsonify({'error': 'You have already reviewed this product'}), 400
        
        review_data = {
            'product_id': product_id,
            'user_id': g.user_id,
            'rating': rating,
            'review_text': review_text,
            'created_at': get_utc_now()
        }
        
        result = DatabaseOperations.insert('reviews', review_data)
        
        # Update product rating
        all_reviews = get_product_reviews(product_id)
        if all_reviews:
            avg_rating = sum(r['rating'] for r in all_reviews) / len(all_reviews)
            DatabaseOperations.update('products', {
                'rating': round(avg_rating, 2),
                'total_reviews': len(all_reviews)
            }, {'id': product_id})
        
        return jsonify({
            'message': 'Review added successfully',
            'review': result[0] if result else {}
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/<product_id>/helpful/<review_id>', methods=['POST'])
def mark_review_helpful(product_id, review_id):
    """Mark review as helpful"""
    try:
        review = DatabaseOperations.select_one('reviews', {'id': review_id})
        
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        new_count = review.get('helpful_count', 0) + 1
        
        DatabaseOperations.update('reviews', {
            'helpful_count': new_count
        }, {'id': review_id})
        
        return jsonify({'message': 'Marked as helpful'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/search', methods=['GET'])
def search_products():
    """Search products"""
    try:
        query = request.args.get('q', '')
        
        if not query or len(query) < 2:
            return jsonify({'error': 'Search query must be at least 2 characters'}), 400
        
        db = Database.get_client()
        
        # Search by name or description
        result = db.table('products').select('*').ilike('name', f'%{query}%').eq('is_active', True).execute()
        
        products = result.data or []
        
        return jsonify({
            'query': query,
            'products': products,
            'total': len(products)
        }), 200
    
    except Exception as e:
        return jsonify({
            'query': request.args.get('q', ''),
            'products': [],
            'total': 0,
            'fallback': True
        }), 200


@products_bp.route('/admin', methods=['POST', 'PUT'])
@login_required
def create_product():
    """Create a product for admin users only"""
    try:
        from flask import g

        if not g.user or not g.user.get('is_admin'):
            return jsonify({'error': 'Admin access required'}), 403

        data = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
        image_files = request.files.getlist('image_files')
        uploaded_images = [
            save_uploaded_media(file, 'products')
            for file in image_files
            if file and getattr(file, 'filename', '')
        ]

        # Backward compatibility for older single-file input.
        if not uploaded_images:
            image_file = request.files.get('image_file')
            if image_file and image_file.filename:
                uploaded_images = [save_uploaded_media(image_file, 'products')]

        if request.method == 'POST':
            required_fields = ['category_id', 'name', 'price']
            missing_fields = [field for field in required_fields if not data.get(field)]

            if missing_fields:
                return jsonify({'error': f"Missing fields: {', '.join(missing_fields)}"}), 400

            category = DatabaseOperations.select_one('categories', {'id': data.get('category_id')})
            if not category:
                return jsonify({'error': 'Select a valid category'}), 400

            product_data = {
                'id': str(uuid.uuid4()),
                'category_id': data.get('category_id'),
                'name': data.get('name'),
                'description': data.get('description'),
                'price': float(data.get('price')),
                'discount_price': float(data['discount_price']) if data.get('discount_price') not in [None, ''] else None,
                'stock_quantity': int(data.get('stock_quantity', 0)),
                'images': uploaded_images if uploaded_images else normalize_images_input(data.get('images')),
                'specifications': data.get('specifications'),
                'expected_delivery_date': data.get('expected_delivery_date'),
                'rating': 0,
                'total_reviews': 0,
                'is_active': True,
                'created_at': get_utc_now()
            }

            # Debug logging for troubleshooting missing fields
            print(f"DEBUG: Creating product payload (id={product_data.get('id')}), description repr: {repr(product_data.get('description'))}")
            try:
                result = DatabaseOperations.insert('products', product_data)
            except Exception as insert_error:
                error_text = str(insert_error).lower()
                if 'expected_delivery_date' in error_text and ('column' in error_text or 'schema' in error_text):
                    # Backward compatibility for databases that have not yet added this column.
                    product_data.pop('expected_delivery_date', None)
                    result = DatabaseOperations.insert('products', product_data)
                else:
                    raise

            print(f"DEBUG: Insert result for product id={product_data.get('id')}: {result}")

            return jsonify({
                'message': 'Product created successfully',
                'product': result[0] if result else product_data
            }), 201

        product_id = data.get('id')
        if not product_id:
            return jsonify({'error': 'Product id is required'}), 400

        existing = DatabaseOperations.select_one('products', {'id': product_id})
        if not existing:
            return jsonify({'error': 'Product not found'}), 404

        category_id = data.get('category_id', existing.get('category_id'))
        if category_id and not DatabaseOperations.select_one('categories', {'id': category_id}):
            return jsonify({'error': 'Select a valid category'}), 400

        update_data = {
            'category_id': category_id,
            'name': data.get('name', existing.get('name')),
            'description': data.get('description', existing.get('description')),
            'price': float(data.get('price', existing.get('price', 0))),
            'discount_price': float(data['discount_price']) if data.get('discount_price') not in [None, ''] else None,
            'stock_quantity': int(data.get('stock_quantity', existing.get('stock_quantity', 0))),
            'images': uploaded_images if uploaded_images else normalize_images_input(data.get('images', existing.get('images'))),
            'specifications': data.get('specifications', existing.get('specifications')),
            'expected_delivery_date': data.get('expected_delivery_date', existing.get('expected_delivery_date')),
            'updated_at': get_utc_now()
        }

        # Debug logging for update payload
        print(f"DEBUG: Updating product id={product_id}, description repr: {repr(update_data.get('description'))}")
        try:
            DatabaseOperations.update('products', update_data, {'id': product_id})
        except Exception as update_error:
            error_text = str(update_error).lower()
            if 'expected_delivery_date' in error_text and ('column' in error_text or 'schema' in error_text):
                update_data.pop('expected_delivery_date', None)
                DatabaseOperations.update('products', update_data, {'id': product_id})
            else:
                raise

        return jsonify({
            'message': 'Product updated successfully',
            'product': {**existing, **update_data}
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/admin/<product_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_product(product_id):
    """Delete a product."""
    try:
        product = DatabaseOperations.select_one('products', {'id': product_id})
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        DatabaseOperations.delete('products', {'id': product_id})
        return jsonify({'message': 'Product deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== COUPON MANAGEMENT ROUTES (Admin) =====

@products_bp.route('/coupons/admin', methods=['GET'])
@login_required
@admin_required
def list_coupons():
    """Get all coupons for admin dashboard"""
    try:
        coupons = DatabaseOperations.select('coupons', {})
        return jsonify({
            'coupons': coupons or [],
            'total': len(coupons) if coupons else 0
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/coupons/admin', methods=['POST', 'PUT'])
@login_required
@admin_required
def manage_coupon():
    """Create or update a coupon"""
    try:
        data = request.get_json(silent=True) or {}
        coupon_id = data.get('id')
        code = (data.get('code') or '').strip().upper()
        description = data.get('description', '').strip()
        discount_type = (data.get('discount_type') or 'percent').lower()
        discount_value = float(data.get('discount_value') or 0)
        min_amount = float(data.get('min_amount') or 0) if data.get('min_amount') else None
        max_discount = float(data.get('max_discount') or 0) if data.get('max_discount') else None
        usage_limit = int(data.get('usage_limit') or 0) if data.get('usage_limit') else None
        expiry_date = data.get('expiry_date')  # ISO format: "2025-12-31T23:59:59"
        is_active = data.get('is_active', True)

        # Validation
        if not code or len(code) < 3:
            return jsonify({'error': 'Coupon code must be at least 3 characters'}), 400
        if discount_value <= 0:
            return jsonify({'error': 'Discount value must be greater than 0'}), 400
        if discount_type not in ['percent', 'flat']:
            return jsonify({'error': 'Discount type must be "percent" or "flat"'}), 400

        coupon_data = {
            'code': code,
            'description': description,
            'discount_type': discount_type,
            'discount_value': discount_value,
            'min_amount': min_amount,
            'max_discount': max_discount,
            'usage_limit': usage_limit,
            'is_active': is_active,
            'expiry_date': expiry_date,
            'updated_at': get_utc_now()
        }

        if request.method == 'POST':
            # Check if code already exists
            existing = DatabaseOperations.select_one('coupons', {'code': code})
            if existing:
                return jsonify({'error': 'Coupon code already exists'}), 400

            coupon_data['created_at'] = get_utc_now()
            coupon_data['usage_count'] = 0
            
            result = DatabaseOperations.insert('coupons', coupon_data)
            
            verify = DatabaseOperations.select_one('coupons', {'code': code})
            
            if verify:
                print(f"✓ Coupon {code} successfully saved to database")
                return jsonify({
                    'message': 'Coupon created successfully',
                    'coupon': verify
                }), 201
            else:
                print(f"✗ ERROR: Coupon {code} not found in database after insert!")
                return jsonify({
                    'error': 'Coupon creation failed - not saved to database. Check RLS policies in Supabase.'
                }), 500

        else:  # PUT
            if not coupon_id:
                return jsonify({'error': 'Coupon ID required for update'}), 400

            # Check if new code already exists (excluding current coupon)
            existing = DatabaseOperations.select_one('coupons', {'code': code})
            if existing and existing.get('id') != coupon_id:
                return jsonify({'error': 'Coupon code already exists'}), 400

            result = DatabaseOperations.update('coupons', coupon_data, {'id': coupon_id})
            return jsonify({'message': 'Coupon updated successfully', 'coupon': result}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/coupons/admin/<coupon_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_coupon(coupon_id):
    """Delete a coupon"""
    try:
        coupon = DatabaseOperations.select_one('coupons', {'id': coupon_id})
        if not coupon:
            return jsonify({'error': 'Coupon not found'}), 404

        DatabaseOperations.delete('coupons', {'id': coupon_id})
        return jsonify({'message': 'Coupon deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
