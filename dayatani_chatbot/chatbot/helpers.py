from cryptography.fernet import Fernet
import os


def encrypt_message(message):
    key = os.getenv('FERNET_KEY')
    cipher_suite = Fernet(key)
    encrypted_message = cipher_suite.encrypt(message.encode())
    return encrypted_message.decode()

def decrypt_message(encrypted_message):
    key = os.getenv('FERNET_KEY')
    cipher_suite = Fernet(key)
    decrypted_message = cipher_suite.decrypt(encrypted_message.encode()).decode()
    return decrypted_message

