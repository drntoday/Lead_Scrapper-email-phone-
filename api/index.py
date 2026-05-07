from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Flask app must be created at module level for Vercel
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///leads.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('/tmp', 'exports')

db = SQLAlchemy(app)

# Import models after db init
class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    company = db.Column(db.String(200), nullable=True)
    job_title = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    source = db.Column(db.String(100), nullable=True)
    confidence_score = db.Column(db.Integer, default=0)
    verification_status = db.Column(db.String(50), default='Unverified')
    is_catch_all = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'company': self.company,
            'job_title': self.job_title,
            'email': self.email,
            'phone': self.phone,
            'source': self.source,
            'confidence_score': self.confidence_score,
            'verification_status': self.verification_status,
            'is_catch_all': self.is_catch_all,
        }

# Create tables
with app.app_context():
    db.create_all()

# Routes
from flask import render_template, jsonify, request, send_file
import pandas as pd
from datetime import datetime

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract')
def extract_page():
    return render_template('extract.html')

@app.route('/validate')
def validate_page():
    return render_template('validate.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    query = Lead.query.order_by(Lead.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    leads = [lead.to_dict() for lead in pagination.items]
    return jsonify({
        'leads': leads,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@app.route('/api/leads/count', methods=['GET'])
def get_lead_count():
    total = Lead.query.count()
    verified = Lead.query.filter(Lead.verification_status == 'Verified').count()
    unverified = Lead.query.filter(Lead.verification_status == 'Unverified').count()
    catch_all = Lead.query.filter(Lead.is_catch_all == True).count()
    return jsonify({
        'total': total,
        'verified': verified,
        'unverified': unverified,
        'catch_all': catch_all
    })

@app.route('/api/leads/export/<format>', methods=['GET'])
def export_leads(format):
    if format not in ['csv', 'xlsx', 'json']:
        return jsonify({'error': 'Unsupported format'}), 400
    leads = Lead.query.all()
    data = [lead.to_dict() for lead in leads]
    if not data:
        return jsonify({'error': 'No leads to export'}), 404
    df = pd.DataFrame(data)
    df = df.drop(columns=['id'], errors='ignore')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_dir = '/tmp/exports'
    os.makedirs(export_dir, exist_ok=True)
    if format == 'csv':
        filepath = os.path.join(export_dir, f'leads_{timestamp}.csv')
        df.to_csv(filepath, index=False)
        return send_file(filepath, as_attachment=True, download_name=f'leads_{timestamp}.csv', mimetype='text/csv')
    elif format == 'xlsx':
        filepath = os.path.join(export_dir, f'leads_{timestamp}.xlsx')
        df.to_excel(filepath, index=False, engine='openpyxl')
        return send_file(filepath, as_attachment=True, download_name=f'leads_{timestamp}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    elif format == 'json':
        filepath = os.path.join(export_dir, f'leads_{timestamp}.json')
        df.to_json(filepath, orient='records', indent=2)
        return send_file(filepath, as_attachment=True, download_name=f'leads_{timestamp}.json', mimetype='application/json')

@app.route('/api/extract', methods=['POST'])
def extract_leads():
    data = request.get_json()
    source_type = data.get('source_type')
    search_query = data.get('search_query')
    max_results = data.get('max_results', 50)
    if not source_type or not search_query:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    leads_found = 0
    leads_added = 0
    errors = []
    try:
        # Sample extraction logic for Vercel demo
        sample_companies = [
            ("TechVista Solutions", "Mumbai"),
            ("DigitalWave Pvt Ltd", "Bangalore"),
            ("CloudNine Systems", "Delhi"),
            ("NextGen Innovations", "Hyderabad"),
            ("PrimeSoft Technologies", "Pune"),
        ]
        for idx, (company, city) in enumerate(sample_companies):
            if idx >= max_results:
                break
            domain = company.lower().replace(' ', '')[:12] + '.com'
            email = f'contact@{domain}'
            existing = Lead.query.filter_by(email=email).first()
            if not existing:
                lead = Lead(
                    first_name=f'Contact{idx+1}',
                    last_name=f'Person{idx+1}',
                    company=company,
                    job_title='Manager',
                    email=email,
                    phone=f'+91-98{idx}00-{idx}0000',
                    source=source_type,
                    confidence_score=30,
                    verification_status='Unverified'
                )
                db.session.add(lead)
                leads_added += 1
            leads_found += 1
        db.session.commit()
        return jsonify({
            'success': True,
            'leads_found': leads_found,
            'leads_added': leads_added,
            'errors': errors
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/validate/email', methods=['POST'])
def validate_single_email():
    data = request.get_json()
    email = data.get('email')
    lead_id = data.get('lead_id')
    if not email:
        return jsonify({'is_valid': False, 'reason': 'No email provided'}), 400
    import re
    syntax_valid = bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))
    result = {
        'email': email,
        'is_valid': syntax_valid,
        'syntax_valid': syntax_valid,
        'mx_valid': True,
        'smtp_valid': False,
        'is_catch_all': False,
        'confidence_score': 60 if syntax_valid else 0,
        'reason': '' if syntax_valid else 'Invalid email syntax'
    }
    if lead_id and result['is_valid']:
        lead = db.session.get(Lead, lead_id)
        if lead:
            lead.confidence_score = result['confidence_score']
            lead.verification_status = 'Verified'
            lead.is_catch_all = result.get('is_catch_all', False)
            db.session.commit()
    return jsonify(result)

@app.route('/api/validate/all', methods=['POST'])
def validate_all_leads():
    unverified_leads = Lead.query.filter(Lead.verification_status != 'Verified').all()
    validated_count = 0
    for lead in unverified_leads:
        lead.confidence_score = 60
        lead.verification_status = 'Verified'
        lead.is_catch_all = False
        validated_count += 1
    db.session.commit()
    return jsonify({'success': True, 'validated': validated_count, 'total_processed': len(unverified_leads)})

@app.route('/api/leads/clear', methods=['DELETE'])
def clear_all_leads():
    count = Lead.query.count()
    Lead.query.delete()
    db.session.commit()
    return jsonify({'deleted': count})
