import os
from cryptography.fernet import Fernet

KEY = os.getenv("FERNET_KEY")
fernet = Fernet(KEY.encode())

def encrypt(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()

def decrypt(data: str) -> str:
    return fernet.decrypt(data.encode()).decode()