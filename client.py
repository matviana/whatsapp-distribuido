import socket
import threading
import json

HOST = '127.0.0.1'
PORT = 12345

def receive_messages(client):
    while True:
        try:
            msg = client.recv(1024).decode()
            data = json.loads(msg)

            print(f"\n[{data['de']}] {data['conteudo']}")

        except:
            print("[DESCONECTADO DO SERVIDOR]")
            client.close()
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    telefone = input("Digite seu telefone: ")
    client.send(telefone.encode())

    threading.Thread(target=receive_messages, args=(client,)).start()

    while True:
        para = input("Enviar para (telefone): ")
        conteudo = input("Mensagem: ")

        mensagem = {
            "tipo": "mensagem",
            "de": telefone,
            "para": para,
            "conteudo": conteudo
    }

        client.send(json.dumps(mensagem).encode())
        
start_client()