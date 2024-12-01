from cryptography.fernet import Fernet
from django.conf import settings


cipher_suite = Fernet(settings.ENCRYPTION_KEY)


def encrypt_text(plain_text):
    """
    Encrypts a given plain text string using Fernet symmetric encryption.
    """
    cipher_text = cipher_suite.encrypt(plain_text.encode("utf-8"))
    return cipher_text.decode("utf-8")


def decrypt_text(cipher_text):
    """
    Decrypts a given encrypted text string using Fernet symmetric encryption.
    """
    plain_text = cipher_suite.decrypt(cipher_text.encode("utf-8"))
    return plain_text.decode("utf-8")
