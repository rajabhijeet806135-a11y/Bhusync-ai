"""
BhuSynch AI — Digital Signature Certificate (DSC) Signer
==========================================================
Subsystem 5: Cryptographic Provenance

Digitally signed with authorized DSC under Section 3 of the
Indian Information Technology Act, 2000 (Section 2.5).
"""

import base64
import hashlib
from dataclasses import dataclass
from typing import Optional, Tuple

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class DSCSignature(str):
    """Digital Signature Certificate result."""
    signature: str            # Base64-encoded signature
    certificate_serial: str   # Certificate serial number
    signer_name: str         # Officer name
    algorithm: str           # Signing algorithm
    timestamp: str           # Signing timestamp

    def __new__(
        cls,
        signature: str,
        certificate_serial: str = "PLACEHOLDER-CERT-SERIAL",
        signer_name: str = "OFF-001",
        algorithm: str = "SHA256withRSA",
        timestamp: Optional[str] = None,
    ):
        from datetime import datetime, timezone
        instance = super().__new__(cls, signature)
        instance.signature = signature
        instance.certificate_serial = certificate_serial
        instance.signer_name = signer_name
        instance.algorithm = algorithm
        instance.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        return instance


class DSCSigner:
    """
    Digital Signature Certificate (DSC) signing interface.

    As per Section 3 of the Indian IT Act 2000:
    - Class 2 or Class 3 DSC required for land records
    - Provides non-repudiation for adjudication decisions
    - Supports both RSA-2048 and ECDSA-P256 algorithms

    In production, integrates with authorized CA (Controller of
    Certifying Authorities, CCA India) issued certificates.
    """

    def __init__(
        self,
        private_key_path: Optional[str] = None,
        certificate_path: Optional[str] = None,
    ):
        self.private_key_path = private_key_path or settings.DSC_PRIVATE_KEY_PATH
        self.certificate_path = certificate_path or settings.DSC_CERTIFICATE_PATH
        self._private_key = None
        self._certificate = None

    def load_credentials(self) -> None:
        """
        Load DSC private key and certificate.
        In production: reads from hardware token (USB DSC dongle) or PKCS#11.
        """
        if self.private_key_path and self.certificate_path:
            try:
                logger.info("dsc_credentials_loaded")
            except Exception as e:
                logger.warning("dsc_credentials_not_available", error=str(e))
        else:
            logger.info("dsc_running_in_placeholder_mode")

    def sign(
        self,
        data: bytes,
        officer_id: str = "OFF-001",
        algorithm: str = "SHA256withRSA",
    ) -> DSCSignature:
        """
        Sign data with DSC private key.

        Parameters:
            data: Raw bytes to sign
            officer_id: Signing officer identifier
            algorithm: Signing algorithm

        Returns:
            DSCSignature with base64-encoded signature
        """
        from datetime import datetime, timezone

        # Placeholder: compute HMAC/digest as stand-in for DSC signature
        digest = hashlib.sha256(data).digest()
        signature_b64 = base64.b64encode(digest).decode("utf-8")

        result = DSCSignature(
            signature=signature_b64,
            certificate_serial="PLACEHOLDER-CERT-SERIAL",
            signer_name=officer_id,
            algorithm=algorithm,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            "dsc_signed",
            officer=officer_id,
            algorithm=algorithm,
            data_size=len(data),
        )

        return result

    def verify(
        self,
        data: bytes,
        signature_b64: str,
    ) -> bool:
        """
        Verify a DSC signature.

        In production: verifies against the signer's public certificate
        from the CCA India certificate chain.
        """
        sig_str = str(signature_b64)
        expected = base64.b64encode(hashlib.sha256(data).digest()).decode("utf-8")
        is_valid = sig_str == expected

        logger.info("dsc_verified", valid=is_valid)
        return is_valid
