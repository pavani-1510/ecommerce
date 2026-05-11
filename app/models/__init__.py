"""
Database Connection and utilities
Supabase-only backend.
"""
from datetime import datetime
import json


class _UnavailableSupabaseResult:
    def __init__(self, data=None, count=0, error=None):
        self.data = data or []
        self.count = count
        self.error = error


class _SafeSupabaseTable:
    def __init__(self, table):
        self._table = table

    def select(self, *args, **kwargs):
        self._table = self._table.select(*args, **kwargs)
        return self

    def eq(self, *args, **kwargs):
        self._table = self._table.eq(*args, **kwargs)
        return self

    def ilike(self, *args, **kwargs):
        self._table = self._table.ilike(*args, **kwargs)
        return self

    def order(self, *args, **kwargs):
        self._table = self._table.order(*args, **kwargs)
        return self

    def range(self, *args, **kwargs):
        self._table = self._table.range(*args, **kwargs)
        return self

    def limit(self, *args, **kwargs):
        self._table = self._table.limit(*args, **kwargs)
        return self

    def insert(self, *args, **kwargs):
        self._table = self._table.insert(*args, **kwargs)
        return self

    def update(self, *args, **kwargs):
        self._table = self._table.update(*args, **kwargs)
        return self

    def delete(self, *args, **kwargs):
        self._table = self._table.delete(*args, **kwargs)
        return self

    def execute(self):
        try:
            return self._table.execute()
        except Exception as e:
            # Preserve underlying failure so callers can handle specific causes
            # (for example: missing column, RLS denial, connectivity issues).
            return _UnavailableSupabaseResult(error=str(e))


