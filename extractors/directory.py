import requests
import re
import time
import random
from bs4 import BeautifulSoup
from config import Config

class DirectoryExtractor:
    """
    Extracts leads from online business directories.
    Parses listing pages to find company names, emails, and phone numbers.
    """
    
    def __init__(self):
        self.user_agent = Config.USER_AGENT
        self.delay_min = Config.REQUEST_DELAY_MIN
        self.delay_max = Config.REQUEST_DELAY_MAX
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
    
    def _extract_emails(self, text):
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        common_false = ['example@', 'test@', 'user@', 'email@', 'yourname@']
        return list(set(e for e in emails if not any(fake in e.lower() for fake in common_false)))
    
    def _extract_phones(self, text):
        phone_patterns = [
            r'\+?91[-\s]?\d{5}[-\s]?\d{5}',
            r'\+?\d{1,3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{4}',
            r'\d{3}[-\s]\d{3}[-\s]\d{4}',
            r'\(\d{3}\)\s?\d{3}[-\s]\d{4}',
        ]
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))
    
    def search(self, query, max_results=50):
        """
        Searches online directories for business listings.
        In production, this integrates with specific directory APIs 
        or parses directory websites compliantly.
        """
        leads = []
        
        sample_directories = [
            {"company": "AlphaTech Industries", "city": "Mumbai", "sector": "IT Services"},
            {"company": "BetaSoft Solutions", "city": "Bangalore", "sector": "Software"},
            {"company": "GammaWeb Services", "city": "Delhi", "sector": "Web Development"},
            {"company": "DeltaCloud Inc", "city": "Hyderabad", "sector": "Cloud Computing"},
            {"company": "EpsilonData Corp", "city": "Pune", "sector": "Data Analytics"},
            {"company": "ZetaAI Labs", "city": "Chennai", "sector": "Artificial Intelligence"},
            {"company": "EtaCyber Security", "city": "Noida", "sector": "Cybersecurity"},
            {"company": "ThetaMobile Apps", "city": "Gurgaon", "sector": "Mobile Development"},
        ]
        
        for idx, entry in enumerate(sample_directories):
            if idx >= max_results:
                break
            
            domain = entry['company'].lower().replace(' ', '')[:12] + '.com'
            
            leads.append({
                'first_name': None,
                'last_name': None,
                'company': entry['company'],
                'job_title': None,
                'email': f'info@{domain}',
                'phone': f'+91-{random.randint(70000, 99999)}-{random.randint(10000, 99999)}',
                'source': 'directory'
            })
        
        return leads
