"""
Customer Support utilities for email and ticketing
"""
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
from config import get_config
from app.models import DatabaseOperations, Database, SYSTEM_CONTACT_INFO

config = get_config()

class SupportManager:
    """Manage customer support tickets and messages"""
    
    @staticmethod
    def generate_ticket_number() -> str:
        """Generate unique ticket number"""
        return f"TICKET-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    @staticmethod
    def create_support_ticket(user_id: str, subject: str, message: str, 
                             category: str = 'general', priority: str = 'normal',
                             contact_method: str = 'email') -> tuple[bool, dict]:
        """Create new support ticket"""
        try:
            ticket_data = {
                'user_id': user_id,
                'ticket_number': SupportManager.generate_ticket_number(),
                'subject': subject,
                'message': message,
                'category': category,
                'priority': priority,
                'contact_method': contact_method,
                'status': 'open',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = DatabaseOperations.insert('support_tickets', ticket_data)
            ticket = result[0] if result else None
            
            return (True, ticket) if ticket else (False, {'error': 'Failed to create ticket'})
        
        except Exception as e:
            print(f"Error creating support ticket: {str(e)}")
            return False, {'error': str(e)}
    
    @staticmethod
    def add_support_message(ticket_id: str, sender_id: str, message: str, attachments: list = None) -> bool:
        """Add message to support ticket"""
        try:
            message_data = {
                'ticket_id': ticket_id,
                'sender_id': sender_id,
                'message': message,
                'attachments': attachments,
                'created_at': datetime.now().isoformat()
            }
            
            DatabaseOperations.insert('support_messages', message_data)
            
            # Update ticket's updated_at
            DatabaseOperations.update('support_tickets', {
                'updated_at': datetime.now().isoformat()
            }, {'id': ticket_id})
            
            return True
        
        except Exception as e:
            print(f"Error adding message: {str(e)}")
            return False
    
    @staticmethod
    def get_ticket_details(ticket_id: str) -> dict:
        """Get ticket with all messages"""
        try:
            db = Database.get_client()
            
            result = db.table('support_tickets').select('*, support_messages(*)').eq('id', ticket_id).execute()
            return result.data[0] if result.data else None
        
        except Exception as e:
            print(f"Error getting ticket: {str(e)}")
            return None
    
    @staticmethod
    def update_ticket_status(ticket_id: str, status: str) -> bool:
        """Update ticket status"""
        try:
            DatabaseOperations.update('support_tickets', {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }, {'id': ticket_id})
            return True
        
        except Exception as e:
            print(f"Error updating ticket: {str(e)}")
            return False
    
    @staticmethod
    def get_user_tickets(user_id: str) -> list:
        """Get all tickets for a user"""
        try:
            db = Database.get_client()
            result = db.table('support_tickets').select('*, support_messages(*)').eq('user_id', user_id).order('created_at', desc=True).execute()
            return result.data or []
        
        except Exception as e:
            print(f"Error getting user tickets: {str(e)}")
            return []


class EmailService:
    """Email service for notifications and support"""
    
    @staticmethod
    def send_email(to_email: str, subject: str, html_body: str) -> bool:
        """Send email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = config.MAIL_USERNAME
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(html_body, 'html'))
            
            server = smtplib.SMTP(config.MAIL_SERVER, config.MAIL_PORT)
            server.starttls()
            server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True
        
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    @staticmethod
    def send_order_confirmation(user_email: str, user_name: str, order_number: str, total_amount: float) -> bool:
        """Send order confirmation email"""
        html_body = f"""
        <html>
            <body>
                <h2>Order Confirmation</h2>
                <p>Dear {user_name},</p>
                <p>Thank you for your order! Your order has been received and is being processed.</p>
                <p><strong>Order Number:</strong> {order_number}</p>
                <p><strong>Total Amount:</strong> ₹{total_amount:.2f}</p>
                <p>You will receive another email with tracking information once your order ships.</p>
                <p>If you have any questions, please don't hesitate to contact us.</p>
                <p>Best regards,<br>3D Printing Store Team</p>
            </body>
        </html>
        """
        return EmailService.send_email(user_email, 'Order Confirmation', html_body)
    
    @staticmethod
    def send_support_email(user_email: str, user_name: str, ticket_number: str, subject: str) -> bool:
        """Send support ticket confirmation email"""
        html_body = f"""
        <html>
            <body>
                <h2>Support Ticket Created</h2>
                <p>Dear {user_name},</p>
                <p>We have received your support request. Our team will respond shortly.</p>
                <p><strong>Ticket Number:</strong> {ticket_number}</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p>You can check your ticket status anytime by logging into your account.</p>
                <p>Best regards,<br>3D Printing Store Support Team</p>
            </body>
        </html>
        """
        return EmailService.send_email(user_email, f'Support Ticket - {ticket_number}', html_body)

    @staticmethod
    def send_support_notification(user_name: str, user_email: str, ticket_number: str, subject: str, message: str, category: str, priority: str, contact_method: str) -> bool:
        """Send internal support notification to the configured inbox."""
        inbox = config.MAIL_USERNAME
        if not inbox:
            print('! Support notification skipped: MAIL_USERNAME is not configured')
            return False

        html_body = f"""
        <html>
            <body>
                <h2>New Support Ticket Received</h2>
                <p><strong>Ticket Number:</strong> {ticket_number}</p>
                <p><strong>Name:</strong> {user_name}</p>
                <p><strong>User Email:</strong> {user_email}</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p><strong>Category:</strong> {category}</p>
                <p><strong>Priority:</strong> {priority}</p>
                <p><strong>Preferred Contact:</strong> {contact_method}</p>
                <p><strong>Message:</strong></p>
                <div style="white-space: pre-wrap; border: 1px solid #ddd; padding: 12px; border-radius: 8px;">{message}</div>
            </body>
        </html>
        """

        return EmailService.send_email(
            inbox,
            f'New Support Ticket - {ticket_number}',
            html_body
        )

    @staticmethod
    def send_order_notification(order_number: str, user_name: str, user_email: str, total_amount: float, payment_method: str, shipping_address: dict = None) -> bool:
        """Send internal order notification to the configured inbox."""
        inbox = config.MAIL_USERNAME
        if not inbox:
            print('! Order notification skipped: MAIL_USERNAME is not configured')
            return False

        shipping_address = shipping_address or {}
        shipping_summary = ', '.join(filter(None, [
            shipping_address.get('address_line'),
            shipping_address.get('city'),
            shipping_address.get('state'),
            shipping_address.get('postal_code'),
            shipping_address.get('country')
        ])) or 'Not provided'

        html_body = f"""
        <html>
            <body>
                <h2>New Order Received</h2>
                <p><strong>Order Number:</strong> {order_number}</p>
                <p><strong>Customer Name:</strong> {user_name}</p>
                <p><strong>Customer Email:</strong> {user_email}</p>
                <p><strong>Total Amount:</strong> Rs.{total_amount:.2f}</p>
                <p><strong>Payment Method:</strong> {payment_method}</p>
                <p><strong>Shipping Address:</strong> {shipping_summary}</p>
            </body>
        </html>
        """

        return EmailService.send_email(
            inbox,
            f'New Order - {order_number}',
            html_body
        )


class ContactManager:
    """Manage contact information"""
    
    @staticmethod
    def get_contact_info() -> dict:
        """Get company contact information"""
        try:
            contact_info = DatabaseOperations.select_one('contact_info', {})
            return contact_info or SYSTEM_CONTACT_INFO
        
        except Exception as e:
            return SYSTEM_CONTACT_INFO
    
    @staticmethod
    def update_contact_info(data: dict) -> bool:
        """Update contact information"""
        try:
            # Get existing contact info
            existing = DatabaseOperations.select_one('contact_info', {})
            
            if existing:
                data['updated_at'] = datetime.now().isoformat()
                DatabaseOperations.update('contact_info', data, {'id': existing['id']})
            else:
                data['updated_at'] = datetime.now().isoformat()
                DatabaseOperations.insert('contact_info', data)
            
            return True
        
        except Exception as e:
            print(f"Error updating contact info: {str(e)}")
            return False
    
    @staticmethod
    def create_default_contact_info() -> bool:
        """Create default contact information"""
        try:
            default_data = {
                'email': 'support@3dprintingstore.com',
                'phone': '+91-1234567890',
                'whatsapp': '+91-9876543210',
                'address': '123 Innovation Street',
                'city': 'Your City',
                'state': 'Your State',
                'country': 'India',
                'postal_code': '000000',
                'business_hours': {
                    'monday_to_friday': '9:00 AM - 6:00 PM',
                    'saturday': '10:00 AM - 4:00 PM',
                    'sunday': 'Closed'
                }
            }
            
            return ContactManager.update_contact_info(default_data)
        
        except Exception as e:
            print(f"Error creating default contact info: {str(e)}")
            return False
