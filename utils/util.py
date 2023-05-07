import os
from hashlib import sha256

def hash_password(password):
    hashed_password = sha256(password.encode()).hexdigest()
    return hashed_password

def generate_cookie():
    return os.urandom(16).hex()

def generate_user_id():
    return os.urandom(24).hex()