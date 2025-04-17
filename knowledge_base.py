from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import KnowledgeBase, init_data, log_activity

kb_bp = Blueprint('kb', __name__, url_prefix='/kb')

@kb_bp.route('/')
@login_required
def kb_home():
    """Knowledge Base home page"""
    articles = KnowledgeBase.get_all_articles()
    return render_template('kb_home.html', articles=articles)

@kb_bp.route('/article/<int:article_id>')
@login_required
def view_article(article_id):
    """View a single knowledge base article"""
    article = KnowledgeBase.get_article_by_id(article_id)
    if not article:
        flash('Article not found', 'danger')
        return redirect(url_for('kb.kb_home'))
    return render_template('kb_article.html', article=article)

@kb_bp.route('/search')
@login_required
def search():
    """Search for knowledge base articles"""
    query = request.args.get('query', '')
    if not query:
        return redirect(url_for('kb.kb_home'))
    
    articles = KnowledgeBase.search_articles(query)
    return render_template('kb_search.html', articles=articles, query=query)

@kb_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_article():
    """Create a new knowledge base article"""
    # Only admins and engineers can create articles
    if current_user.role not in ['admin', 'support_engineer']:
        flash('You do not have permission to create articles', 'danger')
        return redirect(url_for('kb.kb_home'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        tags = request.form.get('tags')
        severity_level = request.form.get('severity_level')
        
        if not title or not content or not category:
            flash('Title, content and category are required', 'danger')
            return render_template('kb_create.html')
        
        article = KnowledgeBase.create_article(
            title=title,
            content=content,
            category=category,
            tags=tags,
            severity_level=severity_level,
            created_by=current_user.id
        )
        
        flash('Knowledge base article created successfully', 'success')
        return redirect(url_for('kb.view_article', article_id=article.id))
    
    return render_template('kb_create.html')

@kb_bp.route('/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    """Edit a knowledge base article"""
    article = KnowledgeBase.get_article_by_id(article_id)
    if not article:
        flash('Article not found', 'danger')
        return redirect(url_for('kb.kb_home'))
    
    # Only admins or the article creator can edit
    if current_user.role != 'admin' and article.created_by != current_user.id:
        flash('You do not have permission to edit this article', 'danger')
        return redirect(url_for('kb.view_article', article_id=article.id))
    
    if request.method == 'POST':
        article.title = request.form.get('title')
        article.content = request.form.get('content')
        article.category = request.form.get('category')
        article.tags = request.form.get('tags')
        article.severity_level = request.form.get('severity_level')
        
        from app import db
        db.session.commit()
        
        log_activity('kb_article_updated', f"Knowledge base article updated: {article.title}", current_user.id)
        
        flash('Knowledge base article updated successfully', 'success')
        return redirect(url_for('kb.view_article', article_id=article.id))
    
    return render_template('kb_edit.html', article=article)

@kb_bp.route('/delete/<int:article_id>', methods=['POST'])
@login_required
def delete_article(article_id):
    """Delete a knowledge base article"""
    article = KnowledgeBase.get_article_by_id(article_id)
    if not article:
        flash('Article not found', 'danger')
        return redirect(url_for('kb.kb_home'))
    
    # Only admins or the article creator can delete
    if current_user.role != 'admin' and article.created_by != current_user.id:
        flash('You do not have permission to delete this article', 'danger')
        return redirect(url_for('kb.view_article', article_id=article.id))
    
    title = article.title
    
    from app import db
    db.session.delete(article)
    db.session.commit()
    
    log_activity('kb_article_deleted', f"Knowledge base article deleted: {title}", current_user.id)
    
    flash('Knowledge base article deleted successfully', 'success')
    return redirect(url_for('kb.kb_home'))

@kb_bp.route('/api/suggestions', methods=['POST'])
@login_required
def get_suggestions():
    """API endpoint to get suggested knowledge base articles for an incident"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    title = data.get('title', '')
    description = data.get('description', '')
    severity = data.get('severity')
    
    suggested_articles = KnowledgeBase.find_relevant_solutions(title, description, severity)
    
    return jsonify({
        'success': True,
        'suggestions': [article.to_dict() for article in suggested_articles]
    })

# Initialize some sample knowledge base articles
def init_kb_data():
    """Initialize sample knowledge base articles if none exist"""
    if KnowledgeBase.query.count() > 0:
        return
    
    # Create sample articles
    network_articles = [
        {
            'title': 'Troubleshooting Network Connectivity Issues',
            'content': (
                '<h3>Steps to diagnose network connectivity problems:</h3>'
                '<ol>'
                '<li>Check physical connections (cables, ports)</li>'
                '<li>Verify network interface status (ifconfig/ipconfig)</li>'
                '<li>Test local connectivity (ping localhost)</li>'
                '<li>Test DNS resolution (ping domain name)</li>'
                '<li>Check network configuration (IP, subnet, gateway)</li>'
                '<li>Verify firewall settings</li>'
                '<li>Check for network hardware issues</li>'
                '</ol>'
                '<h3>Common commands for diagnosis:</h3>'
                '<pre>ipconfig /all      # Windows\nifconfig -a        # Linux/Mac\nping google.com\ntracert google.com # Windows\ntraceroute google.com # Linux/Mac</pre>'
            ),
            'category': 'Network',
            'tags': 'connectivity,troubleshooting,network,ping,dns',
            'severity_level': 'high'
        },
        {
            'title': 'Resolving DNS Resolution Failures',
            'content': (
                '<h3>When DNS resolution fails:</h3>'
                '<ol>'
                '<li>Verify DNS server settings</li>'
                '<li>Flush DNS cache</li>'
                '<li>Test with alternative DNS servers (e.g., 8.8.8.8)</li>'
                '<li>Check host file entries</li>'
                '</ol>'
                '<h3>Commands to fix DNS issues:</h3>'
                '<pre>ipconfig /flushdns  # Windows\ndscacheutil -flushcache  # Mac\nsystemd-resolve --flush-caches # Linux</pre>'
                '<p>If problems persist, consider checking network equipment and ISP status.</p>'
            ),
            'category': 'Network',
            'tags': 'dns,resolution,network,troubleshooting',
            'severity_level': 'medium'
        }
    ]
    
    security_articles = [
        {
            'title': 'Responding to Suspicious Network Activity',
            'content': (
                '<h3>Immediate steps for suspicious activity:</h3>'
                '<ol>'
                '<li>Isolate affected systems from the network</li>'
                '<li>Capture and preserve logs and evidence</li>'
                '<li>Identify the type and scope of suspicious activity</li>'
                '<li>Document all observations and actions taken</li>'
                '<li>Engage security team for deeper investigation</li>'
                '</ol>'
                '<p>Do not power off systems unless instructed, as this may lose valuable volatile memory evidence.</p>'
                '<h3>Detection commands:</h3>'
                '<pre>netstat -ano  # Check active connections\nwhoami /priv  # Windows user privileges\nps -aux      # Active processes on Linux</pre>'
            ),
            'category': 'Security',
            'tags': 'security,suspicious,incident,response,network',
            'severity_level': 'critical'
        }
    ]
    
    application_articles = [
        {
            'title': 'Troubleshooting Application Timeout Issues',
            'content': (
                '<h3>Common causes of application timeouts:</h3>'
                '<ol>'
                '<li>Insufficient resources (CPU, memory)</li>'
                '<li>Network latency or congestion</li>'
                '<li>Database connection issues</li>'
                '<li>Improper timeout configurations</li>'
                '<li>Application code inefficiencies</li>'
                '</ol>'
                '<h3>Immediate remediation steps:</h3>'
                '<ol>'
                '<li>Restart the application service</li>'
                '<li>Check system resource utilization</li>'
                '<li>Verify database connection pools</li>'
                '<li>Review application and server logs</li>'
                '<li>Test with different network conditions</li>'
                '</ol>'
                '<p>For persistent issues, consider implementing performance monitoring tools.</p>'
            ),
            'category': 'Application',
            'tags': 'application,timeout,performance,troubleshooting',
            'severity_level': 'high'
        },
        {
            'title': 'Resolving Database Connection Errors',
            'content': (
                '<h3>Database connection troubleshooting:</h3>'
                '<ol>'
                '<li>Verify database server status</li>'
                '<li>Check connection string parameters</li>'
                '<li>Ensure proper network connectivity to database</li>'
                '<li>Verify user permissions</li>'
                '<li>Check connection pool settings</li>'
                '<li>Review database logs for errors</li>'
                '</ol>'
                '<h3>Temporary solutions:</h3>'
                '<ul>'
                '<li>Restart database service</li>'
                '<li>Increase connection timeout settings</li>'
                '<li>Implement connection retry logic</li>'
                '<li>Use database replication if available</li>'
                '</ul>'
            ),
            'category': 'Application',
            'tags': 'database,connection,error,sql,troubleshooting',
            'severity_level': 'medium'
        }
    ]
    
    hardware_articles = [
        {
            'title': 'Responding to Server Hardware Failures',
            'content': (
                '<h3>Initial hardware failure response:</h3>'
                '<ol>'
                '<li>Identify affected hardware components</li>'
                '<li>Check system logs for hardware errors</li>'
                '<li>Verify environmental conditions (temperature, power)</li>'
                '<li>Test component functionality if possible</li>'
                '<li>Prepare for hardware replacement if necessary</li>'
                '</ol>'
                '<h3>Temporary workarounds:</h3>'
                '<ul>'
                '<li>Migrate critical services to backup systems</li>'
                '<li>Implement failover if available</li>'
                '<li>Reduce system load to minimum required</li>'
                '<li>Document all troubleshooting steps and findings</li>'
                '</ul>'
                '<p>Hardware issues often require physical intervention - prepare for potential maintenance window.</p>'
            ),
            'category': 'Hardware',
            'tags': 'hardware,server,failure,physical,components',
            'severity_level': 'critical'
        }
    ]
    
    # Create admin user if needed for article creation
    from models import User
    admin = User.query.filter_by(role='admin').first()
    admin_id = admin.id if admin else None
    
    # Add all articles
    all_articles = network_articles + security_articles + application_articles + hardware_articles
    
    for article_data in all_articles:
        KnowledgeBase.create_article(
            title=article_data['title'],
            content=article_data['content'],
            category=article_data['category'],
            tags=article_data['tags'],
            severity_level=article_data['severity_level'],
            created_by=admin_id
        )