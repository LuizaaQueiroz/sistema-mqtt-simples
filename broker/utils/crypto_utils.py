from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

def load_cert(cert_bytes):
    return x509.load_pem_x509_certificate(cert_bytes, default_backend())

def verify_cert_signature(cert, ca_cert):
    try:
        ca_public_key = ca_cert.public_key()
        ca_public_key.verify(
            cert.signature,
            cert.tbs_certificate_bytes,
            cert.signature_hash_algorithm
        )
        return True
    except Exception as e:
        print("Erro na verificação do certificado:", e)
        return False
