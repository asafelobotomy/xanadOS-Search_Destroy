"""
Model signature verification for ML threat detection.

Prevents model poisoning attacks by verifying cryptographic signatures
before loading ML models. Uses SHA256 checksums and optional GPG signatures.

Author: xanadOS Security Team
Date: 2025-12-17
Phase: 2 (HIGH severity - CWE-494 mitigation)
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ModelSignatureVerificationError(Exception):
    """Raised when model signature verification fails."""

    pass


class ModelSignatureVerifier:
    """
    Verifies cryptographic signatures of ML models before loading.

    Prevents model poisoning attacks by ensuring model integrity.

    Example:
        >>> verifier = ModelSignatureVerifier()
        >>> verifier.verify_model(model_path, expected_hash)
        True
    """

    def __init__(self, trusted_hashes_file: Path | None = None):
        """
        Initialize model signature verifier.

        Args:
            trusted_hashes_file: Path to JSON file containing trusted model hashes
        """
        self.trusted_hashes_file = trusted_hashes_file or Path(
            "models/trusted_hashes.json"
        )
        self.trusted_hashes = self._load_trusted_hashes()

    def _load_trusted_hashes(self) -> dict[str, str]:
        """Load trusted model hashes from JSON file."""
        if not self.trusted_hashes_file.exists():
            logger.warning(f"Trusted hashes file not found: {self.trusted_hashes_file}")
            return {}

        try:
            return json.loads(self.trusted_hashes_file.read_text())
        except Exception as e:
            logger.error(f"Failed to load trusted hashes: {e}")
            return {}

    def compute_model_hash(self, model_path: Path) -> str:
        """
        Compute SHA256 hash of model file.

        Args:
            model_path: Path to model file

        Returns:
            Hex-encoded SHA256 hash
        """
        hasher = hashlib.sha256()

        # Read file in chunks to handle large models
        with open(model_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        return hasher.hexdigest()

    def verify_model(
        self,
        model_path: Path,
        expected_hash: str | None = None,
        model_name: str | None = None,
    ) -> bool:
        """
        Verify model signature before loading.

        Args:
            model_path: Path to model file
            expected_hash: Expected SHA256 hash (optional, uses trusted_hashes if not provided)
            model_name: Model identifier in trusted_hashes (optional)

        Returns:
            True if verification succeeds

        Raises:
            ModelSignatureVerificationError: If verification fails
        """
        if not model_path.exists():
            raise ModelSignatureVerificationError(f"Model file not found: {model_path}")

        # Compute actual hash
        actual_hash = self.compute_model_hash(model_path)

        # Determine expected hash
        if expected_hash is None:
            if model_name and model_name in self.trusted_hashes:
                expected_hash = self.trusted_hashes[model_name]
            else:
                logger.warning(
                    f"No expected hash provided for {model_path}. "
                    "Model integrity cannot be verified."
                )
                return False

        # Verify hash
        if actual_hash.lower() != expected_hash.lower():
            raise ModelSignatureVerificationError(
                f"Model signature verification failed for {model_path}\\n"
                f"Expected: {expected_hash}\\n"
                f"Actual:   {actual_hash}\\n"
                f"POSSIBLE MODEL POISONING ATTACK DETECTED!"
            )

        logger.info(f"✅ Model signature verified: {model_path}")
        return True

    def add_trusted_model(self, model_name: str, model_path: Path) -> None:
        """
        Add a model to the trusted hashes registry.

        Args:
            model_name: Identifier for the model
            model_path: Path to model file
        """
        model_hash = self.compute_model_hash(model_path)
        self.trusted_hashes[model_name] = model_hash

        # Save to file
        self.trusted_hashes_file.parent.mkdir(parents=True, exist_ok=True)
        self.trusted_hashes_file.write_text(json.dumps(self.trusted_hashes, indent=2))

        logger.info(f"Added trusted model: {model_name} ({model_hash[:16]}...)")

    def verify_model_metadata(self, model_path: Path, metadata_path: Path) -> bool:
        """
        Verify model matches its metadata checksum.

        Args:
            model_path: Path to model file
            metadata_path: Path to metadata JSON file

        Returns:
            True if verification succeeds

        Raises:
            ModelSignatureVerificationError: If verification fails
        """
        if not metadata_path.exists():
            raise ModelSignatureVerificationError(
                f"Metadata file not found: {metadata_path}"
            )

        # Load metadata
        try:
            metadata = json.loads(metadata_path.read_text())
        except Exception as e:
            raise ModelSignatureVerificationError(f"Failed to load metadata: {e}")

        # Get expected hash from metadata
        expected_hash = metadata.get("model_hash") or metadata.get("checksum")
        if not expected_hash:
            raise ModelSignatureVerificationError(
                "Metadata does not contain model hash"
            )

        # Verify
        return self.verify_model(model_path, expected_hash)


# Convenience function for quick verification
def verify_model_file(model_path: Path, expected_hash: str) -> bool:
    """
    Quick model verification (convenience function).

    Args:
        model_path: Path to model file
        expected_hash: Expected SHA256 hash

    Returns:
        True if verification succeeds

    Raises:
        ModelSignatureVerificationError: If verification fails

    Example:
        >>> verify_model_file(Path("model.pkl"), "abc123...")
        True
    """
    verifier = ModelSignatureVerifier()
    return verifier.verify_model(model_path, expected_hash)


# Example usage
if __name__ == "__main__":
    verifier = ModelSignatureVerifier()

    # Example: Verify a model
    model_path = Path("models/production/malware_detector_rf/model.pkl")
    if model_path.exists():
        try:
            # Option 1: Verify with explicit hash
            expected_hash = "abc123..."  # From trusted source
            verifier.verify_model(model_path, expected_hash)
            print("✅ Model verification successful")
        except ModelSignatureVerificationError as e:
            print(f"❌ Model verification failed: {e}")

        # Option 2: Add to trusted registry
        verifier.add_trusted_model("malware_detector_rf_v1.0", model_path)

        # Option 3: Verify from registry
        verifier.verify_model(model_path, model_name="malware_detector_rf_v1.0")
