import socket
import threading
from utils.crypto_utils import load_cert_from_base64, load_ca_cert, verify_certificate
                        
def handle_client(conn, addr):
    print(f"[+] Conexão de {addr}")

    try:
        # Espera o cliente enviar AUTH
        data = conn.recv(4096).decode()
        if data.startswith("AUTH:"):
            cert_b64 = data.split("AUTH:")[1]
            client_cert = load_cert_from_base64(cert_b64)
            ca_cert = load_ca_cert()

            if verify_certificate(client_cert, ca_cert):
                conn.send(b"AUTH_OK\n")
                print(f"[+] Cliente autenticado: {client_cert.subject}")
                # Aqui podemos guardar a identidade do cliente para uso futuro
            else:
                conn.send(b"AUTH_FAIL\n")
                conn.close()
                return
        else:
            conn.send(b"ERRO: Primeiro comando deve ser AUTH\n")
            conn.close()
            return

        # Aqui segue para SUBSCRIBE ou PUBLISH...
        while True:
            msg = conn.recv(4096).decode()
            print(f"[RECEBIDO] {msg}")

    except Exception as e:
        print(f"[ERRO] Falha com {addr}: {e}")
        conn.close()
