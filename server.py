import socket
import threading

HOST = '0.0.0.0'
PORT = 12345

clients = {}  # telefone -> socket

import json

def handle_client(conn, addr):
    print(f"[NOVA CONEXÃO] {addr}")

    telefone = None

    try:
        telefone = conn.recv(1024).decode()
        clients[telefone] = conn

        print(f"[USUÁRIO CONECTADO] {telefone}")

        while True:
            msg = conn.recv(1024).decode()

            if not msg:
                break

            data = json.loads(msg)

            if data["tipo"] == "mensagem":
                destinatario = data["para"]

                if destinatario in clients:
                    clients[destinatario].send(msg.encode())
                    print(f"[ENTREGUE] {telefone} -> {destinatario}")
                else:
                    print(f"[OFFLINE] {destinatario}")

    except Exception as e:
        print(f"[ERRO] {e}")

    finally:
        print(f"[DESCONECTADO] {addr}")
        conn.close()
        if telefone in clients:
            del clients[telefone]
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[SERVIDOR RODANDO] Porta {PORT}")

    while True:
        conn, addr = server.accept()

        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

start_server()