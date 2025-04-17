from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import uuid
from sqlalchemy.sql import func
from app import db

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


class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_base'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Network, Security, Application, etc.
    tags = db.Column(db.String(256))  # Comma-separated tags
    severity_level = db.Column(db.String(20))  # Same as incident severity: critical, high, medium, low
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    author = db.relationship('User', backref=db.backref('kb_articles', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'tags': self.tags,
            'severity_level': self.severity_level,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
    @staticmethod
    def create_article(title, content, category, tags=None, severity_level=None, created_by=None):
        article = KnowledgeBase(
            title=title,
            content=content,
            category=category,
            tags=tags,
            severity_level=severity_level,
            created_by=created_by
        )
        db.session.add(article)
        db.session.commit()
        
        # Create activity log
        log_activity('kb_article_created', f"New knowledge base article created: {title}", created_by)
        
        return article
    
    @staticmethod
    def get_article_by_id(article_id):
        return KnowledgeBase.query.get(article_id)
    
    @staticmethod
    def get_all_articles():
        return KnowledgeBase.query.order_by(KnowledgeBase.updated_at.desc()).all()
    
    @staticmethod
    def get_articles_by_category(category):
        return KnowledgeBase.query.filter_by(category=category).order_by(KnowledgeBase.updated_at.desc()).all()
    
    @staticmethod
    def get_articles_by_severity(severity_level):
        return KnowledgeBase.query.filter_by(severity_level=severity_level).order_by(KnowledgeBase.updated_at.desc()).all()
    
    @staticmethod
    def search_articles(query):
        search = f"%{query}%"
        return KnowledgeBase.query.filter(
            db.or_(
                KnowledgeBase.title.ilike(search),
                KnowledgeBase.content.ilike(search),
                KnowledgeBase.tags.ilike(search)
            )
        ).order_by(KnowledgeBase.updated_at.desc()).all()
    
    @staticmethod
    def find_relevant_solutions(incident_title, incident_description, severity):
        """Find relevant knowledge base articles based on incident details"""
        combined_text = f"{incident_title} {incident_description}"
        search_terms = combined_text.lower().split()
        
        # Filter out common words and short words
        common_words = {'the', 'and', 'or', 'is', 'in', 'to', 'a', 'an', 'for', 'of', 'with', 'by'}
        search_terms = [term for term in search_terms if term not in common_words and len(term) > 2]
        
        if not search_terms:
            # If no meaningful search terms, return articles by severity
            return KnowledgeBase.query.filter_by(severity_level=severity).limit(3).all()
        
        # Build a query to search for articles containing any of the search terms
        conditions = []
        for term in search_terms:
            search = f"%{term}%"
            conditions.append(KnowledgeBase.title.ilike(search))
            conditions.append(KnowledgeBase.content.ilike(search))
            conditions.append(KnowledgeBase.tags.ilike(search))
        
        # Combine all conditions with OR
        query = KnowledgeBase.query.filter(
            db.or_(*conditions)
        )
        
        # Prioritize by severity match
        if severity:
            query = query.order_by(
                # Exact severity match first
                KnowledgeBase.severity_level == severity.desc(), 
                KnowledgeBase.updated_at.desc()
            )
        
        return query.limit(3).all()


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
