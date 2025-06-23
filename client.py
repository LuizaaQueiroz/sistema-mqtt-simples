import socket
import base64
import threading
import json
import os
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.exceptions import InvalidSignature

BROKER_HOST = 'localhost'
BROKER_PORT = 1883
CA_CERT_PATH = 'certs/ca_cert.cer'

class ClienteWeb:
    def __init__(self):
        self.socket = None
        self.mensagens = []
        self.conectado = False
        self.nome_cliente = ""
        self.pub_key_path = ""
        self.priv_key_path = ""

    def gerar_par_de_chaves(self):
        os.makedirs('certs/priv_keys', exist_ok=True)
        os.makedirs('certs/pub_keys', exist_ok=True)

        priv_path = f'certs/priv_keys/{self.nome_cliente}_priv.pem'
        pub_path = f'certs/pub_keys/{self.nome_cliente}_pub.pem'

        if os.path.exists(priv_path) and os.path.exists(pub_path):
            print(f"[✓] Chaves já existem para '{self.nome_cliente}'.")
        else:
            private_key = ec.generate_private_key(ec.SECP256R1())

            with open(priv_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            public_key = private_key.public_key()
            with open(pub_path, "wb") as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))

            print(f"[✓] Chaves geradas para '{self.nome_cliente}'.")

        self.priv_key_path = priv_path
        self.pub_key_path = pub_path

    def receber_mensagens(self):
        while True:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                pacote = json.loads(data.decode())
                if pacote.get("tipo") == "mensagem":
                    topico = pacote.get("topico")
                    mensagem = pacote.get("mensagem")
                    self.mensagens.append(f"[{topico}] {mensagem}")
            except Exception as e:
                print(f"[Erro recebendo mensagens]: {e}")
                break

    def verificar_certificado_broker(self, cert_bytes, ca_path):
        try:
            cert = x509.load_pem_x509_certificate(cert_bytes, default_backend())
            with open(ca_path, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())

            ca_public_key = ca_cert.public_key()

            if isinstance(ca_public_key, ec.EllipticCurvePublicKey):
                ca_public_key.verify(
                    cert.signature,
                    cert.tbs_certificate_bytes,
                    ec.ECDSA(cert.signature_hash_algorithm)
                )
            else:
                ca_public_key.verify(
                    cert.signature,
                    cert.tbs_certificate_bytes,
                    padding.PKCS1v15(),
                    cert.signature_hash_algorithm
                )

            return cert
        except Exception as e:
            raise Exception(f"Erro ao validar certificado: {e}")

    def conectar(self, nome_cliente):
        try:
            self.nome_cliente = nome_cliente
            self.gerar_par_de_chaves()

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((BROKER_HOST, BROKER_PORT))

            size_bytes = self.socket.recv(4)
            size = int.from_bytes(size_bytes, byteorder='big')
            broker_cert_pem = b""
            while len(broker_cert_pem) < size:
                broker_cert_pem += self.socket.recv(2048)

            with open("received_broker_cert.cer", "wb") as f:
                f.write(broker_cert_pem)

            try:
                self.verificar_certificado_broker(broker_cert_pem, CA_CERT_PATH)
            except Exception as e:
                return False, str(e)

            with open(self.pub_key_path, 'rb') as f:
                chave_pub_pem = f.read().decode()

            pacote_auth = json.dumps({
                "tipo": "autenticacao",
                "id": self.nome_cliente,
                "chave_publica": chave_pub_pem
            })
            self.socket.send(pacote_auth.encode())

            resposta = self.socket.recv(1024).decode()
            if resposta.strip() != "AUTENTICADO":
                return False, "Broker recusou a autenticação."

            self.conectado = True
            threading.Thread(target=self.receber_mensagens, daemon=True).start()
            return True, "Conectado com sucesso."

        except Exception as e:
            return False, f"Erro na conexão: {e}"

    def enviar_sub(self, topico):
        if self.conectado:
            pacote = json.dumps({
                "tipo": "inscrever",
                "topico": topico,
                "id": self.nome_cliente
            })
            self.socket.send(pacote.encode())

    def enviar_pub(self, topico, mensagem):
        if self.conectado:
            pacote = json.dumps({
                "tipo": "publicar",
                "topico": topico,
                "mensagem": mensagem,
                "id": self.nome_cliente
            })
            self.socket.send(pacote.encode())
