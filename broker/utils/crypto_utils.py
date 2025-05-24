from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64

def load_cert_from_base64(cert_base64: str):
    cert_bytes = base64.b64decode(cert_base64)
    return x509.load_pem_x509_certificate(cert_bytes, default_backend())

def load_ca_cert(path="certs/ca_cert.pem"):
    with open(path, "rb") as f:
        return x509.load_pem_x509_certificate(f.read(), default_backend())

def verify_certificate(cert, ca_cert):
    try:
        ca_cert.public_key().verify(
            cert.signature,
            cert.tbs_certificate_bytes,
            cert.signature_hash_algorithm
        )
        return True
    except Exception as e:
        print("[ERRO] Certificado inválido:", e)
        return False
  