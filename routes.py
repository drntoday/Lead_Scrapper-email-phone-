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
