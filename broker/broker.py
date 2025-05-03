import socket
import threading

clients = []
topics = {}

def handle_client(conn, addr):
    print(f"[+] Nova conexão de {addr}")
    # Aqui: autenticar cliente e processar comandos (AUTH, SUB, PUB)
    conn.close()

def start_broker():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 8888))
    server.listen(5)
    print("[*] Broker aguardando conexões...")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_broker()
