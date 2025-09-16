#!/usr/bin/env python3
"""
Secure Cryptography Utilities for xanadOS Search & Destroy
Replaces manual crypto implementations with secure, tested cryptography library functions.
"""

import hashlib
import hmac
import os
import secrets
from typing import Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


class SecureCrypto:
    """Secure cryptographic operations using the cryptography library."""

    def __init__(self) -> None:
        """Initialize secure crypto utilities."""
        self._fernet_key: bytes | None = None
        self._fernet: Fernet | None = None

    def generate_key(self) -> bytes:
        """Generate a secure random key for Fernet encryption."""
        return Fernet.generate_key()

    def set_encryption_key(self, key: bytes) -> None:
        """Set the encryption key for symmetric operations."""
        self._fernet_key = key
        self._fernet = Fernet(key)

    def encrypt_data(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data using Fernet symmetric encryption."""
        if self._fernet is None:
            raise ValueError("Encryption key not set. Call set_encryption_key() first.")

        if isinstance(data, str):
            data = data.encode('utf-8')

        return self._fernet.encrypt(data)

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using Fernet symmetric encryption."""
        if self._fernet is None:
            raise ValueError("Encryption key not set. Call set_encryption_key() first.")

        return self._fernet.decrypt(encrypted_data)

    def secure_hash(self, data: Union[str, bytes], algorithm: str = 'sha256') -> str:
        """Generate secure hash using specified algorithm."""
        if isinstance(data, str):
            data = data.encode('utf-8')

        # Use cryptography's hashing instead of hashlib for consistency
        if algorithm.lower() == 'sha256':
            digest = hashes.Hash(hashes.SHA256())
        elif algorithm.lower() == 'sha512':
            digest = hashes.Hash(hashes.SHA512())
        elif algorithm.lower() == 'md5':
            # MD5 is deprecated but included for legacy compatibility
            # Prefer SHA256 for new implementations
            digest = hashes.Hash(hashes.MD5())
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        digest.update(data)
        return digest.finalize().hex()

    def secure_hmac(self, key: bytes, data: Union[str, bytes], algorithm: str = 'sha256') -> str:
        """Generate HMAC using secure implementation."""
        if isinstance(data, str):
            data = data.encode('utf-8')

        if algorithm.lower() == 'sha256':
            return hmac.new(key, data, hashlib.sha256).hexdigest()
        elif algorithm.lower() == 'sha512':
            return hmac.new(key, data, hashlib.sha512).hexdigest()
        else:
            raise ValueError(f"Unsupported HMAC algorithm: {algorithm}")

    def derive_key_pbkdf2(self, password: Union[str, bytes], salt: bytes,
                         iterations: int = 100000, key_length: int = 32) -> bytes:
        """Derive key from password using PBKDF2."""
        if isinstance(password, str):
            password = password.encode('utf-8')

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            iterations=iterations,
        )
        return kdf.derive(password)

    def derive_key_scrypt(self, password: Union[str, bytes], salt: bytes,
                         n: int = 2**14, r: int = 8, p: int = 1, key_length: int = 32) -> bytes:
        """Derive key from password using Scrypt (more secure than PBKDF2)."""
        if isinstance(password, str):
            password = password.encode('utf-8')

        kdf = Scrypt(
            length=key_length,
            salt=salt,
            n=n,
            r=r,
            p=p,
        )
        return kdf.derive(password)

    def generate_salt(self, length: int = 16) -> bytes:
        """Generate cryptographically secure random salt."""
        return secrets.token_bytes(length)

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        return secrets.token_hex(length)

    def constant_time_compare(self, a: Union[str, bytes], b: Union[str, bytes]) -> bool:
        """Constant-time comparison to prevent timing attacks."""
        if isinstance(a, str):
            a = a.encode('utf-8')
        if isinstance(b, str):
            b = b.encode('utf-8')

        return hmac.compare_digest(a, b)

    def generate_rsa_keypair(self, key_size: int = 2048) -> tuple[bytes, bytes]:
        """Generate RSA public/private key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_pem, public_pem

    def rsa_encrypt(self, public_key_pem: bytes, data: bytes) -> bytes:
        """Encrypt data using RSA public key."""
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

        public_key = serialization.load_pem_public_key(public_key_pem)
        if not isinstance(public_key, RSAPublicKey):
            raise ValueError("Invalid RSA public key")

        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted

    def rsa_decrypt(self, private_key_pem: bytes, encrypted_data: bytes) -> bytes:
        """Decrypt data using RSA private key."""
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
        )
        if not isinstance(private_key, RSAPrivateKey):
            raise ValueError("Invalid RSA private key")

        decrypted = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted

    def aes_encrypt(self, key: bytes, plaintext: bytes,
                   associated_data: bytes | None = None) -> tuple[bytes, bytes, bytes]:
        """
        AES-GCM encryption (authenticated encryption).
        Returns: (ciphertext, nonce, tag)
        """
        # Generate a random 96-bit IV for GCM
        nonce = os.urandom(12)

        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        encryptor = cipher.encryptor()

        # Add associated data if provided
        if associated_data:
            encryptor.authenticate_additional_data(associated_data)

        # Encrypt and finalize
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        return ciphertext, nonce, encryptor.tag

    def aes_decrypt(self, key: bytes, ciphertext: bytes, nonce: bytes, tag: bytes,
                   associated_data: bytes | None = None) -> bytes:
        """
        AES-GCM decryption (authenticated decryption).
        """
        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()

        # Add associated data if provided
        if associated_data:
            decryptor.authenticate_additional_data(associated_data)

        # Decrypt and verify
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        return plaintext


# Global instance for easy access
secure_crypto = SecureCrypto()


def secure_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute secure hash of a file using the cryptography library.
    Replacement for manual hashlib implementations.
    """
    if algorithm.lower() == 'sha256':
        digest = hashes.Hash(hashes.SHA256())
    elif algorithm.lower() == 'sha512':
        digest = hashes.Hash(hashes.SHA512())
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                digest.update(chunk)
        return digest.finalize().hex()
    except Exception as e:
        raise RuntimeError(f"Failed to hash file {file_path}: {e}") from e


def legacy_hashlib_sha256(data: Union[str, bytes]) -> str:
    """
    Drop-in replacement for hashlib.sha256().hexdigest()
    Maintains compatibility while using cryptography library.
    """
    return secure_crypto.secure_hash(data, 'sha256')


def legacy_hashlib_md5(data: Union[str, bytes]) -> str:
    """
    Drop-in replacement for hashlib.md5().hexdigest()
    Maintains compatibility while using cryptography library.
    Note: MD5 is deprecated and should be replaced with SHA256 when possible.
    """
    return secure_crypto.secure_hash(data, 'md5')


# Convenience functions for common operations
def generate_api_key() -> str:
    """Generate a secure API key."""
    return secure_crypto.generate_secure_token(32)


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, bytes]:
    """
    Hash a password using secure Scrypt algorithm.
    Returns: (hashed_password_hex, salt)
    """
    if salt is None:
        salt = secure_crypto.generate_salt()

    key = secure_crypto.derive_key_scrypt(password, salt)
    return key.hex(), salt


def verify_password(password: str, hashed_password: str, salt: bytes) -> bool:
    """Verify a password against its hash."""
    key = secure_crypto.derive_key_scrypt(password, salt)
    return secure_crypto.constant_time_compare(key.hex(), hashed_password)
