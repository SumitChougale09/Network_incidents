"""
Notification system for the Network Incident Management System
Provides real-time notifications for critical incidents, status changes, and assignments
"""

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
import datetime
from models import db, User, Incident, ActivityLog, log_activity

notif_bp = Blueprint('notifications', __name__)

class Notification:
    """Notification model for storing user notifications"""
    def __init__(self, user_id, incident_id, message, type, timestamp=None):
        self.user_id = user_id
        self.incident_id = incident_id  # Can be None for system notifications
        self.message = message
        self.type = type  # 'critical', 'assignment', 'update', 'system'
        self.timestamp = timestamp or datetime.datetime.now()
        self.read = False
        
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'incident_id': self.incident_id,
            'message': self.message,
            'type': self.type,
            'timestamp': self.timestamp.isoformat(),
            'read': self.read
        }

# In-memory notification storage (would be replaced with database in production)
user_notifications = {}  # user_id -> list of notifications

def create_notification(user_id, message, incident_id=None, type='update'):
    """Create a notification for a user"""
    if user_id not in user_notifications:
        user_notifications[user_id] = []
        
    notification = Notification(user_id, incident_id, message, type)
    user_notifications[user_id].insert(0, notification)  # Add to beginning of list
    
    # Keep only the latest 50 notifications
    if len(user_notifications[user_id]) > 50:
        user_notifications[user_id] = user_notifications[user_id][:50]
        
    return notification

def get_user_notifications(user_id, unread_only=False, limit=10):
    """Get notifications for a user"""
    if user_id not in user_notifications:
        return []
        
    if unread_only:
        return [n for n in user_notifications[user_id] if not n.read][:limit]
    else:
        return user_notifications[user_id][:limit]
    
def mark_notification_read(user_id, timestamp):
    """Mark a notification as read"""
    if user_id not in user_notifications:
        return False
        
    for notification in user_notifications[user_id]:
        if notification.timestamp.isoformat() == timestamp:
            notification.read = True
            return True
            
    return False
    
def mark_all_read(user_id):
    """Mark all notifications as read for a user"""
    if user_id not in user_notifications:
        return 0
        
    count = 0
    for notification in user_notifications[user_id]:
        if not notification.read:
            notification.read = True
            count += 1
            
    return count

def notify_critical_incident(incident):
    """Notify all users about a critical incident"""
    if incident.severity != 'critical':
        return
        
    message = f"CRITICAL INCIDENT: {incident.title}"
    
    # Notify all users about critical incidents
    all_users = User.query.all()
    for user in all_users:
        create_notification(user.id, message, incident.id, 'critical')
        
    # Log the notification
    log_activity("critical_notification", f"Critical incident notification sent to all users for incident {incident.id}")
    
def notify_incident_assignment(incident, assignee_id):
    """Notify a user that they have been assigned to an incident"""
    user = User.query.get(assignee_id)
    if not user:
        return
        
    message = f"You have been assigned to incident: {incident.title}"
    create_notification(assignee_id, message, incident.id, 'assignment')
    
    # Log the notification
    log_activity("assignment_notification", f"Assignment notification sent to {user.username} for incident {incident.id}")
    
def notify_incident_update(incident, update_content, exclude_user_id=None):
    """Notify relevant users about an incident update"""
    # Determine which users should be notified
    users_to_notify = set()
    
    # Always notify the reporter
    if incident.reporter_id:
        users_to_notify.add(incident.reporter_id)
        
    # Always notify the assignee
    if incident.assignee_id:
        users_to_notify.add(incident.assignee_id)
        
    # Notify team members if a team is assigned
    if incident.team_id:
        team_members = User.query.filter_by(team_id=incident.team_id).all()
        for user in team_members:
            users_to_notify.add(user.id)
            
    # Don't notify the user who made the update
    if exclude_user_id and exclude_user_id in users_to_notify:
        users_to_notify.remove(exclude_user_id)
        
    # Create the notification
    message = f"Update on incident {incident.title}: {update_content[:50]}..."
    
    for user_id in users_to_notify:
        create_notification(user_id, message, incident.id, 'update')
        
    # Log the notification
    log_activity("update_notification", f"Update notification sent to {len(users_to_notify)} users for incident {incident.id}")

# API endpoints for notifications
@notif_bp.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get notifications for the current user"""
    unread_only = request.args.get('unread', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 10))
    
    notifications = get_user_notifications(current_user.id, unread_only, limit)
    return jsonify({
        'success': True,
        'unread_count': len([n for n in notifications if not n.read]),
        'notifications': [n.to_dict() for n in notifications]
    })
    
@notif_bp.route('/api/notifications/read', methods=['POST'])
@login_required
def mark_read():
    """Mark a notification as read"""
    data = request.json
    timestamp = data.get('timestamp')
    
    if timestamp:
        success = mark_notification_read(current_user.id, timestamp)
        return jsonify({'success': success})
    else:
        return jsonify({'success': False, 'error': 'No timestamp provided'})
        
@notif_bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read_endpoint():
    """Mark all notifications as read"""
    count = mark_all_read(current_user.id)
    return jsonify({'success': True, 'count': count})
    
@notif_bp.route('/notifications')
@login_required
def notifications_page():
    """Notifications page"""
    notifications = get_user_notifications(current_user.id, unread_only=False, limit=50)
    return render_template('notifications.html', notifications=notifications)