from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import Incident, get_incident_stats
import pandas as pd
import numpy as np
from ml_model import predict_incidents

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis')
@login_required
def analysis_dashboard():
    # Check if user is admin
    if current_user.role != 'admin':
        return render_template('analysis.html', admin_access=False)
    
    # Get incidents data for analysis
    all_incidents = Incident.get_all_incidents()
    
    return render_template('analysis.html', admin_access=True)

@analysis_bp.route('/api/analysis/incident-trends')
@login_required
def incident_trends():
    # Get all incidents
    all_incidents = Incident.get_all_incidents()
    
    # Convert to pandas DataFrame for easier analysis
    data = []
    for incident in all_incidents:
        data.append({
            'id': incident.id,
            'title': incident.title,
            'severity': incident.severity,
            'status': incident.status,
            'created_at': incident.created_at,
            'resolved_at': incident.resolved_at,
            'time_to_resolve': (incident.resolved_at - incident.created_at).total_seconds() / 3600 if incident.resolved_at else None
        })
    
    df = pd.DataFrame(data)
    
    # If no incidents, return empty data
    if df.empty:
        return jsonify({
            'incidents_by_day': [],
            'incidents_by_severity': [],
            'avg_resolution_time': 0
        })
    
    # Convert datetime to date for grouping
    if not df.empty and 'created_at' in df.columns:
        df['date'] = df['created_at'].dt.date
    
    # Incidents by day
    if not df.empty and 'date' in df.columns:
        incidents_by_day = df.groupby('date').size().reset_index(name='count')
        incidents_by_day['date'] = incidents_by_day['date'].astype(str)
        incidents_by_day_data = incidents_by_day.to_dict('records')
    else:
        incidents_by_day_data = []
    
    # Incidents by severity
    if not df.empty and 'severity' in df.columns:
        incidents_by_severity = df.groupby('severity').size().reset_index(name='count')
        incidents_by_severity_data = incidents_by_severity.to_dict('records')
    else:
        incidents_by_severity_data = []
    
    # Average resolution time (in hours)
    avg_resolution_time = df['time_to_resolve'].mean() if 'time_to_resolve' in df.columns and not df['time_to_resolve'].isna().all() else 0
    
    return jsonify({
        'incidents_by_day': incidents_by_day_data,
        'incidents_by_severity': incidents_by_severity_data,
        'avg_resolution_time': avg_resolution_time
    })

@analysis_bp.route('/api/analysis/prediction')
@login_required
def incident_prediction():
    # This would use our ML model to predict incidents
    prediction_data = predict_incidents()
    
    return jsonify(prediction_data)

@analysis_bp.route('/api/analysis/performance')
@login_required
def team_performance():
    # Get all incidents
    all_incidents = Incident.get_all_incidents()
    
    # Convert to pandas DataFrame for easier analysis
    data = []
    for incident in all_incidents:
        if incident.team_id is not None:
            resolution_time = None
            if incident.resolved_at and incident.created_at:
                resolution_time = (incident.resolved_at - incident.created_at).total_seconds() / 3600  # hours
            
            data.append({
                'id': incident.id,
                'team_id': incident.team_id,
                'severity': incident.severity,
                'status': incident.status,
                'created_at': incident.created_at,
                'resolved_at': incident.resolved_at,
                'resolution_time': resolution_time
            })
    
    df = pd.DataFrame(data)
    
    # If no incidents with team assignments, return empty data
    if df.empty:
        return jsonify({
            'team_incident_counts': [],
            'team_resolution_times': []
        })
    
    # Incident counts by team
    if not df.empty and 'team_id' in df.columns:
        team_counts = df.groupby('team_id').size().reset_index(name='count')
        team_counts_data = team_counts.to_dict('records')
    else:
        team_counts_data = []
    
    # Average resolution time by team
    if not df.empty and 'team_id' in df.columns and 'resolution_time' in df.columns:
        resolution_times = df[~df['resolution_time'].isna()]
        
        if not resolution_times.empty:
            team_resolution = resolution_times.groupby('team_id')['resolution_time'].mean().reset_index()
            team_resolution_data = team_resolution.to_dict('records')
        else:
            team_resolution_data = []
    else:
        team_resolution_data = []
    
    return jsonify({
        'team_incident_counts': team_counts_data,
        'team_resolution_times': team_resolution_data
    })
