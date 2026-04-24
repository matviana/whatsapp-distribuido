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

            
            if data["tipo"] == "mensagem":
                nome = data.get("nome", data["de"])
                print(f"\n[{nome}] {data['conteudo']}")

                
                confirmacao = {
                    "tipo": "lido",
                    "id": data["id"]
                }
                client.send(json.dumps(confirmacao).encode())

            
            elif data["tipo"] == "status":
                print(f"[STATUS] Mensagem {data['id']} -> {data['status']}")

            
            elif data["tipo"] == "historico":
                print("\n--- HISTÓRICO ---")
                for msg in data["mensagens"]:
                    nome = msg.get("nome", msg["de"])
                    print(f"[{nome}] {msg['conteudo']}")
                print("-----------------\n")

        except:
            print("[DESCONECTADO DO SERVIDOR]")
            client.close()
            break


def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    telefone = input("Digite seu telefone: ").strip()
    nome = input("Digite seu nome: ").strip()

    
    client.send(f"{telefone}|{nome}".encode())

    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    print("\nDigite mensagens normalmente ou use:")
    print("/historico <telefone>\n")

    while True:
        entrada = input()

        
        if entrada.startswith("/historico"):
            try:
                _, destino = entrada.split()

                requisicao = {
                    "tipo": "historico",
                    "com": destino
                }

                client.send(json.dumps(requisicao).encode())

            except:
                print("Uso correto: /historico 222")

        
        else:
            para = input("Enviar para (telefone): ")

            mensagem = {
                "tipo": "mensagem",
                "id": str(time.time()),
                "de": telefone,
                "para": para,
                "conteudo": entrada,
                "status": "ENVIADA"
            }

            client.send(json.dumps(mensagem).encode())


start_client()