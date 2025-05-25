import socket
import base64
import threading

from utils.crypto_utils import (
    carregar_chave_publica,
    gerar_chave_aes,
    criptografar_rsa,
    criptografar_aes,
    descriptografar_aes
)

# Configurações
BROKER_HOST = 'localhost'
BROKER_PORT = 8888
CLIENT_CERT_PATH = 'certs/client_cert.pem'
BROKER_CERT_PATH = 'certs/broker_cert.pem'

class ClienteWeb:
    def __init__(self):
        self.socket = None
        self.aes_key = None
        self.mensagens = []
        self.conectado = False

    def carregar_certificado_base64(self, path):
        with open(path, 'rb') as cert_file:
            return base64.b64encode(cert_file.read()).decode()

    def receber_mensagens(self):
        while True:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                prefixo_fim = data.find(b':') + 1
                if prefixo_fim <= 0:
                    continue
                prefixo = data[:prefixo_fim].decode(errors="ignore")
                payload = data[prefixo_fim:]
                msg = descriptografar_aes(payload, self.aes_key)
                self.mensagens.append(f"{prefixo.strip()} {msg}")
            except:
                break

    def conectar(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((BROKER_HOST, BROKER_PORT))

            # Envia AUTH
            cert_b64 = self.carregar_certificado_base64(CLIENT_CERT_PATH)
            self.socket.sendall(f"AUTH:{cert_b64}".encode())
            resposta = self.socket.recv(4096).decode()
            if resposta.strip() != "AUTH_OK":
                return False, "Falha na autenticação."

            # Envia KEY
            self.aes_key = gerar_chave_aes()
            chave_pub = carregar_chave_publica(BROKER_CERT_PATH)
            chave_aes_cripto = criptografar_rsa(self.aes_key, chave_pub)
            self.socket.sendall(f"KEY:{base64.b64encode(chave_aes_cripto).decode()}".encode())

            self.conectado = True
            threading.Thread(target=self.receber_mensagens, daemon=True).start()
            return True, "Autenticado com sucesso."

        except Exception as e:
            return False, f"Erro ao conectar: {e}"

    def enviar_sub(self, topico):
        if self.conectado:
            self.socket.send(f"SUB:{topico}".encode())

    def enviar_pub(self, topico, mensagem):
        if self.conectado:
            try:
                msg_cript = criptografar_aes(mensagem, self.aes_key)
                self.socket.send(f"PUB:{topico}:".encode() + msg_cript)
            except Exception as e:
                raise Exception("Erro ao criptografar ou enviar mensagem: " + str(e))
