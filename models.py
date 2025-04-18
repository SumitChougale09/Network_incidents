from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import uuid
from sqlalchemy.sql import func
from extentions import db 
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='support_engineer')  # admin or support_engineer
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    team = db.relationship('Team', backref=db.backref('members', lazy='dynamic'))
    incidents_reported = db.relationship('Incident', backref='reporter', foreign_keys='Incident.reporter_id')
    incidents_assigned = db.relationship('Incident', backref='assignee', foreign_keys='Incident.assignee_id')
    updates = db.relationship('IncidentUpdate', backref='user')
    
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
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_user_by_username(username):
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_email(email):
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def create_user(username, email, password, role='support_engineer'):
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user


class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    incidents = db.relationship('Incident', backref='team')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_team_by_id(team_id):
        return Team.query.get(team_id)
    
    @staticmethod
    def create_team(name, description=None):
        team = Team(name=name, description=description)
        db.session.add(team)
        db.session.commit()
        return team
    
    @staticmethod
    def get_all_teams():
        return Team.query.all()


class Incident(db.Model):
    __tablename__ = 'incidents'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    status = db.Column(db.String(20), default='open')  # 'open', 'assigned', 'in_progress', 'resolved', 'closed'
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    updates = db.relationship('IncidentUpdate', backref='incident', cascade='all, delete-orphan')
    
    def assign(self, team_id, assignee_id=None):
        self.team_id = team_id
        self.assignee_id = assignee_id
        self.status = 'assigned'
        self.updated_at = datetime.datetime.now()
        db.session.commit()
        
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
        
        db.session.commit()
        
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }
    
    @staticmethod
    def get_incident_by_id(incident_id):
        return Incident.query.get(incident_id)
    
    @staticmethod
    def create_incident(title, description, severity, reporter_id):
        incident_id = str(uuid.uuid4())
        incident = Incident(
            id=incident_id,
            title=title,
            description=description,
            severity=severity,
            reporter_id=reporter_id
        )
        db.session.add(incident)
        db.session.commit()
        
        # Create activity log
        log_activity('incident_created', f"New incident created: {title}")
        
        return incident
    
    @staticmethod
    def get_all_incidents():
        return Incident.query.all()
    
    @staticmethod
    def get_incidents_by_status(status):
        return Incident.query.filter_by(status=status).all()
    
    @staticmethod
    def get_incidents_by_severity(severity):
        return Incident.query.filter_by(severity=severity).all()
    
    @staticmethod
    def get_incidents_by_team(team_id):
        return Incident.query.filter_by(team_id=team_id).all()
    
    @staticmethod
    def get_incidents_by_assignee(assignee_id):
        return Incident.query.filter_by(assignee_id=assignee_id).all()


