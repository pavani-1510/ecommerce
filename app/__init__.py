"""
Flask Application Factory
"""
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid
from config import get_config
from app.models import Database, DatabaseOperations, get_site_settings, get_all_categories, get_product_by_id, get_user_by_email, SYSTEM_CATEGORIES
from app.routes.auth import auth_bp
from app.routes.products import products_bp
from app.routes.orders import orders_bp
from app.routes.support import support_bp
from app.utils.auth import admin_required


def create_app(config_name=None):
    """Create and configure Flask application"""
    
    # Create Flask instance
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(support_bp)

    try:
        startup_probe = Database.probe_connection()
        if not startup_probe.get('writable'):
            print(
                "! Category bootstrap skipped: Supabase key is read-only "
                f"({startup_probe.get('key_type', 'unknown')})."
            )
        else:
            categories = get_all_categories()
            if not categories:
                for category in SYSTEM_CATEGORIES:
                    existing = DatabaseOperations.select_one('categories', {'slug': category['slug']})
                    if existing:
                        continue
                    DatabaseOperations.insert('categories', {
                        'id': str(uuid.uuid4()),
                        **category,
                        'created_at': datetime.now().isoformat()
                    })
    except Exception as e:
        print(f"! Category bootstrap skipped: {str(e)}")

    @app.context_processor
    def inject_site_settings():
        try:
            site_settings = get_site_settings()
        except Exception:
            site_settings = {}

        return {'site_settings': site_settings}
    
    # Basic routes
    @app.route('/', methods=['GET'])
    def index():
        """Frontend default home page"""
        return render_template('index.html')

    @app.route('/api', methods=['GET'])
    def api_index():
        """API root status"""
        return jsonify({
            'message': '3D Printing E-Commerce API',
            'version': '1.0.0',
            'status': 'running'
        }), 200

    @app.route('/app', methods=['GET'])
    def frontend_home():
        """Frontend home page"""
        return render_template('index.html')

    @app.route('/products', methods=['GET'])
    def products_page():
        """Products listing page"""
        return render_template('products.html')

    @app.route('/products/<product_id>', methods=['GET'])
    def product_detail_page(product_id):
        """Product detail page"""
        return render_template('product_detail.html', product_id=product_id)

    @app.route('/cart', methods=['GET'])
    def cart_page():
        """Cart page"""
        return render_template('cart.html')

    @app.route('/orders', methods=['GET'])
    def orders_page():
        """Orders page"""
        return render_template('orders.html')

    @app.route('/support', methods=['GET'])
    def support_page():
        """Support page"""
        return render_template('support.html')

    @app.route('/profile', methods=['GET'])
    def profile_page():
        """Profile page"""
        return render_template('profile.html')

    @app.route('/login', methods=['GET'])
    def frontend_login():
        """Frontend login page"""
        return render_template('login.html')

    @app.route('/admin/products', methods=['GET'])
    def admin_products_page():
        """Admin product management page"""
        return render_template('admin_products.html')

    @app.route('/admin/theme', methods=['GET'])
    def admin_theme_page():
        """Admin theme page"""
        return render_template('admin_theme.html')

    @app.route('/admin/categories', methods=['GET'])
    def admin_categories_page():
        """Admin category management page"""
        return render_template('admin_categories.html')

    @app.route('/admin/support', methods=['GET'])
    def admin_support_page():
        """Admin support management page"""
        return render_template('admin_support.html')

    @app.route('/admin', methods=['GET'])
    def admin_dashboard_page():
        """Admin landing page with control cards"""
        return render_template('admin_dashboard.html')

    @app.route('/api/site-settings', methods=['GET', 'POST'])
    @admin_required
    def site_settings_api():
        """Get or update the shared storefront settings."""
        if request.method == 'GET':
            return jsonify(get_site_settings()), 200

        data = request.form.to_dict() if request.form else (request.get_json() or {})
        current_settings = get_site_settings()

        wallpaper_image_url = current_settings.get('wallpaper_image_url', '')
        wallpaper_file = request.files.get('wallpaper_file') if request.files else None
        if wallpaper_file and getattr(wallpaper_file, 'filename', ''):
            uploads_root = Path(__file__).resolve().parent / 'static' / 'uploads' / 'theme'
            uploads_root.mkdir(parents=True, exist_ok=True)
            safe_name = secure_filename(wallpaper_file.filename)
            suffix = Path(safe_name).suffix or '.bin'
            file_name = f"{uuid.uuid4().hex}{suffix}"
            file_path = uploads_root / file_name
            wallpaper_file.save(file_path)
            wallpaper_image_url = f"/static/uploads/theme/{file_name}"

        logo_image_url = current_settings.get('logo_image_url', '')
        logo_file = request.files.get('logo_file') if request.files else None
        if logo_file and getattr(logo_file, 'filename', ''):
            uploads_root = Path(__file__).resolve().parent / 'static' / 'uploads' / 'theme'
            uploads_root.mkdir(parents=True, exist_ok=True)
            safe_name = secure_filename(logo_file.filename)
            suffix = Path(safe_name).suffix or '.bin'
            file_name = f"{uuid.uuid4().hex}{suffix}"
            file_path = uploads_root / file_name
            logo_file.save(file_path)
            logo_image_url = f"/static/uploads/theme/{file_name}"

        updated_settings = {
            'id': 'default',
            'shop_name': data.get('shop_name', current_settings.get('shop_name')),
            'logo_image_url': data.get('logo_image_url', logo_image_url),
            'brand_tag': data.get('brand_tag', current_settings.get('brand_tag')),
            'hero_title': data.get('hero_title', current_settings.get('hero_title')),
            'hero_subtitle': data.get('hero_subtitle', current_settings.get('hero_subtitle')),
            'primary_color': data.get('primary_color', current_settings.get('primary_color')),
            'accent_color': data.get('accent_color', current_settings.get('accent_color')),
            'footer_text': data.get('footer_text', current_settings.get('footer_text')),
            'background_mode': data.get('background_mode', current_settings.get('background_mode')),
            'background_color': data.get('background_color', current_settings.get('background_color')),
            'background_gradient_start': data.get('background_gradient_start', current_settings.get('background_gradient_start')),
            'background_gradient_end': data.get('background_gradient_end', current_settings.get('background_gradient_end')),
            'wallpaper_image_url': data.get('wallpaper_image_url', wallpaper_image_url),
            'wallpaper_overlay_opacity': data.get('wallpaper_overlay_opacity', current_settings.get('wallpaper_overlay_opacity')),
            'updated_at': datetime.now().isoformat()
        }

        existing = DatabaseOperations.select_one('site_settings', {'id': 'default'})
        if existing:
            DatabaseOperations.update('site_settings', updated_settings, {'id': 'default'})
        else:
            DatabaseOperations.insert('site_settings', updated_settings)

        return jsonify({
            'message': 'Site settings updated successfully',
            'site_settings': updated_settings
        }), 200
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check"""
        probe = Database.probe_connection()
        db_status = 'connected' if probe.get('connected') else 'disconnected'
        
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'database_writable': probe.get('writable', False),
            'supabase_key_type': probe.get('key_type', 'unknown'),
            'database_error': probe.get('error')
        }), 200

    @app.route('/favicon.ico', methods=['GET'])
    def favicon():
        """Avoid noisy 404s when favicon is not configured."""
        return ('', 204)
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
