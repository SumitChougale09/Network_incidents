from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Incident, IncidentUpdate, Team, User, get_incident_stats, get_recent_activities
from ai_agent import NetworkIncidentAgent

incident_bp = Blueprint('incident', __name__)
ai_agent = NetworkIncidentAgent()

@incident_bp.route('/dashboard')
@login_required
def dashboard():
    # Get incident statistics
    stats = get_incident_stats()
    
    # Get recent incidents (limited to 5)
    recent_incidents = sorted(
        Incident.get_all_incidents(), 
        key=lambda x: x.created_at,
        reverse=True
    )[:5]
    
    # Get recent activities
    recent_activities = get_recent_activities(10)
    
    return render_template(
        'dashboard.html',
        stats=stats,
        recent_incidents=recent_incidents,
        recent_activities=recent_activities
    )

@incident_bp.route('/incidents')
@login_required
def list_incidents():
    status_filter = request.args.get('status', 'all')
    severity_filter = request.args.get('severity', 'all')
    
    # Get all incidents
    all_incidents = Incident.get_all_incidents()
    
    # Apply filters
    filtered_incidents = all_incidents
    
    if status_filter != 'all':
        filtered_incidents = [inc for inc in filtered_incidents if inc.status == status_filter]
    
    if severity_filter != 'all':
        filtered_incidents = [inc for inc in filtered_incidents if inc.severity == severity_filter]
    
    # Sort by created_at (newest first)
    filtered_incidents = sorted(filtered_incidents, key=lambda x: x.created_at, reverse=True)
    
    return render_template(
        'incidents.html',
        incidents=filtered_incidents,
        status_filter=status_filter,
        severity_filter=severity_filter
    )

@incident_bp.route('/incidents/new', methods=['GET', 'POST'])
@login_required
def new_incident():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        severity = request.form.get('severity')
        
        if not title or not severity:
            flash('Title and severity are required', 'danger')
            return redirect(url_for('incident.new_incident'))
        
        # Create incident
        incident = Incident.create_incident(
            title=title,
            description=description,
            severity=severity,
            reporter_id=current_user.id
        )
        
        # Run AI analysis automatically on new incidents if requested
        if request.form.get('auto_analyze') == 'on':
            try:
                solutions = ai_agent.get_solutions(
                    title=title,
                    description=description,
                    severity=severity
                )
                
                # Create an incident update with the analysis
                update_content = f"""
                AI Analysis Results:
                
                Root Cause Analysis:
                {solutions['analysis']}
                
                Suggested Actions:
                {chr(10).join(f'- {action}' for action in solutions['suggested_actions'])}
                
                Confidence Score: {solutions['confidence_score']*100:.1f}%
                
                References:
                {chr(10).join(f'- {ref["type"].upper()}: {ref["reference"]}' for ref in solutions['references'] if 'type' in ref and 'reference' in ref)}
                """
                
                IncidentUpdate.create_update(
                    incident_id=incident.id,
                    user_id=current_user.id,
                    content=update_content
                )
                
                flash('Incident reported and AI analysis completed', 'success')
            except Exception as e:
                flash(f'Incident reported but AI analysis failed: {str(e)}', 'warning')
        else:
            flash('Incident reported successfully', 'success')
            
        return redirect(url_for('incident.view_incident', incident_id=incident.id))
    
    return render_template('incident_details.html', incident=None, teams=Team.get_all_teams())

@incident_bp.route('/incidents/<incident_id>')
@login_required
def view_incident(incident_id):
    incident = Incident.get_incident_by_id(incident_id)
    
    if not incident:
        flash('Incident not found', 'danger')
        return redirect(url_for('incident.list_incidents'))
    
    # Get updates for this incident
    updates = IncidentUpdate.get_updates_for_incident(incident_id)
    
    # Get teams for assignment
    teams = Team.get_all_teams()
    
    # Get potential assignees (all support engineers)
    support_engineers = User.query.filter_by(role='support_engineer').all()
    
    return render_template(
        'incident_details.html',
        incident=incident,
        updates=updates,
        teams=teams,
        support_engineers=support_engineers
    )

@incident_bp.route('/incidents/<incident_id>/update', methods=['POST'])
@login_required
def update_incident(incident_id):
    incident = Incident.get_incident_by_id(incident_id)
    
    if not incident:
        flash('Incident not found', 'danger')
        return redirect(url_for('incident.list_incidents'))
    
    # Handle status update
    new_status = request.form.get('status')
    if new_status and new_status != incident.status:
        incident.set_status(new_status)
    
    # Handle team assignment
    team_id = request.form.get('team_id')
    if team_id and (not incident.team_id or int(team_id) != incident.team_id):
        assignee_id = request.form.get('assignee_id')
        assignee_id = int(assignee_id) if assignee_id else None
        incident.assign(int(team_id), assignee_id)
    
    # Handle update comment
    update_content = request.form.get('update_content')
    if update_content:
        IncidentUpdate.create_update(incident_id, current_user.id, update_content)
    
    flash('Incident updated successfully', 'success')
    return redirect(url_for('incident.view_incident', incident_id=incident_id))

@incident_bp.route('/incidents/<incident_id>/suggestions')
@login_required
def get_incident_suggestions(incident_id):
    """Get AI-generated suggestions for an incident"""
    incident = Incident.get_incident_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    # Get AI-generated solutions
    solutions = ai_agent.get_solutions(
        title=incident.title,
        description=incident.description,
        severity=incident.severity
    )
    
    return jsonify(solutions)

@incident_bp.route('/incidents/<incident_id>/analyze', methods=['POST'])
@login_required
def analyze_incident(incident_id):
    """Trigger AI analysis of an incident"""
    incident = Incident.get_incident_by_id(incident_id)
    
    if not incident:
        flash('Incident not found', 'danger')
        return redirect(url_for('incident.list_incidents'))
    
    try:
        solutions = ai_agent.get_solutions(
            title=incident.title,
            description=incident.description,
            severity=incident.severity
        )
        
        # Create an incident update with the analysis
        update_content = f"""
        AI Analysis Results:
        
        Root Cause Analysis:
        {solutions['analysis']}
        
        Suggested Actions:
        {chr(10).join(f'- {action}' for action in solutions['suggested_actions'])}
        
        Confidence Score: {solutions['confidence_score']*100:.1f}%
        
        References:
        {chr(10).join(f'- {ref["type"].upper()}: {ref["reference"]}' for ref in solutions['references'] if 'type' in ref and 'reference' in ref)}
        """
        
        IncidentUpdate.create_update(
            incident_id=incident_id,
            user_id=current_user.id,
            content=update_content
        )
        
        flash('AI analysis completed successfully', 'success')
    except Exception as e:
        flash(f'Error during AI analysis: {str(e)}', 'danger')
    
    return redirect(url_for('incident.view_incident', incident_id=incident_id))