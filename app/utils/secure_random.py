"""
Cryptographically secure random number generation.

Replaces insecure random.random() with secrets module for security-critical
operations like token generation, session IDs, etc.

Author: xanadOS Security Team
Date: 2025-12-17
Phase: 2 (HIGH severity - CWE-338 mitigation)
"""

import secrets
import string
from typing import Sequence


class SecureRandom:
    """
    Cryptographically secure random number generator.

    Uses secrets module instead of random module for all security-sensitive
    random number generation.

    DO NOT use random.random(), random.randint(), etc. for:
    - Tokens
    - Session IDs
    - Cryptographic keys
    - Password reset codes
    - API keys
    - Challenge responses

    Example:
        >>> rng = SecureRandom()
        >>> token = rng.token_hex(32)
        >>> session_id = rng.token_urlsafe(32)
    """

    @staticmethod
    def token_bytes(nbytes: int = 32) -> bytes:
        """
        Generate cryptographically strong random bytes.

        Args:
            nbytes: Number of bytes to generate

        Returns:
            Random bytes
        """
        return secrets.token_bytes(nbytes)

    @staticmethod
    def token_hex(nbytes: int = 32) -> str:
        """
        Generate cryptographically strong random hex string.

        Args:
            nbytes: Number of bytes (output will be 2x characters)

        Returns:
            Hex-encoded random string

        Example:
            >>> SecureRandom.token_hex(16)
            'a1b2c3d4e5f60708091a2b3c4d5e6f70'
        """
        return secrets.token_hex(nbytes)

    @staticmethod
    def token_urlsafe(nbytes: int = 32) -> str:
        """
        Generate URL-safe random string.

        Args:
            nbytes: Number of random bytes

        Returns:
            URL-safe random string

        Example:
            >>> SecureRandom.token_urlsafe(32)
            'Xq9Kv2Lm8Nw3Pz5Rt7Yu1Io0Qs4Wd6'
        """
        return secrets.token_urlsafe(nbytes)

    @staticmethod
    def randbelow(exclusive_upper_bound: int) -> int:
        """
        Generate random integer in [0, exclusive_upper_bound).

        Args:
            exclusive_upper_bound: Upper bound (exclusive)

        Returns:
            Random integer

        Example:
            >>> SecureRandom.randbelow(100)  # Random int from 0-99
            42
        """
        return secrets.randbelow(exclusive_upper_bound)

    @staticmethod
    def choice(sequence: Sequence) -> any:
        """
        Choose random element from sequence.

        Args:
            sequence: Non-empty sequence to choose from

        Returns:
            Random element

        Example:
            >>> SecureRandom.choice(['red', 'green', 'blue'])
            'green'
        """
        return secrets.choice(sequence)

    @staticmethod
    def generate_password(
        length: int = 16,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_special: bool = True,
    ) -> str:
        """
        Generate cryptographically secure random password.

        Args:
            length: Password length
            use_uppercase: Include uppercase letters
            use_lowercase: Include lowercase letters
            use_digits: Include digits
            use_special: Include special characters

        Returns:
            Random password

        Example:
            >>> SecureRandom.generate_password(20)
            'X9k#mP2vL@qR7wN4sT1!'
        """
        alphabet = ""
        if use_uppercase:
            alphabet += string.ascii_uppercase
        if use_lowercase:
            alphabet += string.ascii_lowercase
        if use_digits:
            alphabet += string.digits
        if use_special:
            alphabet += "!@#$%^&*()-_=+[]{}|;:,.<>?"

        if not alphabet:
            raise ValueError("At least one character type must be enabled")

        # Generate password ensuring at least one char from each enabled type
        password = []

        if use_uppercase:
            password.append(secrets.choice(string.ascii_uppercase))
        if use_lowercase:
            password.append(secrets.choice(string.ascii_lowercase))
        if use_digits:
            password.append(secrets.choice(string.digits))
        if use_special:
            password.append(secrets.choice("!@#$%^&*()-_=+[]{}|;:,.<>?"))

        # Fill remaining length
        for _ in range(length - len(password)):
            password.append(secrets.choice(alphabet))

        # Shuffle
        secrets.SystemRandom().shuffle(password)

        return "".join(password)

    @staticmethod
    def generate_session_id(length: int = 32) -> str:
        """
        Generate secure session ID.

        Args:
            length: Session ID length

        Returns:
            URL-safe session ID
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_api_key(prefix: str = "sk", length: int = 32) -> str:
        """
        Generate secure API key.

        Args:
            prefix: Key prefix (e.g., 'sk' for secret key)
            length: Random portion length

        Returns:
            API key in format: prefix_randomhex

        Example:
            >>> SecureRandom.generate_api_key('sk', 32)
            'sk_a1b2c3d4e5f60708091a2b3c4d5e6f70...'
        """
        return f"{prefix}_{secrets.token_hex(length)}"

    @staticmethod
    def generate_csrf_token() -> str:
        """
        Generate CSRF token for web forms.

        Returns:
            URL-safe CSRF token
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def compare_digest(a: str | bytes, b: str | bytes) -> bool:
        """
        Timing-attack resistant string comparison.

        Use this instead of == for comparing secrets.

        Args:
            a: First value
            b: Second value

        Returns:
            True if equal

        Example:
            >>> token = SecureRandom.token_hex(16)
            >>> SecureRandom.compare_digest(token, user_input)
        """
        return secrets.compare_digest(a, b)


# Convenience functions
def generate_token(nbytes: int = 32) -> str:
    """Generate secure random token."""
    return SecureRandom.token_hex(nbytes)


def generate_session_id() -> str:
    """Generate secure session ID."""
    return SecureRandom.generate_session_id()


def generate_api_key(prefix: str = "sk") -> str:
    """Generate secure API key."""
    return SecureRandom.generate_api_key(prefix)


def generate_csrf_token() -> str:
    """Generate CSRF token."""
    return SecureRandom.generate_csrf_token()


# Example usage
if __name__ == "__main__":
    rng = SecureRandom()

    print("Cryptographically Secure Random Generation Examples:\\n")

    print(f"Token (hex):        {rng.token_hex(16)}")
    print(f"Token (URL-safe):   {rng.token_urlsafe(16)}")
    print(f"Session ID:         {rng.generate_session_id()}")
    print(f"API Key:            {rng.generate_api_key('sk', 24)}")
    print(f"Password:           {rng.generate_password(20)}")
    print(f"CSRF Token:         {rng.generate_csrf_token()}")
    print(f"Random int (0-99):  {rng.randbelow(100)}")
    print(f"Random choice:      {rng.choice(['red', 'green', 'blue', 'yellow'])}")
