import json
import os
from datetime import datetime
import hashlib

class EmailManager:
    def __init__(self):
        self.email_file = 'pkg_keys/registered_emails.json'
        self.salt = 'encra'
        self._load_emails()

    def _load_emails(self):
        if os.path.exists(self.email_file):
            with open(self.email_file, 'r') as f:
                self.registered_emails = json.load(f)
        else:
            self.registered_emails = {}
            self._save_emails()

    def _save_emails(self):
        os.makedirs(os.path.dirname(self.email_file), exist_ok=True)
        with open(self.email_file, 'w') as f:
            json.dump(self.registered_emails, f, indent=2)

    def _hash_email(self, email):
        salted_email = email + self.salt
        return hashlib.sha256(salted_email.encode()).hexdigest()

    def is_registered(self, email):
        email_hash = self._hash_email(email)
        return email_hash in self.registered_emails

    def register_email(self, email):
        if self.is_registered(email):
            raise ValueError("이미 등록된 이메일입니다.")
        
        email_hash = self._hash_email(email)
        self.registered_emails[email_hash] = {
            "registered_at": datetime.now().isoformat(),
            "verified": False
        }
        self._save_emails()

    def verify_email(self, email):
        if not self.is_registered(email):
            raise ValueError("등록되지 않은 이메일입니다.")
        
        email_hash = self._hash_email(email)
        self.registered_emails[email_hash]["verified"] = True
        self.registered_emails[email_hash]["verified_at"] = datetime.now().isoformat()
        self._save_emails()

    def is_verified(self, email):
        if not self.is_registered(email):
            return False
        
        email_hash = self._hash_email(email)
        return self.registered_emails[email_hash].get("verified", False)