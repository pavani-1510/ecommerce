# 3D Printing E-Commerce Platform

A complete, production-ready e-commerce website for 3D printing products, handcrafted items, LED lamps, toys, spiritual dolls, and home decor items.

## ⚡ Quick Start (Local No-Setup Mode)

Want to run locally **without Supabase**? We got you!

```bash
# 1. Clone & setup
git clone <repo-url>
cd 3d-printing-ecommerce
python -m venv venv
source venv/bin/activate

# 2. Install & initialize
pip install -r requirements.txt
python init_local_db.py

# 3. Run!
python wsgi.py
```

**That's it!** App is running at `http://localhost:5000` with local SQLite database.

👉 **See [LOCAL_SETUP.md](LOCAL_SETUP.md)** for detailed local development guide.

---

## Features

### Authentication
- **Email OTP Login**: Send OTP via email only
- **Email & Password Login**: Traditional password-based authentication
- **Secure JWT Tokens**: Session management with JWT

### Product Management
- **Multiple Categories**: Handcrafted, LED lamps, Toys, Spiritual dolls, Home decor
- **Product Listings**: Browse and search products
- **Product Details**: View full product information, specifications
- **Reviews & Ratings**: Customer reviews with ratings
- **Product Images**: Multiple images per product

### Shopping Cart & Orders
- **Shopping Cart**: Add/Remove products, update quantities
- **Order Management**: Create orders, track status
- **Order History**: View past orders and details
- **Order Items**: Detailed breakdown of items in each order

### Payment Methods
- **QR Code (UPI)**: Scan QR code with UPI app for instant payment
- **Cash on Delivery**: Pay when order arrives

### Customer Support
- **Support Tickets**: Create and manage support tickets
- **Email Support**: Send emails to customers
- **FAQ Section**: Common questions and answers
- **Contact Information**: Easy access to contact details

### Business Hours & Contact
- **Contact Details**: Email, Phone, WhatsApp
- **Business Hours**: Display operating hours
- **Contact Form**: For inquiries

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite (Local) or Supabase PostgreSQL (Cloud) - 100% compatible!
- **Authentication**: JWT, Email OTP
- **Payment**: QR Code generation (UPI)
- **Email**: SMTP (Gmail compatible)

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Responsive design
- **JavaScript**: Interactive functionality
- **Razorpay Checkout**: Payment integration

### Deployment
- **WSGI Server**: Gunicorn
- **Environment**: Docker ready

## Installation & Setup

### Choose Your Setup:

#### 🚀 **Option A: Local Development (SQLite) - Recommended for Getting Started**

```bash
# Quick setup with no external services
git clone <repository-url>
cd 3d-printing-ecommerce
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_local_db.py
python wsgi.py
```

**That's it!** See [LOCAL_SETUP.md](LOCAL_SETUP.md) for details.

**What you get:**
- ✅ Local SQLite database (no Supabase needed)
- ✅ Sample products and users pre-loaded
- ✅ Works completely offline
- ✅ Perfect for development and testing

---

#### ☁️ **Option B: Production with Supabase (PostgreSQL)**

See [SETUP.md](SETUP.md) for complete Supabase setup instructions.

**What you get:**
- ✅ Cloud database hosted by Supabase
- ✅ Real-time multi-user support
- ✅ Automatic backups
- ✅ Production-ready infrastructure

---

### Prerequisites
- Python 3.8+
- Gmail account (for email OTP) - optional, can test without it

### Switching Between Local and Cloud

Update `.env` file:

**Local SQLite:**
```env
USE_LOCAL_DB=true
```

