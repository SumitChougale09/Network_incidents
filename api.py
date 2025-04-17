from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import Incident, IncidentUpdate, Team, User, get_incident_stats, get_recent_activities
import datetime

api_bp = Blueprint('api', __name__)

# Helper function to format incident data
def format_incident(incident):
    return {
        'id': incident.id,
        'title': incident.title,
        'description': incident.description,
        'severity': incident.severity,
        'status': incident.status,
        'reporter_id': incident.reporter_id,
        'reporter': User.get_user_by_id(incident.reporter_id).username if User.get_user_by_id(incident.reporter_id) else None,
        'assignee_id': incident.assignee_id,
        'assignee': User.get_user_by_id(incident.assignee_id).username if incident.assignee_id and User.get_user_by_id(incident.assignee_id) else None,
        'team_id': incident.team_id,
        'team': Team.get_team_by_id(incident.team_id).name if incident.team_id and Team.get_team_by_id(incident.team_id) else None,
        'created_at': incident.created_at.isoformat(),
        'updated_at': incident.updated_at.isoformat(),
        'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
        'closed_at': incident.closed_at.isoformat() if incident.closed_at else None
    }

@api_bp.route('/incidents', methods=['GET'])
@login_required
def get_incidents():
    status = request.args.get('status')
    severity = request.args.get('severity')
    
    incidents = Incident.get_all_incidents()
    
    if status:
        incidents = [inc for inc in incidents if inc.status == status]
    
    if severity:
        incidents = [inc for inc in incidents if inc.severity == severity]
    
    return jsonify({
        'incidents': [format_incident(inc) for inc in incidents]
    })

@api_bp.route('/incidents/<incident_id>', methods=['GET'])
@login_required
def get_incident(incident_id):
    incident = Incident.get_incident_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    # Get updates for this incident
    incident_updates = IncidentUpdate.get_updates_for_incident(incident_id)
    updates_data = []
    
    for update in incident_updates:
        user = User.get_user_by_id(update.user_id)
        updates_data.append({
            'id': update.id,
            'content': update.content,
            'user_id': update.user_id,
            'user': user.username if user else None,
            'created_at': update.created_at.isoformat()
        })
    
    return jsonify({
        'incident': format_incident(incident),
        'updates': updates_data
    })

@api_bp.route('/incidents', methods=['POST'])
@login_required
def create_incident():
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    title = data.get('title')
    description = data.get('description', '')
    severity = data.get('severity')
    
    if not title or not severity:
        return jsonify({'error': 'Title and severity are required'}), 400
    
    # Create incident
    incident = Incident.create_incident(
        title=title,
        description=description,
        severity=severity,
        reporter_id=current_user.id
    )
    
    return jsonify({
        'message': 'Incident created successfully',
        'incident': format_incident(incident)
    }), 201

@api_bp.route('/incidents/<incident_id>', methods=['PUT'])
@login_required
def update_incident(incident_id):
    incident = Incident.get_incident_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update status
    if 'status' in data:
        incident.set_status(data['status'])
    
    # Update team assignment
    if 'team_id' in data:
        assignee_id = data.get('assignee_id')
        incident.assign(data['team_id'], assignee_id)
    
    # Add update comment
    if 'comment' in data:
        IncidentUpdate.create_update(incident_id, current_user.id, data['comment'])
    
    return jsonify({
        'message': 'Incident updated successfully',
        'incident': format_incident(incident)
    })

@api_bp.route('/teams', methods=['GET'])
@login_required
def get_teams():
    teams = Team.get_all_teams()
    
    return jsonify({
        'teams': [team.to_dict() for team in teams]
    })

@api_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    return jsonify(get_incident_stats())

@api_bp.route('/activities', methods=['GET'])
@login_required
def get_activities():
    limit = request.args.get('limit', 20, type=int)
    activities = get_recent_activities(limit)
    
    # Format timestamps
    for activity in activities:
        activity['timestamp'] = activity['timestamp'].isoformat()
    
    return jsonify({
        'activities': activities
    })