class IncidentUpdate(db.Model):
    __tablename__ = 'incident_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.String(36), db.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def create_update(incident_id, user_id, content):
        update = IncidentUpdate(
            incident_id=incident_id,
            user_id=user_id,
            content=content
        )
        db.session.add(update)
        db.session.commit()
        
        # Create activity log
        log_activity('incident_update', f"Update added to incident #{incident_id}")
        
        return update
    
    @staticmethod
    def get_updates_for_incident(incident_id):
        return IncidentUpdate.query.filter_by(incident_id=incident_id).order_by(IncidentUpdate.created_at).all()


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(256), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=func.now())
    
    # Relationship
    user = db.relationship('User', backref=db.backref('activities', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'action_type': self.action_type,
            'description': self.description,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


def log_activity(action_type, description, user_id=None):
    activity = ActivityLog(
        action_type=action_type,
        description=description,
        user_id=user_id
    )
    db.session.add(activity)
    db.session.commit()
    return activity


def get_recent_activities(limit=20):
    return ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()


def get_incident_stats():
    total = Incident.query.count()
    open_incidents = Incident.query.filter_by(status='open').count()
    assigned_incidents = Incident.query.filter_by(status='assigned').count()
    in_progress_incidents = Incident.query.filter_by(status='in_progress').count()
    resolved_incidents = Incident.query.filter_by(status='resolved').count()
    closed_incidents = Incident.query.filter_by(status='closed').count()
    
    critical = Incident.query.filter_by(severity='critical').count()
    high = Incident.query.filter_by(severity='high').count()
    medium = Incident.query.filter_by(severity='medium').count()
    low = Incident.query.filter_by(severity='low').count()
    
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
    """Initialize sample data for the database if empty"""
    # Create teams
    if Team.query.count() == 0:
        Team.create_team("Network Operations", "Handles network infrastructure issues")
        Team.create_team("Security Operations", "Handles security incidents")
        Team.create_team("Application Support", "Handles application-related issues")
    
    # Create admin user if none exists
    if User.query.filter_by(role='admin').count() == 0:
        User.create_user("admin", "admin@example.com", "admin123", "admin")
        
    # Create a support engineer if none exists
    if User.query.filter_by(role='support_engineer').count() == 0:
        user = User.create_user("support", "support@example.com", "support123", "support_engineer")
        # Assign to a team
        team = Team.query.first()
        if team:
            user.team_id = team.id
            db.session.commit()
    
    # Generate sample incidents if we have fewer than 5
    if Incident.query.count() < 5:
        generate_sample_incidents(15)  # Generate 15 sample incidents
        
def generate_sample_incidents(num_incidents=15):
    """Generate sample incidents with realistic timestamps, severities, and progression"""
    import datetime
    import random
    import uuid
    
    print(f"Generating {num_incidents} sample incidents...")
    
    # Get existing users and teams from the database
    users = User.query.all()
    teams = Team.query.all()
    
    if not users or not teams:
        print("Error: No users or teams found in the database.")
        return
    
    # Use admin user as a fallback reporter
    admin_user = User.query.filter_by(username='admin').first()
    reporter_id = admin_user.id if admin_user else users[0].id
    
    # Get the current date for relative timestamps
    current_date = datetime.datetime.now()
    
    # Generate incidents starting from three months ago
    start_date = current_date - datetime.timedelta(days=90)
    
    # Sample incident titles and descriptions
    incident_titles = [
        "Network outage in Building A",
        "Website loading slow for external users",
        "Email server not responding",
        "Authentication service failure",
        "Database connection timeout",
        "Load balancer failover issue",
        "CDN cache purge failure",
        "API rate limiting errors",
        "VPN connection drops",
        "Firewall blocking legitimate traffic",
        "High CPU usage on application servers",
        "Memory leak in microservice",
        "Storage capacity reached critical threshold",
        "SSL certificate expiration",
        "DNS resolution failures"
    ]
    
    incident_descriptions = [
        "Users are unable to access the service. All attempts result in connection timeout errors.",
        "The system is experiencing high latency. Response times are exceeding 5 seconds.",
        "Multiple customers reported inability to log in due to authentication failures.",
        "Automated monitoring detected service degradation. Investigation in progress.",
        "The issue appears to be affecting all users in the EU region only.",
        "Database queries are taking longer than usual, causing cascading timeouts.",
        "The third-party API integration is failing intermittently with 503 errors.",
        "Memory usage is increasing steadily, pointing to a potential memory leak.",
        "Network traffic analysis shows unusual patterns consistent with a DDoS attack.",
        "The failover mechanism did not trigger automatically, requiring manual intervention."
    ]
    
    # Sample update messages
    update_messages = [
        "Initial investigation started. Looking into the root cause.",
        "Identified that the issue is related to recent configuration changes.",
        "Restarted the affected services. Monitoring the situation.",
        "Root cause appears to be network connectivity between services.",
        "Applied temporary workaround. Permanent fix in progress.",
        "Rolled back recent deployment that was causing issues.",
        "Escalated to database team for further investigation.",
        "Scaling up resources to handle increased load.",
        "Implemented rate limiting to prevent cascading failures.",
        "Issue resolved. Services running normally again."
    ]
    
    # Severity and status distributions (weighted for realism)
    severity_options = ["critical", "high", "medium", "low"]
    severity_weights = [0.1, 0.25, 0.4, 0.25]  # 10% critical, 25% high, 40% medium, 25% low
    
    status_options = ["open", "assigned", "in_progress", "resolved", "closed"]
    
    for i in range(num_incidents):
        # Generate a unique incident ID
        incident_id = str(uuid.uuid4())
        
        # Randomly select a title and description
        title = random.choice(incident_titles)
        description = random.choice(incident_descriptions)
        
        # Choose severity based on weighted distribution
        severity = random.choices(
            severity_options,
            weights=severity_weights,
            k=1
        )[0]
        
        # Randomly assign a creation date within the past three months
        days_ago = random.randint(0, 90)
        created_at = current_date - datetime.timedelta(days=days_ago)
        
        # Create the incident
        incident = Incident(
            id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status="open",  # Initial status is always open
            reporter_id=reporter_id,
            created_at=created_at,
            updated_at=created_at
        )
        
        db.session.add(incident)
        db.session.flush()  # Flush without committing
        
        # Log the incident creation
        log_activity("incident_created", f"Incident '{title}' created with {severity} severity", reporter_id)
        
        # Randomly determine the final status based on age (older incidents more likely to be resolved)
        if days_ago > 60:  # Very old incidents
            status_weights = [0.05, 0.05, 0.1, 0.3, 0.5]  # Mostly closed
        elif days_ago > 30:  # Old incidents
            status_weights = [0.1, 0.1, 0.2, 0.4, 0.2]  # Mostly resolved
        elif days_ago > 14:  # Recent incidents
            status_weights = [0.2, 0.2, 0.4, 0.15, 0.05]  # Mostly in progress
        else:  # Very recent incidents
            status_weights = [0.4, 0.3, 0.2, 0.1, 0.0]  # Mostly open or assigned
        
        target_status_idx = random.choices(
            range(len(status_options)),
            weights=status_weights,
            k=1
        )[0]
        
        # Process the incident through its determined progression
        current_time = created_at
        
        # Add random updates as the incident progresses
        num_updates = random.randint(0, 3)  # Between 0 and 3 updates
        
        for status_idx in range(1, target_status_idx + 1):
            # Add some time since the last update
            hours_delta = random.randint(4, 48)  # Between 4 and 48 hours
            current_time += datetime.timedelta(hours=hours_delta)
            
            # Don't go beyond current date
            if current_time > current_date:
                current_time = current_date
            
            new_status = status_options[status_idx]
            
            # Assign to a team and/or user when transitioning to assigned
            if new_status == "assigned":
                team = random.choice(teams)
                assignees = User.query.filter_by(team_id=team.id).all()
                assignee = random.choice(assignees) if assignees else None
                
                if assignee:
                    incident.team_id = team.id
                    incident.assignee_id = assignee.id
                    log_activity("incident_assigned", 
                                f"Incident assigned to {assignee.username} from {team.name} team", 
                                admin_user.id)
            
            # Set resolved_at timestamp when status becomes resolved
            if new_status == "resolved":
                incident.resolved_at = current_time
                log_activity("incident_resolved", 
                            f"Incident was resolved after {(current_time - created_at).days} days", 
                            incident.assignee_id or admin_user.id)
            
            # Set closed_at timestamp when status becomes closed
            if new_status == "closed":
                incident.closed_at = current_time
                log_activity("incident_closed", 
                            "Incident was closed", 
                            incident.assignee_id or admin_user.id)
                
            incident.status = new_status
            incident.updated_at = current_time
            
            # Add an update message
            if random.random() < 0.7:  # 70% chance of adding an update
                update_content = random.choice(update_messages)
                update_author = incident.assignee_id if incident.assignee_id else reporter_id
                
                incident_update = IncidentUpdate(
                    incident_id=incident_id,
                    user_id=update_author,
                    content=update_content,
                    created_at=current_time
                )
                
                db.session.add(incident_update)
    
    # Commit all changes to the database
    db.session.commit()
    
    print("Sample incident generation complete.")
