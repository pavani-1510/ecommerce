"""
Customer Support Routes
"""
from flask import Blueprint, request, jsonify, g
from app.models import Database, DatabaseOperations
from app.utils.auth import login_required, admin_required
from app.utils.support import SupportManager, EmailService, ContactManager
from datetime import datetime

support_bp = Blueprint('support', __name__, url_prefix='/api/support')

@support_bp.route('/contact', methods=['GET'])
def get_contact_info():
    """Get contact information"""
    try:
        contact_info = ContactManager.get_contact_info()
        
        return jsonify({'contact_info': contact_info}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@support_bp.route('/contact', methods=['PUT'])
@login_required
@admin_required
def update_contact_info():
    """Update contact information (Admin only)"""
    try:
        data = request.get_json() or {}
        
        success = ContactManager.update_contact_info(data)
        
        if not success:
            return jsonify({'error': 'Failed to update contact info'}), 500
        
        return jsonify({'message': 'Contact information updated'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@support_bp.route('/tickets', methods=['GET'])
@login_required
def list_tickets():
    """Get user support tickets"""
    try:
        tickets = SupportManager.get_user_tickets(g.user_id)
        
        return jsonify({
            'tickets': tickets,
            'total': len(tickets)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@support_bp.route('/admin/tickets', methods=['GET'])
@login_required
@admin_required
def list_all_tickets_admin():
    """Get all support tickets for admin dashboard"""
    try:
        db = Database.get_client()
        result = db.table('support_tickets').select('*').order('created_at', desc=True).execute()
        tickets = result.data or []

        for ticket in tickets:
            user_info = DatabaseOperations.select_one('users', {'id': ticket.get('user_id')}) if ticket.get('user_id') else None
            ticket['user_email'] = user_info.get('email') if user_info else ''
            ticket['user_name'] = user_info.get('full_name') if user_info else ''

        return jsonify({
            'tickets': tickets,
            'total': len(tickets)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@support_bp.route('/tickets', methods=['POST'])
@login_required
def create_ticket():
    """Create support ticket"""
    try:
        data = request.get_json()
        
        subject = data.get('subject')
        message = data.get('message')
        category = data.get('category', 'general')
        priority = data.get('priority', 'normal')
        contact_method = data.get('contact_method', 'email')
        
        if not subject or not message:
            return jsonify({'error': 'Subject and message are required'}), 400
        
        success, ticket = SupportManager.create_support_ticket(
            g.user_id, subject, message, category, priority, contact_method
        )
        
        if not success:
            return jsonify(ticket), 500
        
        # Send confirmation email to the user
        user_email = g.user.get('email')
        user_name = g.user.get('full_name', 'Customer')
        EmailService.send_support_email(user_email, user_name, ticket['ticket_number'], subject)

        # Send an internal notification to your Gmail inbox
        EmailService.send_support_notification(
            user_name=user_name,
            user_email=user_email,
            ticket_number=ticket['ticket_number'],
            subject=subject,
            message=message,
            category=category,
            priority=priority,
            contact_method=contact_method
        )
        
        return jsonify({
            'message': 'Ticket created successfully',
            'ticket': ticket
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@support_bp.route('/tickets/<ticket_id>', methods=['GET'])
@login_required
def get_ticket(ticket_id):
    """Get ticket details"""
    try:
        ticket = SupportManager.get_ticket_details(ticket_id)
        
        if not ticket or ticket['user_id'] != g.user_id:
            return jsonify({'error': 'Ticket not found'}), 404
        
        return jsonify({'ticket': ticket}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@support_bp.route('/tickets/<ticket_id>/messages', methods=['POST'])
@login_required
def add_ticket_message(ticket_id):
    """Add message to support ticket"""
    try:
        ticket = SupportManager.get_ticket_details(ticket_id)
        
        if not ticket or ticket['user_id'] != g.user_id:
            return jsonify({'error': 'Ticket not found'}), 404
        
        data = request.get_json()
        message = data.get('message')
        attachments = data.get('attachments')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        success = SupportManager.add_support_message(
            ticket_id, g.user_id, message, attachments
        )
        
        if not success:
            return jsonify({'error': 'Failed to add message'}), 500
        
        return jsonify({'message': 'Message added successfully'}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@support_bp.route('/tickets/<ticket_id>/status', methods=['PUT'])
@login_required
@admin_required
def update_ticket_status(ticket_id):
    """Update ticket status (Admin only)"""
    try:
        data = request.get_json() or {}
        status = data.get('status')
        
        if status not in ['open', 'in_progress', 'resolved', 'closed']:
            return jsonify({'error': 'Invalid status'}), 400
        
        success = SupportManager.update_ticket_status(ticket_id, status)
        
        if not success:
            return jsonify({'error': 'Failed to update ticket'}), 500
        
        return jsonify({'message': 'Ticket status updated'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@support_bp.route('/faq', methods=['GET'])
def get_faq():
    """Get FAQ list"""
    try:
        # Placeholder FAQ data
        faq_data = [
            {
                'id': '1',
                'question': 'What is the delivery time?',
                'answer': 'Standard delivery takes 3-5 business days. Express delivery is available for 1-2 business days.'
            },
            {
                'id': '2',
                'question': 'Do you offer returns?',
                'answer': 'Yes, we accept returns within 7 days of purchase. Items must be in original condition.'
            },
            {
                'id': '3',
                'question': 'What payment methods do you accept?',
                'answer': 'We accept QR Code (UPI) and Cash on Delivery payment methods.'
            },
            {
                'id': '4',
                'question': 'How do I track my order?',
                'answer': 'You can track your order in your account dashboard or via the tracking link sent in your order confirmation email.'
            },
            {
                'id': '5',
                'question': 'Can I cancel my order?',
                'answer': 'Orders can be cancelled within 24 hours of placement. After that, contact our support team.'
            }
        ]
        
        return jsonify({
            'faq': faq_data,
            'total': len(faq_data)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


