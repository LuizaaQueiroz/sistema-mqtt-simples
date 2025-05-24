from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding
import os, base64

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

def criptografar_aes(msg, chave):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(chave), modes.CFB(iv))
    encryptor = cipher.encryptor()
    return iv + encryptor.update(msg.encode()) + encryptor.finalize()

def descriptografar_aes(msg_cript, chave):
    iv = msg_cript[:16]
    conteudo = msg_cript[16:]
    cipher = Cipher(algorithms.AES(chave), modes.CFB(iv))
    decryptor = cipher.decryptor()
    return decryptor.update(conteudo).decode()

def carregar_chave_publica(path):
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read(), backend=default_backend())

def carregar_chave_privada(path):
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

def criptografar_rsa(chave_simetrica, chave_publica):
    return chave_publica.encrypt(
        chave_simetrica,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def descriptografar_rsa(chave_criptografada, chave_privada):
    return chave_privada.decrypt(
        chave_criptografada,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def gerar_chave_aes():
    return os.urandom(32)  
