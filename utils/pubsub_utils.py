import json

def enviar_sub(cliente, topico):
    if cliente.conectado:
        try:
            pacote = json.dumps({
                "tipo": "inscrever",
                "topico": topico,
                "id": cliente.nome_cliente
            })
            cliente.socket.send(pacote.encode())
            print(f"[DEBUG] Inscrição enviada para o tópico {topico} por {cliente.nome_cliente}")
        except Exception as e:
            print(f"[ERRO] Falha ao inscrever no tópico {topico}: {e}")

def enviar_pub(cliente, topico, mensagem):
    if cliente.conectado:
        try:
            pacote = json.dumps({
                "tipo": "publicar",
                "topico": topico,
                "mensagem": mensagem,
                "id": cliente.nome_cliente
            })
            cliente.socket.send(pacote.encode())
            print(f"[DEBUG] Mensagem publicada para o tópico {topico} por {cliente.nome_cliente}: {mensagem[:50]}...")
        except Exception as e:
            print(f"[ERRO] Falha ao publicar no tópico {topico}: {e}")