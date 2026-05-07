from app import db
from datetime import datetime

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
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
