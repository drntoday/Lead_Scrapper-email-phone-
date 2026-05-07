from flask import Blueprint, render_template, jsonify, request, send_file
from models import Lead
from app import db
import pandas as pd
import os
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/api/leads', methods=['GET'])
def get_leads():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    
    query = Lead.query
    
    if sort_by == 'confidence_score':
        order_col = Lead.confidence_score
    elif sort_by == 'company':
        order_col = Lead.company
    else:
        order_col = Lead.created_at
    
    if order == 'asc':
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    leads = [lead.to_dict() for lead in pagination.items]
    
    return jsonify({
        'leads': leads,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@main.route('/api/leads/count', methods=['GET'])
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

@main.route('/api/leads/export/<format>', methods=['GET'])
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
    
    if format == 'csv':
        filename = f'leads_export_{timestamp}.csv'
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports', filename)
        df.to_csv(filepath, index=False)
        return send_file(filepath, as_attachment=True, download_name=filename, mimetype='text/csv')
    
    elif format == 'xlsx':
        filename = f'leads_export_{timestamp}.xlsx'
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports', filename)
        df.to_excel(filepath, index=False, engine='openpyxl')
        return send_file(filepath, as_attachment=True, download_name=filename, 
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    elif format == 'json':
        filename = f'leads_export_{timestamp}.json'
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports', filename)
        df.to_json(filepath, orient='records', indent=2)
        return send_file(filepath, as_attachment=True, download_name=filename, mimetype='application/json')


@main.route('/api/extract', methods=['POST'])
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
        if source_type == 'google_maps':
            from extractors.google_maps import GoogleMapsExtractor
            extractor = GoogleMapsExtractor()
            raw_leads = extractor.search(search_query, max_results)
        elif source_type == 'directory':
            from extractors.directory import DirectoryExtractor
            extractor = DirectoryExtractor()
            raw_leads = extractor.search(search_query, max_results)
        elif source_type == 'website':
            from extractors.website import WebsiteExtractor
            extractor = WebsiteExtractor()
            raw_leads = extractor.extract_from_url(search_query)
        else:
            return jsonify({'success': False, 'message': f'Unsupported source: {source_type}'}), 400
        
        leads_found = len(raw_leads)
        
        for lead_data in raw_leads:
            try:
                existing = Lead.query.filter_by(email=lead_data.get('email')).first()
                if not existing and lead_data.get('email'):
                    lead = Lead(
                        first_name=lead_data.get('first_name'),
                        last_name=lead_data.get('last_name'),
                        company=lead_data.get('company'),
                        job_title=lead_data.get('job_title'),
                        email=lead_data.get('email'),
                        phone=lead_data.get('phone'),
                        source=source_type,
                        confidence_score=30,
                        verification_status='Unverified'
                    )
                    db.session.add(lead)
                    leads_added += 1
            except Exception as e:
                errors.append(str(e))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'leads_found': leads_found,
            'leads_added': leads_added,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
