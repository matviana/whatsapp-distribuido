import socket
import threading
import json
import time

HOST = '127.0.0.1'
PORT = 12345

def receive_messages(client):
    while True:
        try:
            msg = client.recv(1024).decode()
            data = json.loads(msg)

            # =========================
            # 📩 MENSAGEM RECEBIDA
            # =========================
            if data["tipo"] == "mensagem":
                print(f"\n[{data['de']}] {data['conteudo']}")

                # envia confirmação de leitura
                confirmacao = {
                    "tipo": "lido",
                    "id": data["id"]
                }
                client.send(json.dumps(confirmacao).encode())

            # =========================
            # 🔄 STATUS DA MENSAGEM
            # =========================
            elif data["tipo"] == "status":
                print(f"[STATUS] Mensagem {data['id']} -> {data['status']}")

        except Exception as e:
            print("[DESCONECTADO DO SERVIDOR]")
            client.close()
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    telefone = input("Digite seu telefone: ")
    client.send(telefone.encode())

    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    while True:
        para = input("Enviar para (telefone): ")
        conteudo = input("Mensagem: ")

        mensagem = {
            "tipo": "mensagem",
            "id": str(time.time()),  # ID único
            "de": telefone,
            "para": para,
            "conteudo": conteudo,
            "status": "ENVIADA"
        }

        client.send(json.dumps(mensagem).encode())

start_client()