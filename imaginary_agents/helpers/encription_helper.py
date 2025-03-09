from cryptography.fernet import Fernet

# Encryption and Decryption functions
def generate_user_encryption_key():
    return Fernet.generate_key()

def encrypt_secret(encryption_key, secret):
    f = Fernet(encryption_key)
    return f.encrypt(secret.encode()).decode()

def decrypt_secret(encryption_key, encrypted_secret):
    f = Fernet(encryption_key)
    return f.decrypt(encrypted_secret.encode()).decode()