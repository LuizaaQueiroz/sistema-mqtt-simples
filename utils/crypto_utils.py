from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import os
import base64
from datetime import datetime

def gerar_par_chaves(cliente_nome, senha=None):
    os.makedirs('certs/priv_keys', exist_ok=True)
    os.makedirs('certs/pub_keys', exist_ok=True)
    priv_path = f'certs/priv_keys/{cliente_nome}_priv.pem'
    pub_path = f'certs/pub_keys/{cliente_nome}_pub.pem'
    if os.path.exists(priv_path) and os.path.exists(pub_path):
        print(f"[✓] Chaves já existentes para {cliente_nome}")
        return pub_path, priv_path
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    # Salvar chave privada
    with open(priv_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(senha.encode()) if senha else serialization.NoEncryption()
        ))
    # Salvar chave pública
    public_key = private_key.public_key()
    with open(pub_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    print(f"[✓] Par de chaves gerado para {cliente_nome}")
    return pub_path, priv_path

def load_cert_from_base64(cert_base64: str):
    try:
        cert_bytes = base64.b64decode(cert_base64)
        cert = x509.load_pem_x509_certificate(cert_bytes, default_backend())
        return cert
    except Exception as e:
        print(f"[ERRO] Falha ao carregar certificado Base64: {e}")
        raise

def load_ca_cert(path="certs/ca_cert.cer"):
    with open(path, "rb") as f:
        data = f.read()
        try:
            return x509.load_pem_x509_certificate(data, default_backend())
        except ValueError:
            return x509.load_der_x509_certificate(data, default_backend())

def verificar_certificado(cert, ca_cert):
    try:
        algorithm = cert.signature_hash_algorithm or hashes.SHA256()
        public_key = ca_cert.public_key()

        # Verificação adequada para RSA ou EC
        if isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                ec.ECDSA(algorithm)
            )
        else:
            from cryptography.hazmat.primitives.asymmetric import padding
            public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                algorithm
            )

        now = datetime.utcnow()
        if now < cert.not_valid_before or now > cert.not_valid_after:
            print("[ERRO] Certificado fora da validade")
            return False

        print("[DEBUG] Certificado verificado com sucesso")
        return True

    except Exception as e:
        print(f"[ERRO] Certificado inválido: {e}")
        return False


def criptografar_ec(chave_aes, chave_publica):
    try:
        ephemeral_private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        ephemeral_public_key = ephemeral_private_key.public_key()
        shared_key = ephemeral_private_key.exchange(ec.ECDH(), chave_publica)
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
            backend=default_backend()
        ).derive(shared_key)
        fernet_key = base64.b64encode(derived_key)
        cipher = Fernet(fernet_key)
        encrypted_aes_key = cipher.encrypt(chave_aes)
        return encrypted_aes_key, ephemeral_public_key
    except Exception as e:
        print(f"[ERRO] Falha ao criptografar com EC: {e}")
        raise

def descriptografar_ec(chave_aes_cript, ephemeral_public_key_pem, chave_privada):
    try:
        ephemeral_public_key = serialization.load_pem_public_key(
            ephemeral_public_key_pem.encode(), default_backend()
        )
        shared_key = chave_privada.exchange(ec.ECDH(), ephemeral_public_key)
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
            backend=default_backend()
        ).derive(shared_key)
        fernet_key = base64.b64encode(derived_key)
        cipher = Fernet(fernet_key)
        chave_aes = cipher.decrypt(bytes.fromhex(chave_aes_cript))
        return chave_aes
    except Exception as e:
        print(f"[ERRO] Falha ao descriptografar com EC: {e}")
        raise

def criptografar_aes(mensagem, chave):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(chave), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    msg_bytes = mensagem.encode() if isinstance(mensagem, str) else mensagem
    msg_cript = iv + encryptor.update(msg_bytes) + encryptor.finalize()
    return msg_cript

def descriptografar_aes(msg_cript, chave):
    try:
        iv = msg_cript[:16]
        conteudo = msg_cript[16:]
        cipher = Cipher(algorithms.AES(chave), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(conteudo) + decryptor.finalize()
        return decrypted.decode()
    except Exception as e:
        print(f"[ERRO] Falha ao descriptografar com AES: {e}")
        raise

def gerar_chave_aes():
    return os.urandom(32)

def carregar_certificado_broker(path="certs/broker_cert.cer"):
    with open(path, "rb") as f:
        data = f.read()
        try:
            cert = x509.load_pem_x509_certificate(data, default_backend())
        except ValueError:
            cert = x509.load_der_x509_certificate(data, default_backend())
            data = cert.public_bytes(serialization.Encoding.PEM)
        return base64.b64encode(data).decode()

def enviar_certificado_broker(conn):
    cert_base64 = carregar_certificado_broker()
    conn.send(cert_base64.encode())

def enviar_mensagem(conn, topico, mensagem):
    import json
    pacote = {
        "tipo": "mensagem",
        "topico": topico,
        "mensagem": mensagem
    }
    conn.send(json.dumps(pacote).encode())

def carregar_chave_privada_pem(path, senha=None):
    with open(path, "rb") as f:
        data = f.read()
        try:
            return serialization.load_pem_private_key(
                data,
                password=senha.encode() if senha else None,
                backend=default_backend()
            )
        except Exception as e:
            print(f"[ERRO] Falha ao carregar chave privada: {e}")
            raise

def carregar_chave_publica_pem(path):
    with open(path, "rb") as f:
        data = f.read()
        try:
            return serialization.load_pem_public_key(data, backend=default_backend())
        except Exception as e:
            print(f"[ERRO] Falha ao carregar chave pública: {e}")
            raise
