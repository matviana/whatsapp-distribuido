import socket
import threading
import json
import database

database.criar_tabelas()

HOST = '0.0.0.0'
PORT = 12345

clients = {}  
clients_lock = threading.Lock()


def handle_client(conn, addr):
    print(f"[NOVA CONEXÃO] {addr}")

    telefone = None

    try:
        telefone = conn.recv(1024).decode()

        with clients_lock:
            clients[telefone] = conn

        print(f"[USUÁRIO CONECTADO] {telefone}")

        
        pendentes = database.buscar_pendentes(telefone)

        for msg in pendentes:
            try:
                conn.send(json.dumps(msg).encode())
                database.atualizar_status(msg["id"], "ENTREGUE")

                # avisar remetente que foi entregue
                if msg["de"] in clients:
                    confirmacao = {
                        "tipo": "status",
                        "id": msg["id"],
                        "status": "ENTREGUE"
                    }
                    clients[msg["de"]].send(json.dumps(confirmacao).encode())

                print(f"[PENDENTE ENTREGUE] {msg['de']} -> {telefone}")

            except:
                pass

        while True:
            msg = conn.recv(1024).decode()

            if not msg:
                break

            data = json.loads(msg)

            
            #  envio
            
            if data["tipo"] == "mensagem":
                destinatario = data["para"]

                data["status"] = "ENVIADA"

                
                database.salvar_mensagem(data)

                with clients_lock:
                    if destinatario in clients:
                        
                        data["status"] = "ENTREGUE"

                        
                        clients[destinatario].send(json.dumps(data).encode())

                        
                        database.atualizar_status(data["id"], "ENTREGUE")

                        
                        confirmacao = {
                            "tipo": "status",
                            "id": data["id"],
                            "status": "ENTREGUE"
                        }
                        clients[telefone].send(json.dumps(confirmacao).encode())

                        print(f"[ENTREGUE] {telefone} -> {destinatario}")

                    else:
                        
                        confirmacao = {
                            "tipo": "status",
                            "id": data["id"],
                            "status": "ENVIADA"
                        }
                        clients[telefone].send(json.dumps(confirmacao).encode())

                        print(f"[OFFLINE] {destinatario}")

            
            #  confirmação
            
            elif data["tipo"] == "lido":
                id_msg = data["id"]

                
                database.atualizar_status(id_msg, "LIDO")

                
                remetente = database.buscar_remetente(id_msg)

                if remetente and remetente in clients:
                    confirmacao = {
                        "tipo": "status",
                        "id": id_msg,
                        "status": "LIDO"
                    }

                    clients[remetente].send(json.dumps(confirmacao).encode())

                print(f"[LIDO] Mensagem {id_msg}")

    except Exception as e:
        print(f"[ERRO] {e}")

    finally:
        print(f"[DESCONECTADO] {addr}")
        conn.close()

        with clients_lock:
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