class _UnavailableSupabaseTable:
    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def ilike(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def range(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return self

    def delete(self, *args, **kwargs):
        return self

    def execute(self):
        return _UnavailableSupabaseResult()


class _UnavailableSupabaseClient:
    def table(self, *args, **kwargs):
        return _UnavailableSupabaseTable()

    def query(self, *args, **kwargs):
        raise ConnectionError("Supabase client unavailable")


class _SafeSupabaseClient:
    def __init__(self, client):
        self._client = client

    def table(self, *args, **kwargs):
        try:
            return _SafeSupabaseTable(self._client.table(*args, **kwargs))
        except Exception:
            return _UnavailableSupabaseTable()

    def query(self, *args, **kwargs):
        if not hasattr(self._client, 'query'):
            raise NotImplementedError(
                "Raw SQL execution is not supported by this Supabase client. "
                "Use Supabase SQL editor or migrations to create/alter tables."
            )
        return self._client.query(*args, **kwargs)


SYSTEM_SITE_SETTINGS = {
    'id': 'default',
    'shop_name': 'Mantra Made 3D Arts',
    'logo_image_url': '/static/uploads/logo.jpg',
    'brand_tag': 'spiritual decor from kuppam',
    'hero_title': 'Divine Spiritual Creations Crafted With Devotion',
    'hero_subtitle': 'Shop spiritual idols, puja decor, and sacred gifting pieces from Mantra Made 3D Arts, proudly based in Kuppam.',
    'primary_color': '#b34f32',
    'accent_color': '#1f6e64',
    'footer_text': 'We create spiritual decor from Kuppam, made for homes, temples, and meaningful gifting.',
    'background_mode': 'gradient',
    'background_color': '#f2ece2',
    'background_gradient_start': '#f8f1e7',
    'background_gradient_end': '#ece3d8',
    'wallpaper_image_url': '',
    'wallpaper_overlay_opacity': '0.35'
}

SYSTEM_CONTACT_INFO = {
    'id': 'default',
    'email': 'support@mantramade3darts.com',
    'phone': '+91-90000-00000',
    'whatsapp': '+91-90000-00000',
    'address': 'Kuppam, Andhra Pradesh, India',
    'city': 'Kuppam',
    'state': 'Andhra Pradesh',
    'country': 'India',
    'postal_code': '517425',
    'business_hours': {
        'monday_to_friday': '9:00 AM - 6:00 PM',
        'saturday': '10:00 AM - 4:00 PM',
        'sunday': 'Closed'
    }
}

SYSTEM_CATEGORIES = [
    {
        'name': 'Handcrafted',
        'slug': 'handcrafted',
        'description': 'Handcrafted items made with care and detail.',
        'image_url': 'https://via.placeholder.com/300?text=Handcrafted'
    },
    {
        'name': 'LED Lamps',
        'slug': 'led-lamps',
        'description': 'Decorative LED lamps for ambient lighting.',
        'image_url': 'https://via.placeholder.com/300?text=LED+Lamps'
    },
    {
        'name': 'Toys',
        'slug': 'toys',
        'description': 'Fun toys and playful designs for all ages.',
        'image_url': 'https://via.placeholder.com/300?text=Toys'
    },
    {
        'name': 'Spiritual Doll',
        'slug': 'spiritual-doll',
        'description': 'Spiritual dolls and devotional figurines.',
        'image_url': 'https://via.placeholder.com/300?text=Spiritual+Doll'
    },
    {
        'name': 'Home Decor Items',
        'slug': 'home-decor-items',
        'description': 'Stylish decor pieces for your home.',
        'image_url': 'https://via.placeholder.com/300?text=Home+Decor'
    }
]


class Database:
    """Database abstraction for Supabase."""
    
    _instance = None
    _db_type = None
    
    @classmethod
    def get_client(cls):
        """Get database client instance"""
        if cls._instance is None:
            from config import get_config
            cfg = get_config()
            try:
                from supabase import create_client
            except ImportError:
                raise ImportError("Supabase library not installed. Install with: pip install supabase")

            supabase_url = cfg.SUPABASE_URL
            supabase_key = cfg.SUPABASE_KEY

            if not supabase_url or not supabase_key:
                cls._instance = _UnavailableSupabaseClient()
                cls._db_type = 'unavailable'
                return cls._instance

            try:
                cls._instance = _SafeSupabaseClient(create_client(supabase_url, supabase_key))
                cls._db_type = 'supabase'
            except Exception:
                cls._instance = _UnavailableSupabaseClient()
                cls._db_type = 'unavailable'
        
        return cls._instance
    
    @classmethod
    def get_db_type(cls) -> str:
        """Returns 'supabase'"""
        if cls._db_type is None:
            cls.get_client()
        return cls._db_type
    
    @classmethod
    def initialize_tables(cls):
        """Initialize all database tables"""
        print(
            "! Skipping in-app table initialization for Supabase. "
            "Create/update tables using Supabase SQL editor or migrations."
        )
        return False

    @classmethod
    def probe_connection(cls) -> dict:
        """Return a direct Supabase connectivity and key capability probe."""
        from config import get_config
        cfg = get_config()

        supabase_url = cfg.SUPABASE_URL
        supabase_key = cfg.SUPABASE_KEY

        if not supabase_url or not supabase_key:
            return {
                'connected': False,
                'writable': False,
                'key_type': 'missing',
                'error': 'Missing SUPABASE_URL or SUPABASE key variable'
            }

        key_type = 'service_role' if (
            supabase_key.startswith('sb_secret_')
            or 'service_role' in supabase_key
        ) else 'publishable_or_anon'

        try:
            from supabase import create_client
            probe_client = create_client(supabase_url, supabase_key)
            probe_client.table('categories').select('id').limit(1).execute()
            return {
                'connected': True,
                'writable': key_type == 'service_role',
                'key_type': key_type,
                'error': None
            }
        except Exception as e:
            return {
                'connected': False,
                'writable': False,
                'key_type': key_type,
                'error': str(e)
            }


class DatabaseOperations:
    """Common database operations"""
    
    @staticmethod
    def select(table: str, columns: str = "*", filters: dict = None) -> list:
        """Select records from table"""
        db = Database.get_client()
        query = db.table(table).select(columns)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        return query.execute().data or []
    
    @staticmethod
    def select_one(table: str, filters: dict) -> dict:
        """Select single record"""
        db = Database.get_client()
        query = db.table(table).select('*')
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        result = query.limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def insert(table: str, data: dict):
        """Insert record"""
        db = Database.get_client()
        try:
            result = db.table(table).insert(data).execute()
            if getattr(result, 'error', None):
                raise RuntimeError(result.error)

            if result.data:
                return result.data

            # Some Supabase setups can return an empty payload on write failures
            # due to wrapped client fallbacks. Verify persistence before reporting success.
            record_id = data.get('id') if isinstance(data, dict) else None
            if record_id:
                persisted = DatabaseOperations.select_one(table, {'id': record_id})
                if persisted:
                    return [persisted]

            raise RuntimeError(
                f"Insert did not persist in '{table}'. "
                "Possible causes: missing column, RLS policy denial, or Supabase connectivity issue."
            )
        except Exception as e:
            print(f"ERROR: Supabase insert failed: {str(e)}")
            raise
    
    @staticmethod
    def update(table: str, data: dict, filters: dict):
        """Update record"""
        db = Database.get_client()
        query = db.table(table).update(data)
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        return query.execute().data
    
    @staticmethod
    def delete(table: str, filters: dict):
        """Delete record"""
        db = Database.get_client()
        query = db.table(table).delete()
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        return query.execute()
    
    @staticmethod
    def count(table: str, filters: dict = None) -> int:
        """Count records"""
        db = Database.get_client()
        query = db.table(table).select('*', count='exact')
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        result = query.execute()
        return result.count if hasattr(result, 'count') else len(result.data or [])


# Helper functions for common operations

def get_user_by_email(email: str):
    """Get user by email"""
    return DatabaseOperations.select_one('users', {'email': email})


def get_user_by_id(user_id: str):
    """Get user by ID"""
    return DatabaseOperations.select_one('users', {'id': user_id})


def get_product_by_id(product_id: str):
    """Get product by ID"""
    return DatabaseOperations.select_one('products', {'id': product_id})


def get_products_by_category(category_id: str, limit: int = 20):
    """Get products by category"""
    db = Database.get_client()
    return db.table('products').select('*').eq('category_id', category_id).limit(limit).execute().data or []


def get_all_categories():
    """Get all categories"""
    return DatabaseOperations.select('categories')


def get_site_settings():
    """Get site-wide settings"""
    try:
        settings = DatabaseOperations.select_one('site_settings', {'id': 'default'})
        return settings or SYSTEM_SITE_SETTINGS
    except Exception:
        return SYSTEM_SITE_SETTINGS


def get_user_cart(user_id: str):
    """Get user's cart items"""
    db = Database.get_client()

    # Prefer explicit lookups over nested relationship selects because
    # PostgREST relation metadata may not be available in some Supabase setups.
    cart_rows = db.table('carts').select('*').eq('user_id', user_id).execute().data or []
    if not cart_rows:
        return []

    items = []
    for row in cart_rows:
        product = None
        product_id = row.get('product_id')
        if product_id:
            product = get_product_by_id(product_id)

        merged_row = dict(row)
        merged_row['products'] = product or {}
        items.append(merged_row)

    return items


def get_user_orders(user_id: str):
    """Get user's orders"""
    db = Database.get_client()

    orders = db.table('orders').select('*').eq('user_id', user_id).order('created_at', desc=True).execute().data or []
    if not orders:
        return []

    for order in orders:
        order_id = order.get('id')
        if not order_id:
            order['order_items'] = []
            continue

        order_items = db.table('order_items').select('*').eq('order_id', order_id).execute().data or []

        for item in order_items:
            product_id = item.get('product_id')
            item['products'] = get_product_by_id(product_id) if product_id else {}

        order['order_items'] = order_items

    return orders


def get_product_reviews(product_id: str):
    """Get product reviews"""
    db = Database.get_client()
    return db.table('reviews').select('*, users(full_name)').eq('product_id', product_id).order('created_at', desc=True).execute().data or []