**Supabase Cloud:**
```env
USE_LOCAL_DB=false
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Email Configuration (Optional)

For OTP email delivery, add Gmail credentials to `.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_USE_TLS=True
```

If not configured, OTP testing still works (check terminal output in dev mode).

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/send-otp` - Send OTP
- `POST /api/auth/verify-otp` - Verify OTP and login
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/set-password` - Set password after OTP
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile
- `POST /api/auth/logout` - Logout

### Products
- `GET /api/products/categories` - Get all categories
- `GET /api/products/category/<id>` - Get single category
- `GET /api/products` - List products with pagination
- `GET /api/products/<id>` - Get product details
- `GET /api/products/<id>/reviews` - Get product reviews
- `POST /api/products/<id>/reviews` - Add review
- `POST /api/products/<id>/helpful/<review_id>` - Mark review as helpful
- `GET /api/products/search` - Search products

### Shopping Cart & Orders
- `GET /api/cart` - Get user cart
- `POST /api/cart` - Add to cart
- `PUT /api/cart/<product_id>` - Update cart item
- `DELETE /api/cart/<product_id>` - Remove from cart
- `GET /api/orders` - Get user orders
- `POST /api/orders` - Create order
- `GET /api/orders/<id>` - Get order details
- `POST /api/orders/<id>/cancel` - Cancel order

### Payments
- `POST /api/payment/qr-code` - Generate QR code for UPI payment
- `POST /api/payment/qr-verify` - Verify QR code payment completion

### Support
- `GET /api/support/contact` - Get contact information
- `PUT /api/support/contact` - Update contact info
- `GET /api/support/tickets` - Get user tickets
- `POST /api/support/tickets` - Create support ticket
- `GET /api/support/tickets/<id>` - Get ticket details
- `POST /api/support/tickets/<id>/messages` - Add message to ticket
- `PUT /api/support/tickets/<id>/status` - Update ticket status
- `GET /api/support/faq` - Get FAQ list

## Project Structure

```
3d-printing-ecommerce/
├── app/
│   ├── __init__.py                 # Flask app factory
│   ├── models/
│   │   ├── __init__.py            # Database operations
│   │   └── models.py              # Database models/schemas
│   ├── routes/
│   │   ├── auth.py                # Authentication routes
│   │   ├── products.py            # Product routes
│   │   ├── orders.py              # Orders & cart routes
│   │   └── support.py             # Support routes
│   ├── utils/
│   │   ├── auth.py                # Auth utilities
│   │   ├── payment.py             # Payment utilities
│   │   └── support.py             # Support utilities
│   ├── templates/
│   │   ├── base.html              # Base template
│   │   ├── index.html             # Home page
│   │   └── login.html             # Login page
│   └── static/
│       ├── css/
│       │   └── style.css          # CSS styles
│       └── js/
│           └── main.js            # JavaScript
├── config.py                       # Configuration
├── wsgi.py                         # WSGI entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
└── README.md                       # Documentation
```

## Database Schema

### Tables
- **users**: User accounts
- **categories**: Product categories
- **products**: Products catalog
- **carts**: Shopping cart items
- **orders**: Customer orders
- **order_items**: Items in orders
- **payments**: Payment records
- **reviews**: Product reviews
- **support_tickets**: Support tickets
- **support_messages**: Support messages
- **otps**: OTP records
- **contact_info**: Company contact information

## Security Features

- JWT authentication
- Password hashing with SHA-256
- OTP verification
- HTTPS ready (use with reverse proxy in production)
- CORS enabled for frontend
- Input validation
- Secure session management

## Deployment

### Docker
```bash
docker build -t 3d-printing-store .
docker run -p 5000:5000 3d-printing-store
```

### Supabase Hosting
```bash
# Using Supabase Platform
# Set environment variables in Supabase
# Deploy using Vercel, Netlify, or similar
```

### Production Server
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

## Configuration

### Environment Variables
- `FLASK_ENV`: development/production
- `SECRET_KEY`: Flask secret key
- `DEBUG`: Debug mode (False in production)
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase API key
- `RAZORPAY_KEY_ID`: Razorpay key
- `RAZORPAY_KEY_SECRET`: Razorpay secret
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `MAIL_SERVER`: Email server
- `MAIL_USERNAME`: Email username
- `MAIL_PASSWORD`: Email password

## Testing

### API Testing
```bash
# Using curl
curl http://localhost:5000/api/products

# Using Postman
# Import API endpoints and test
```

### Database Testing
```bash
# Check database connection
curl http://localhost:5000/health
```

## Performance Optimization

- Database indexing on frequently queried fields
- Pagination of large result sets
- Caching of static files
- Lazy loading of images
- Compression of CSS/JS
- CDN ready (for static files)

## Future Enhancements

- [ ] Admin panel for product management
- [ ] Order analytics and reporting
- [ ] Email newsletter system
- [ ] Wishlist feature
- [ ] Referral program
- [ ] Discount codes
- [ ] Multiple language support
- [ ] Mobile app (iOS/Android)
- [ ] Advanced search with filters
- [ ] Product recommendations
- [ ] Customer loyalty program
- [ ] Video product demonstrations
- [ ] Live chat support
- [ ] Inventory management
- [ ] Multi-warehouse support

## Troubleshooting

### Database Connection Issues
- Verify Supabase credentials in `.env`
- Check network connectivity
- Ensure Supabase project is running

### Email Not Sending
- Enable "Less secure app access" for Gmail
- Use app-specific passwords
- Check SMTP settings

### OTP Not Received
- Verify Twilio credentials
- Check phone number format
- Ensure enough Twilio credits

### Payment Issues
- Verify Razorpay API keys
- Check payment gateway configuration
- Enable test mode for development

## Support

For support:
- Email: support@3dprintingstore.com
- WhatsApp: +91-9876543210
- Create a support ticket in the application

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Changelog

### Version 1.0.0 - Initial Release
- User authentication (OTP & Email)
- Product listing and details
- Shopping cart
- Multiple payment methods
- Customer support system
- Email and WhatsApp integration

---

**Last Updated**: April 2024
**Version**: 1.0.0
