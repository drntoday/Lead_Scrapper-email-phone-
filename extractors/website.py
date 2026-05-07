import requests
import re
import time
import random
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from config import Config

class WebsiteExtractor:
    """
    Extracts contact information from a company's website.
    Scrapes emails and phone numbers from public pages only.
    """
    
    def __init__(self):
        self.user_agent = Config.USER_AGENT
        self.delay_min = Config.REQUEST_DELAY_MIN
        self.delay_max = Config.REQUEST_DELAY_MAX
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
    
    def _validate_url(self, url):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def _extract_emails(self, text):
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        common_false_emails = [
            'example@', 'test@', 'user@', 'email@', 'yourname@',
            'company@example.com', 'info@example.com'
        ]
        return list(set(
            email for email in emails 
            if not any(fake in email.lower() for fake in common_false_emails)
        ))
    
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
    
    def extract_from_url(self, url):
        url = self._validate_url(url)
        leads = []
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '')
        company_name = domain.split('.')[0].capitalize()
        
        try:
            time.sleep(random.uniform(self.delay_min, self.delay_max))
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            page_text = soup.get_text()
            emails = self._extract_emails(page_text)
            phones = self._extract_phones(page_text)
            
            contact_links = soup.find_all('a', href=True)
            for link in contact_links:
                href = link['href']
                if href.startswith('mailto:'):
                    email = href.replace('mailto:', '').split('?')[0]
                    emails.append(email)
                if href.startswith('tel:'):
                    phone = href.replace('tel:', '')
                    phones.append(phone)
            
            emails = list(set(emails))
            phones = list(set(phones))
            
            if emails:
                for idx, email in enumerate(emails):
                    lead = {
                        'first_name': None,
                        'last_name': None,
                        'company': company_name,
                        'job_title': None,
                        'email': email,
                        'phone': phones[idx] if idx < len(phones) else (phones[0] if phones else None),
                        'source': 'website'
                    }
                    leads.append(lead)
            else:
                lead = {
                    'first_name': None,
                    'last_name': None,
                    'company': company_name,
                    'job_title': None,
                    'email': f'info@{domain}',
                    'phone': phones[0] if phones else None,
                    'source': 'website'
                }
                leads.append(lead)
            
        except requests.RequestException as e:
            print(f"[WebsiteExtractor] Error extracting from {url}: {e}")
        
        return leads
