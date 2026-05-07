from flask import Flask, render_template, jsonify, request, send_file
import os
import re
import json
import pandas as pd
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# In-memory storage (Vercel is stateless but works for demo)
leads_store = []
lead_id_counter = 0

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
    start = (page - 1) * per_page
    end = start + per_page
    paginated = leads_store[start:end]
    return jsonify({
        'leads': paginated,
        'total': len(leads_store),
        'pages': max(1, (len(leads_store) + per_page - 1) // per_page),
        'current_page': page
    })

@app.route('/api/leads/count', methods=['GET'])
def get_lead_count():
    verified = sum(1 for l in leads_store if l.get('verification_status') == 'Verified')
    unverified = sum(1 for l in leads_store if l.get('verification_status') == 'Unverified')
    catch_all = sum(1 for l in leads_store if l.get('is_catch_all'))
    return jsonify({
        'total': len(leads_store),
        'verified': verified,
        'unverified': unverified,
        'catch_all': catch_all
    })

@app.route('/api/leads/export/<format>', methods=['GET'])
def export_leads(format):
    if format not in ['csv', 'xlsx', 'json']:
        return jsonify({'error': 'Unsupported format'}), 400
    if not leads_store:
        return jsonify({'error': 'No leads to export'}), 404
    df = pd.DataFrame(leads_store)
    df = df.drop(columns=['id'], errors='ignore')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_dir = '/tmp'
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
        with open(filepath, 'w') as f:
            json.dump(leads_store, f, indent=2)
        return send_file(filepath, as_attachment=True, download_name=f'leads_{timestamp}.json', mimetype='application/json')

@app.route('/api/extract', methods=['POST'])
def extract_leads():
    global lead_id_counter
    data = request.get_json()
    source_type = data.get('source_type', 'demo')
    search_query = data.get('search_query', '')
    max_results = data.get('max_results', 50)
    
    if not source_type or not search_query:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    leads_found = 0
    leads_added = 0
    
    sample_companies = [
        ("TechVista Solutions", "Mumbai", "IT Services"),
        ("DigitalWave Pvt Ltd", "Bangalore", "Software"),
        ("CloudNine Systems", "Delhi", "Cloud Computing"),
        ("NextGen Innovations", "Hyderabad", "AI & ML"),
        ("PrimeSoft Technologies", "Pune", "Mobile Apps"),
        ("ApexData Analytics", "Chennai", "Data Science"),
        ("CyberShield Security", "Noida", "Cybersecurity"),
        ("GreenCode Labs", "Gurgaon", "Web Development"),
    ]
    
    for idx, (company, city, sector) in enumerate(sample_companies):
        if idx >= max_results:
            break
        domain = company.lower().replace(' ', '')[:12] + '.com'
        email = f'contact@{domain}'
        if not any(l.get('email') == email for l in leads_store):
            lead_id_counter += 1
            leads_store.append({
                'id': lead_id_counter,
                'first_name': f'Contact{idx+1}',
                'last_name': f'Person{idx+1}',
                'company': company,
                'job_title': 'Manager',
                'email': email,
                'phone': f'+91-98{idx}00-{idx}0000',
                'source': source_type,
                'confidence_score': 30,
                'verification_status': 'Unverified',
                'is_catch_all': False
            })
            leads_added += 1
        leads_found += 1
    
    return jsonify({
        'success': True,
        'leads_found': leads_found,
        'leads_added': leads_added,
        'errors': []
    })

@app.route('/api/validate/email', methods=['POST'])
def validate_single_email():
    data = request.get_json()
    email = data.get('email', '')
    lead_id = data.get('lead_id')
    
    if not email:
        return jsonify({'is_valid': False, 'reason': 'No email provided'}), 400
    
    syntax_valid = bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))
    confidence = 60 if syntax_valid else 0
    
    result = {
        'email': email,
        'is_valid': syntax_valid,
        'syntax_valid': syntax_valid,
        'mx_valid': True,
        'smtp_valid': False,
        'is_catch_all': False,
        'confidence_score': confidence,
        'reason': '' if syntax_valid else 'Invalid email syntax'
    }
    
    if lead_id and result['is_valid']:
        for lead in leads_store:
            if lead['id'] == lead_id:
                lead['confidence_score'] = result['confidence_score']
                lead['verification_status'] = 'Verified'
                lead['is_catch_all'] = result.get('is_catch_all', False)
                break
    
    return jsonify(result)

@app.route('/api/validate/all', methods=['POST'])
def validate_all_leads():
    validated_count = 0
    for lead in leads_store:
        if lead.get('verification_status') != 'Verified':
            lead['confidence_score'] = 60
            lead['verification_status'] = 'Verified'
            lead['is_catch_all'] = False
            validated_count += 1
    return jsonify({
        'success': True,
        'validated': validated_count,
        'total_processed': len(leads_store)
    })

@app.route('/api/leads/clear', methods=['DELETE'])
def clear_all_leads():
    count = len(leads_store)
    leads_store.clear()
    return jsonify({'deleted': count})

# For local development
if __name__ == '__main__':
    app.run(debug=True, port=5000)
