"""
Script to generate dummy incident data for the Network Incident Management System
This will help populate the database for analysis and visualization purposes
"""

import datetime
import random
import uuid
from sqlalchemy import func
from app import app, db
from models import User, Team, Incident, IncidentUpdate, log_activity

# Ensures consistent random output
random.seed(42)

# Sample incident titles and descriptions
INCIDENT_TITLES = [
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
    "DNS resolution failures",
    "Service discovery unavailable",
    "Kubernetes pod scheduling issues",
    "Docker image pull failures",
    "Monitoring alert storm",
    "Data synchronization delay",
    "Backup job failure",
    "Network packet loss between regions",
    "JWT token validation errors",
    "DDOS attack detected",
    "Inter-service communication timeout"
]

INCIDENT_DESCRIPTIONS = [
    "Users are unable to access the service. All attempts result in connection timeout errors.",
    "The system is experiencing high latency. Response times are exceeding 5 seconds.",
    "Multiple customers reported inability to log in due to authentication failures.",
    "Automated monitoring detected service degradation. Investigation in progress.",
    "The issue appears to be affecting all users in the EU region only.",
    "Database queries are taking longer than usual, causing cascading timeouts.",
    "The third-party API integration is failing intermittently with 503 errors.",
    "Memory usage is increasing steadily, pointing to a potential memory leak.",
    "Network traffic analysis shows unusual patterns consistent with a DDoS attack.",
    "The failover mechanism did not trigger automatically, requiring manual intervention.",
    "Service health checks are failing on multiple nodes in the cluster.",
    "The data pipeline is experiencing delays in processing, creating a backlog.",
    "SSL certificate validation is failing, causing secure connections to be rejected.",
    "Configuration changes deployed in the last release appear to have caused the issue.",
    "Log analysis shows increasing error rates starting around 2:30 AM UTC."
]

# Sample update messages
UPDATE_MESSAGES = [
    "Initial investigation started. Looking into the root cause.",
    "Identified that the issue is related to recent configuration changes.",
    "Restarted the affected services. Monitoring the situation.",
    "Root cause appears to be network connectivity between services.",
    "Applied temporary workaround. Permanent fix in progress.",
    "Rolled back recent deployment that was causing issues.",
    "Escalated to database team for further investigation.",
    "Scaling up resources to handle increased load.",
    "Implemented rate limiting to prevent cascading failures.",
    "Issue resolved. Services running normally again.",
    "Post-mortem analysis in progress to prevent recurrence.",
    "Updated monitoring thresholds to catch similar issues earlier.",
    "Working with vendor on a permanent solution.",
    "Backup systems have been activated. Service restored.",
    "Deployed hotfix to address the immediate issue."
]

# Severity and status distributions (weighted for realism)
SEVERITY_WEIGHTS = {
    "critical": 0.1,  # 10% are critical
    "high": 0.25,     # 25% are high
    "medium": 0.4,    # 40% are medium
    "low": 0.25       # 25% are low
}

STATUS_PROGRESSION = ["open", "assigned", "in_progress", "resolved", "closed"]

def random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    time_delta = end_date - start_date
    random_days = random.randrange(time_delta.days)
    return start_date + datetime.timedelta(days=random_days)

def random_time_delta(min_hours=1, max_hours=48):
    """Generate a random time delta between min_hours and max_hours"""
    hours = random.randint(min_hours, max_hours)
    return datetime.timedelta(hours=hours)

def generate_dummy_incidents(num_incidents=50):
    """Generate dummy incidents with realistic timestamps, severities, and progression"""
    
    print(f"Generating {num_incidents} dummy incidents...")
    
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
    
    # Track the number of incidents per severity for distribution
    severity_count = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    
    for i in range(num_incidents):
        # Generate a unique incident ID
        incident_id = str(uuid.uuid4())
        
        # Randomly select a title and description
        title = random.choice(INCIDENT_TITLES)
        description = random.choice(INCIDENT_DESCRIPTIONS)
        
        # Choose severity based on weighted distribution
        severity = random.choices(
            list(SEVERITY_WEIGHTS.keys()),
            weights=list(SEVERITY_WEIGHTS.values()),
            k=1
        )[0]
        
        severity_count[severity] += 1
        
        # Randomly assign a creation date within the past three months
        created_at = random_date(start_date, current_date)
        
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
        
        # Randomly determine how far this incident has progressed
        progress_level = random.choices(
            range(len(STATUS_PROGRESSION)),
            # Weight towards resolved/closed for older incidents
            weights=[0.1, 0.15, 0.25, 0.3, 0.2],
            k=1
        )[0]
        
        # Process the incident through its determined progression
        current_status_idx = 0
        current_time = created_at
        
        # Add random updates as the incident progresses
        num_updates = random.randint(1, 5)  # Between 1 and 5 updates
        
        for j in range(num_updates):
            # Add some time since the last update
            current_time += random_time_delta(min_hours=1, max_hours=24)
            
            # Don't go beyond current date
            if current_time > current_date:
                current_time = current_date
                
            # Add update
            update_content = random.choice(UPDATE_MESSAGES)
            update_author = random.choice(users)
            
            incident_update = IncidentUpdate(
                incident_id=incident_id,
                user_id=update_author.id,
                content=update_content,
                created_at=current_time
            )
            
            db.session.add(incident_update)
            
            # Progress incident status if we haven't reached the final determined status
            if current_status_idx < progress_level:
                current_status_idx += 1
                new_status = STATUS_PROGRESSION[current_status_idx]
                
                # Assign to a team and/or user when transitioning to assigned
                if new_status == "assigned":
                    team = random.choice(teams)
                    assignee = random.choice(team.members.all() or [None])
                    
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
        
    # Commit all changes to the database
    db.session.commit()
    
    # Print summary of generated incidents
    print("Dummy data generation complete.")
    print(f"Incident severity distribution:")
    for severity, count in severity_count.items():
        print(f"  - {severity}: {count} incidents ({count/num_incidents*100:.1f}%)")
    
    return True

if __name__ == "__main__":
    with app.app_context():
        # Check if we already have incidents in the database
        existing_count = Incident.query.count()
        
        if existing_count > 5:  # We consider more than 5 as having sufficient data
            print(f"Found {existing_count} existing incidents in the database.")
            response = input("Do you want to generate additional dummy incidents? (y/n): ")
            
            if response.lower() != 'y':
                print("Exiting without generating additional data.")
                exit(0)
        
        # Generate the dummy data
        generate_dummy_incidents(20)  # Generate 20 incidents by default