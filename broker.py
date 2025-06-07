# ============================
# Arquivo: broker.py
# ============================
import socket
import threading
import json
import os

BROKER_HOST = '127.0.0.1'
BROKER_PORT = 1883

clientes_conectados = {}   # chave: id_cliente, valor: socket
subscricoes = {}           # chave: topico, valor: lista de id_cliente

# Certifique-se de que o diretório para chaves existe
os.makedirs("chaves", exist_ok=True)

def enviar_mensagem(conn, topico, mensagem):
    pacote = {
        "tipo": "mensagem",
        "topico": topico,
        "mensagem": mensagem
    }
    conn.send(json.dumps(pacote).encode())

def tratar_cliente(conn, addr):
    try:
        print(f"[+] Conexao de {addr}")

        dados_iniciais = conn.recv(4096).decode()
        print("[RECEBIDO DO CLIENTE]", dados_iniciais)
        pacote = json.loads(dados_iniciais)

        if pacote['tipo'] == 'autenticacao':
            id_cliente = pacote['id']
            chave_publica = pacote.get('chave_publica', '')

            # Salva chave pública do cliente
            if chave_publica:
                with open(f"chaves/{id_cliente}.pem", "w") as f:
                    f.write(chave_publica)
                print(f"[✓] Chave de {id_cliente} salva em chaves/{id_cliente}.pem")

            print(f"[✓] Cliente {id_cliente} conectado")
            clientes_conectados[id_cliente] = conn
            conn.send(b"AUTENTICADO")

        while True:
            dados = conn.recv(4096)
            if not dados:
                break

            pacote = json.loads(dados.decode())
            tipo = pacote.get('tipo')
            id_cliente = pacote.get('id')

            if tipo == 'publicar':
                topico = pacote['topico']
                payload = pacote['mensagem']

                for sub_id in subscricoes.get(topico, []):
                    if sub_id != id_cliente and sub_id in clientes_conectados:
                        enviar_mensagem(clientes_conectados[sub_id], topico, payload)

            elif tipo == 'inscrever':
                topico = pacote['topico']
                subscricoes.setdefault(topico, []).append(id_cliente)
                print(f"[+] {id_cliente} inscrito em {topico}")

    except Exception as e:
        print(f"[!] Erro com cliente {addr}: {e}")
    finally:
        conn.close()

def iniciar_broker():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((BROKER_HOST, BROKER_PORT))
    servidor.listen(5)
    print(f"[*] Broker ouvindo em {BROKER_HOST}:{BROKER_PORT}")

    while True:
        conn, addr = servidor.accept()
        threading.Thread(target=tratar_cliente, args=(conn, addr)).start()

if __name__ == '__main__':
    iniciar_broker()
