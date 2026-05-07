import re
import dns.resolver
import smtplib
import socket

class EmailValidator:
    """
    Multi-layer email validation without sending actual emails.
    Checks: Syntax -> MX Record -> SMTP Handshake -> Catch-All Detection.
    """
    
    @staticmethod
    def syntax_check(email):
        if not email or '@' not in email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def mx_lookup(domain):
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(list(mx_records)) > 0
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, 
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return False
    
    @staticmethod
    def smtp_verify(email, timeout=10):
        domain = email.split('@')[1]
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(sorted(mx_records, key=lambda r: r.preference)[0].exchange)
            
            server = smtplib.SMTP(mx_host, timeout=timeout)
            server.helo()
            server.mail('verify@ethicalbot.com')
            code, _ = server.rcpt(email)
            server.quit()
            return code == 250
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected,
                smtplib.SMTPResponseException, socket.timeout, socket.error,
                dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return False
    
    @staticmethod
    def is_catch_all_domain(domain):
        catch_all_indicators = ['catchall', 'catch-all', 'mailall']
        random_test = f'noexist-{domain}@{domain}'
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(sorted(mx_records, key=lambda r: r.preference)[0].exchange)
            server = smtplib.SMTP(mx_host, timeout=5)
            server.helo()
            server.mail('verify@ethicalbot.com')
            code, _ = server.rcpt(random_test)
            server.quit()
            return code == 250
        except Exception:
            return False
    
    def validate(self, email):
        result = {
            'email': email,
            'is_valid': False,
            'syntax_valid': False,
            'mx_valid': False,
            'smtp_valid': False,
            'is_catch_all': False,
            'confidence_score': 0,
            'reason': ''
        }
        
        if not self.syntax_check(email):
            result['reason'] = 'Invalid email syntax'
            return result
        
        result['syntax_valid'] = True
        result['confidence_score'] = 30
        
        domain = email.split('@')[1]
        
        if not self.mx_lookup(domain):
            result['reason'] = 'No MX records found for domain'
            return result
        
        result['mx_valid'] = True
        result['confidence_score'] = 60
        
        if self.smtp_verify(email):
            result['smtp_valid'] = True
            result['confidence_score'] = 95
            result['is_valid'] = True
        else:
            if self.is_catch_all_domain(domain):
                result['is_catch_all'] = True
                result['confidence_score'] = 50
                result['reason'] = 'Catch-all domain - email may or may not exist'
            else:
                result['confidence_score'] = 60
                result['reason'] = 'SMTP verification failed'
        
        return result
