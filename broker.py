import socket
import threading
import json
import os
from datetime import datetime

BROKER_HOST = '127.0.0.1'
BROKER_PORT = 1883

clientes_conectados = {}        # id_cliente -> socket
subscricoes = {}                # topico -> lista de id_cliente
historico_topicos = {}          # topico -> lista de mensagens (strings)

TOPICOS_JSON = "json/topicos.json"
ADMINS_JSON = "json/admins.json"
PRIVACIDADE_JSON = "json/privacidade_topicos.json"
MEMBROS_JSON = "json/membros_topicos.json"

def carregar_json(caminho):
    if os.path.exists(caminho):
        with open(caminho, "r") as f:
            return json.load(f)
    return {}

def enviar_mensagem(conn, topico, mensagem):
    pacote = {
        "tipo": "mensagem",
        "topico": topico,
        "mensagem": mensagem
    }
    try:
        conn.send(json.dumps(pacote).encode())
    except:
        pass  # Cliente pode ter desconectado

def tratar_cliente(conn, addr):
    id_cliente = None
    try:
        print(f"[+] Conexão de {addr}")

        # Enviar certificado do broker
        with open("certs/broker_cert.cer", "rb") as f:
            cert_data = f.read()
            conn.send(len(cert_data).to_bytes(4, byteorder='big'))
            conn.send(cert_data)

        dados_iniciais = conn.recv(4096).decode()
        pacote = json.loads(dados_iniciais)

        if pacote['tipo'] == 'autenticacao':
            id_cliente = pacote['id']
            chave_publica = pacote.get('chave_publica', '').strip()
            chave_path = f"certs/pub_keys/{id_cliente}.pem"

            if os.path.exists(chave_path):
                with open(chave_path, 'r') as f:
                    chave_salva = f.read().strip()
                if chave_publica != chave_salva:
                    print(f"[!] Chave inválida para {id_cliente}.")
                    conn.send(b"FALHA_AUTENTICACAO")
                    conn.close()
                    return
            else:
                with open(chave_path, "w") as f:
                    f.write(chave_publica)
                print(f"[✓] Chave de {id_cliente} salva.")

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

                privacidade = carregar_json(PRIVACIDADE_JSON).get(topico, "publico")
                membros = carregar_json(MEMBROS_JSON).get(topico, [])
                admin_topico = carregar_json(ADMINS_JSON).get(topico, "")

                autorizado = False
                if privacidade == "publico":
                    autorizado = True
                elif privacidade == "privado":
                    if id_cliente == admin_topico or id_cliente in membros:
                        autorizado = True

                if autorizado:
                    horario = datetime.now().strftime('%H:%M')
                    mensagem_formatada = f"{id_cliente}: {payload} [{horario}]"

                    # ✅ Inscreve o cliente no tópico automaticamente se ainda não estiver
                    subscricoes.setdefault(topico, [])
                    if id_cliente not in subscricoes[topico]:
                        subscricoes[topico].append(id_cliente)

                    # ✅ Salva no histórico
                    historico_topicos.setdefault(topico, []).append(mensagem_formatada)

                    # ✅ Envia para todos os inscritos, inclusive o próprio cliente
                    for sub_id in subscricoes[topico]:
                        if sub_id in clientes_conectados:
                            enviar_mensagem(clientes_conectados[sub_id], topico, mensagem_formatada)

                    print(f"[{topico}] {mensagem_formatada}")
                else:
                    print(f"[!] {id_cliente} tentou publicar sem permissão no tópico {topico}.")

            elif tipo == 'inscrever':
                topico = pacote['topico']
                subscricoes.setdefault(topico, [])
                if id_cliente not in subscricoes[topico]:
                    subscricoes[topico].append(id_cliente)
                print(f"[+] {id_cliente} inscrito em {topico}")

                # Enviar histórico para o novo inscrito
                for msg in historico_topicos.get(topico, []):
                    enviar_mensagem(conn, topico, msg)

    except Exception as e:
        print(f"[!] Erro com cliente {addr}: {e}")
    finally:
        if id_cliente and id_cliente in clientes_conectados:
            del clientes_conectados[id_cliente]
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
