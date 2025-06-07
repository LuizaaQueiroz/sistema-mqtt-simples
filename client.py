import socket
import base64
import threading
import json
import os

# Configurações
BROKER_HOST = 'localhost'
BROKER_PORT = 1883
CHAVE_PUB_PATH = 'certs/client_pub.pem'

class ClienteWeb:
    def __init__(self):
        self.socket = None
        self.mensagens = []
        self.conectado = False
        self.nome_cliente = ""

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
            except:
                break

    def conectar(self, nome_cliente):
        try:
            self.nome_cliente = nome_cliente
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((BROKER_HOST, BROKER_PORT))

            print("[⚠️] Verificação de certificado ignorada temporariamente.")

            # Envia identificador + chave pública
            with open(CHAVE_PUB_PATH, 'rb') as f:
                chave_pub_pem = f.read().decode()

            pacote_auth = json.dumps({
                "tipo": "autenticacao",
                "id": self.nome_cliente,
                "chave_publica": chave_pub_pem
            })
            self.socket.send(pacote_auth.encode())

            resposta = self.socket.recv(1024).decode()
            if resposta.strip() != "AUTENTICADO":
                return False, "Broker recusou autenticação do cliente."

            self.conectado = True
            threading.Thread(target=self.receber_mensagens, daemon=True).start()
            return True, "Conectado com sucesso ao broker."

        except Exception as e:
            return False, f"Erro ao conectar: {e}"

    def enviar_sub(self, topico):
        if self.conectado:
            pacote = json.dumps({"tipo": "inscrever", "topico": topico, "id": self.nome_cliente})
            self.socket.send(pacote.encode())

    def enviar_pub(self, topico, mensagem):
        if self.conectado:
            try:
                pacote = json.dumps({
                    "tipo": "publicar",
                    "topico": topico,
                    "mensagem": mensagem,
                    "id": self.nome_cliente
                })
                self.socket.send(pacote.encode())
            except Exception as e:
                raise Exception("Erro ao enviar mensagem: " + str(e))