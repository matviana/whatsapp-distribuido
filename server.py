import socket
import threading
import json
import database

database.criar_tabelas()

HOST = '0.0.0.0'
PORT = 12345

clients = {}
users = {}
clients_lock = threading.Lock()


def handle_client(conn, addr):
    print(f"[NOVA CONEXÃO] {addr}")

    telefone = None

    try:
        
        dados = conn.recv(1024).decode().strip()
        telefone, nome = dados.split("|")

        telefone = telefone.strip()
        nome = nome.strip()

        with clients_lock:
            clients[telefone] = conn
            users[telefone] = nome

        print(f"[USUÁRIO CONECTADO] {nome} ({telefone})")

        
        pendentes = database.buscar_pendentes(telefone)

        for msg in pendentes:
            try:
                msg["nome"] = users.get(msg["de"], msg["de"])

                conn.send(json.dumps(msg).encode())
                database.atualizar_status(msg["id"], "ENTREGUE")

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

            #evita bug
            if "para" in data:
                data["para"] = data["para"].strip()

            
            if data["tipo"] == "mensagem":
                destinatario = data["para"]
                data["status"] = "ENVIADA"
                data["nome"] = users.get(telefone, telefone)

                database.salvar_mensagem(data)

                with clients_lock:
                    print(f"[DEBUG] Destinatário: '{destinatario}'")
                    print(f"[DEBUG] Clientes: {list(clients.keys())}")

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

            
            elif data["tipo"] == "historico":
                outro = data["com"].strip()

                conversa = database.buscar_conversa(telefone, outro)

                for msg in conversa:
                    msg["nome"] = users.get(msg["de"], msg["de"])

                resposta = {
                    "tipo": "historico",
                    "mensagens": conversa
                }

                conn.send(json.dumps(resposta).encode())

                print(f"[HISTÓRICO] {telefone} com {outro}")

    except Exception as e:
        print(f"[ERRO] {e}")

    finally:
        print(f"[DESCONECTADO] {addr}")
        conn.close()

        with clients_lock:
            if telefone in clients:
                del clients[telefone]
                del users[telefone]


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