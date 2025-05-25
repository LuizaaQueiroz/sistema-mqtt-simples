import socket
import threading
import base64

from utils.crypto_utils import (
    load_cert_from_base64,
    load_ca_cert,
    verify_certificate,
    carregar_chave_privada,
    descriptografar_rsa
)

from cryptography.x509.oid import NameOID

# Estruturas de dados globais
topicos = {}           # {"chat": [conn1, conn2], ...}
clientes_aes = {}      # {conn: chave_aes}
clientes_nomes = {}    # {conn: nome_cliente (CN do certificado)}


def handle_client(conn, addr):
    print(f"[+] Conexão de {addr}")

    try:
        # 1. Autenticação: espera AUTH:<certificado em base64>
        data = conn.recv(4096).decode()
        if data.startswith("AUTH:"):
            cert_b64 = data.split("AUTH:")[1]
            client_cert = load_cert_from_base64(cert_b64)
            ca_cert = load_ca_cert()

            if verify_certificate(client_cert, ca_cert):
                conn.send("AUTH_OK\n".encode)
                nome_cliente = client_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                clientes_nomes[conn] = nome_cliente  # salva nome para rastrear
                print(f"[+] Cliente autenticado: {nome_cliente}")
            else:
                conn.send("AUTH_FAIL\n".encode)
                conn.close()
                return
        else:
            conn.send("ERRO: Primeiro comando deve ser AUTH\n".encode)
            conn.close()
            return

        # 2. Recebe a chave AES criptografada via RSA
        data = conn.recv(4096).decode()
        if data.startswith("KEY:"):
            chave_cripto = base64.b64decode(data[4:])
            chave_privada = carregar_chave_privada("certs/broker_key.pem")
            chave_aes = descriptografar_rsa(chave_cripto, chave_privada)
            clientes_aes[conn] = chave_aes
            print(f"[+] Chave AES recebida de {clientes_nomes[conn]}")
        else:
            conn.send("ERRO: Esperado comando KEY após AUTH\n".encode())

            conn.close()
            return

        # 3. Espera comandos SUB:<topico> ou PUB:<topico>:<mensagem criptografada>
        while True:
            data = conn.recv(4096)
            if not data:
                break

            try:
                msg = data.decode(errors="ignore")
            except:
                msg = ""

            if msg.startswith("SUB:"):
                topico = msg.split("SUB:")[1].strip()
                topicos.setdefault(topico, []).append(conn)
                print(f"[Broker] {clientes_nomes[conn]} assinou o tópico '{topico}'")

            elif msg.startswith("PUB:"):
                try:
                    partes = msg.split(":", 2)
                    topico = partes[1]
                    payload = partes[2].encode()

                    print(f"[Broker] {clientes_nomes[conn]} publicou em '{topico}'")

                    for cliente in topicos.get(topico, []):
                        if cliente != conn:
                            cliente.send(f"MSG:{topico}:".encode() + payload)
                except Exception as e:
                    print("[ERRO] Falha ao processar PUB:", e)

    except Exception as e:
        print(f"[ERRO] Cliente {addr} desconectado: {e}")

    finally:
        if conn in clientes_nomes:
            print(f"[Broker] Desconectado: {clientes_nomes[conn]}")
            del clientes_nomes[conn]
        if conn in clientes_aes:
            del clientes_aes[conn]
        conn.close()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 8888))
    server.listen(5)
    print("[Broker] Aguardando conexões...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()


if __name__ == "__main__":
    main()
