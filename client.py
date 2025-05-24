import socket
import base64

# Configurações
BROKER_HOST = 'localhost'
BROKER_PORT = 8888
CLIENT_CERT_PATH = 'certs/client_cert.pem'

def carregar_certificado_base64(path):
    with open(path, 'rb') as cert_file:
        cert_bytes = cert_file.read()
        cert_b64 = base64.b64encode(cert_bytes).decode()
        return cert_b64

def conectar_ao_broker():
    # Conecta ao broker via TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((BROKER_HOST, BROKER_PORT))
        print("[+] Conectado ao broker")

        # Envia o comando AUTH:<certificado>
        cert_b64 = carregar_certificado_base64(CLIENT_CERT_PATH)
        comando_auth = f'AUTH:{cert_b64}\n'
        s.sendall(comando_auth.encode())
        print("[>] Enviado comando AUTH")

        # Aguarda resposta do broker
        resposta = s.recv(4096).decode()
        print(f"[<] Resposta do broker: {resposta.strip()}")

if __name__ == "__main__":
    conectar_ao_broker()
