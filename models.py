from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import random
import uuid

# In-memory data storage
users = {}
incidents = {}
teams = {}
updates = {}
activity_logs = []

class User(UserMixin):
    def __init__(self, id, username, email, password=None, role='support_engineer'):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password) if password else None
        self.role = role  # admin or support_engineer
        self.team_id = None
        self.created_at = datetime.datetime.now()
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'team_id': self.team_id,
            'created_at': self.created_at.isoformat()
        }
    
    @staticmethod
    def get_user_by_id(user_id):
        return users.get(user_id)
    
    @staticmethod
    def get_user_by_username(username):
        for user in users.values():
            if user.username == username:
                return user
        return None
    
    @staticmethod
    def get_user_by_email(email):
        for user in users.values():
            if user.email == email:
                return user
        return None
    
    @staticmethod
    def create_user(username, email, password, role='support_engineer'):
        user_id = max(users.keys(), default=0) + 1
        user = User(user_id, username, email, password, role)
        users[user_id] = user
        return user


class Team:
    def __init__(self, id, name, description=None):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = datetime.datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }
    
    @staticmethod
    def get_team_by_id(team_id):
        return teams.get(team_id)
    
    @staticmethod
    def create_team(name, description=None):
        team_id = max(teams.keys(), default=0) + 1
        team = Team(team_id, name, description)
        teams[team_id] = team
        return team
    
    @staticmethod
    def get_all_teams():
        return list(teams.values())


class Incident:
    def __init__(self, id, title, description, severity, reporter_id, status='open'):
        self.id = id
        self.title = title
        self.description = description
        self.severity = severity  # 'low', 'medium', 'high', 'critical'
        self.reporter_id = reporter_id
        self.status = status  # 'open', 'assigned', 'in_progress', 'resolved', 'closed'
        self.assignee_id = None
        self.team_id = None
        self.created_at = datetime.datetime.now()
        self.updated_at = self.created_at
        self.resolved_at = None
        self.closed_at = None
    
    def assign(self, team_id, assignee_id=None):
        self.team_id = team_id
        self.assignee_id = assignee_id
        self.status = 'assigned'
        self.updated_at = datetime.datetime.now()
        
        # Create activity log
        log_activity('incident_assigned', f"Incident #{self.id} assigned to team #{team_id}")
    
    def set_status(self, status):
        old_status = self.status
        self.status = status
        self.updated_at = datetime.datetime.now()
        
        if status == 'resolved' and old_status != 'resolved':
            self.resolved_at = datetime.datetime.now()
        elif status == 'closed' and old_status != 'closed':
            self.closed_at = datetime.datetime.now()
        
        # Create activity log
        log_activity('status_update', f"Incident #{self.id} status changed from {old_status} to {status}")
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'reporter_id': self.reporter_id,
            'status': self.status,
            'assignee_id': self.assignee_id,
            'team_id': self.team_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }
    
    @staticmethod
    def get_incident_by_id(incident_id):
        return incidents.get(incident_id)
    
    @staticmethod
    def create_incident(title, description, severity, reporter_id):
        incident_id = str(uuid.uuid4())
        incident = Incident(incident_id, title, description, severity, reporter_id)
        incidents[incident_id] = incident
        
        # Create activity log
        log_activity('incident_created', f"New incident created: {title}")
        
        return incident
    
    @staticmethod
    def get_all_incidents():
        return list(incidents.values())
    
    @staticmethod
    def get_incidents_by_status(status):
        return [inc for inc in incidents.values() if inc.status == status]
    
    @staticmethod
    def get_incidents_by_severity(severity):
        return [inc for inc in incidents.values() if inc.severity == severity]
    
    @staticmethod
    def get_incidents_by_team(team_id):
        return [inc for inc in incidents.values() if inc.team_id == team_id]
    
    @staticmethod
    def get_incidents_by_assignee(assignee_id):
        return [inc for inc in incidents.values() if inc.assignee_id == assignee_id]


class IncidentUpdate:
    def __init__(self, id, incident_id, user_id, content):
        self.id = id
        self.incident_id = incident_id
        self.user_id = user_id
        self.content = content
        self.created_at = datetime.datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }
    
    @staticmethod
    def create_update(incident_id, user_id, content):
        update_id = max(updates.keys(), default=0) + 1
        update = IncidentUpdate(update_id, incident_id, user_id, content)
        
        if incident_id not in updates:
            updates[incident_id] = []
        
        updates[incident_id].append(update)
        
        # Create activity log
        log_activity('incident_update', f"Update added to incident #{incident_id}")
        
        return update
    
    @staticmethod
    def get_updates_for_incident(incident_id):
        return updates.get(incident_id, [])


def log_activity(action_type, description, user_id=None):
    activity = {
        'id': len(activity_logs) + 1,
        'action_type': action_type,
        'description': description,
        'user_id': user_id,
        'timestamp': datetime.datetime.now()
    }
    activity_logs.append(activity)
    return activity


def get_recent_activities(limit=20):
    return sorted(activity_logs, key=lambda x: x['timestamp'], reverse=True)[:limit]


def get_incident_stats():
    total = len(incidents)
    open_incidents = len(Incident.get_incidents_by_status('open'))
    assigned_incidents = len(Incident.get_incidents_by_status('assigned'))
    in_progress_incidents = len(Incident.get_incidents_by_status('in_progress'))
    resolved_incidents = len(Incident.get_incidents_by_status('resolved'))
    closed_incidents = len(Incident.get_incidents_by_status('closed'))
    
    critical = len(Incident.get_incidents_by_severity('critical'))
    high = len(Incident.get_incidents_by_severity('high'))
    medium = len(Incident.get_incidents_by_severity('medium'))
    low = len(Incident.get_incidents_by_severity('low'))
    
    return {
        'total': total,
        'by_status': {
            'open': open_incidents,
            'assigned': assigned_incidents,
            'in_progress': in_progress_incidents,
            'resolved': resolved_incidents,
            'closed': closed_incidents
        },
        'by_severity': {
            'critical': critical,
            'high': high,
            'medium': medium,
            'low': low
        }
    }


def init_data():
    """Initialize sample data for the in-memory storage"""
    # Create teams
    if not teams:
        Team.create_team("Network Operations", "Handles network infrastructure issues")
        Team.create_team("Security Operations", "Handles security incidents")
        Team.create_team("Application Support", "Handles application-related issues")
    
    # Create admin user if none exists
    if not any(user.role == 'admin' for user in users.values()):
        User.create_user("admin", "admin@example.com", "admin123", "admin")
