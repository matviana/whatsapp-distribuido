import socket
import threading
import json
import database

# Garante que as tabelas do banco existam antes do servidor iniciar
database.criar_tabelas()

HOST = '0.0.0.0'  # Aceita conexões de qualquer IP da rede
PORT = 12345      # Porta onde o servidor ficará escutando

# Armazena os clientes conectados: telefone -> socket
clients = {}

# Armazena os nomes dos usuários: telefone -> nome
users = {}

# Lock para evitar problemas de concorrência ao acessar clients/users
clients_lock = threading.Lock()


def handle_client(conn, addr):
    print(f"[NOVA CONEXÃO] {addr}")

    telefone = None

    try:
        # Recebe os dados iniciais do cliente (formato: telefone|nome)
        dados = conn.recv(1024).decode().strip()
        telefone, nome = dados.split("|")

        # Remove possíveis espaços extras
        telefone = telefone.strip()
        nome = nome.strip()

        database.cadastrar_usuario(telefone, nome)

        with clients_lock:
            clients[telefone] = conn
            users[telefone] = nome

        print(f"[USUÁRIO CONECTADO] {nome} ({telefone})")

        # Busca mensagens que foram enviadas enquanto o usuário estava offline
        pendentes = database.buscar_pendentes(telefone)

        for msg in pendentes:
            try:
                # Adiciona o nome do remetente à mensagem
                msg["nome"] = database.buscar_nome(msg["de"]) or msg["de"]

                # Envia a mensagem pendente para o cliente
                conn.send(json.dumps(msg).encode())

                # Atualiza o status para ENTREGUE no banco
                database.atualizar_status(msg["id"], "ENTREGUE")

                # Se o remetente ainda estiver online, envia confirmação
                if msg["de"] in clients:
                    confirmacao = {
                        "tipo": "status",
                        "id": msg["id"],
                        "status": "ENTREGUE"
                    }
                    clients[msg["de"]].send(json.dumps(confirmacao).encode())

                print(f"[PENDENTE ENTREGUE] {msg['de']} -> {telefone}")

            except:
                # Evita que erro em uma mensagem interrompa o processamento das outras
                pass

        # Loop principal que mantém a conexão com o cliente ativa
        while True:
            msg = conn.recv(1024).decode()

            # Se não receber nada, o cliente desconectou
            if not msg:
                break

            # Converte a mensagem recebida (JSON) para dicionário
            data = json.loads(msg)

            # Remove espaços no campo destinatário (evita erro de comparação)
            if "para" in data:
                data["para"] = data["para"].strip()

            
            # envio de mensagem
            
            if data["tipo"] == "mensagem":
                destinatario = data["para"]

                
                # Verifica se o destinatário existe no cadastro
                if not database.usuario_existe(destinatario):

                    confirmacao = {
                        "tipo": "status",
                        "id": data["id"],
                        "status": "USUARIO_NAO_CADASTRADO"
        }

                    clients[telefone].send(json.dumps(confirmacao).encode())

                    print(f"[ENVIO BLOQUEADO] Usuário {destinatario} não cadastrado")

                    continue

                data["status"] = "ENVIADA"

                # Adiciona o nome do remetente
                data["nome"] = users.get(telefone, telefone)

                # Salva a mensagem no banco
                database.salvar_mensagem(data)

                with clients_lock:
                    # Logs de debug para verificar problemas de entrega
                    print(f"[DEBUG] Destinatário: '{destinatario}'")
                    print(f"[DEBUG] Clientes: {list(clients.keys())}")

                    # Se o destinatário estiver online
                    if destinatario in clients:
                        data["status"] = "ENTREGUE"

                        # Envia a mensagem ao destinatário
                        clients[destinatario].send(json.dumps(data).encode())

                        # Atualiza o status no banco
                        database.atualizar_status(data["id"], "ENTREGUE")

                        # Confirma para o remetente que foi entregue
                        confirmacao = {
                            "tipo": "status",
                            "id": data["id"],
                            "status": "ENTREGUE"
                        }
                        clients[telefone].send(json.dumps(confirmacao).encode())

                        print(f"[ENTREGUE] {telefone} -> {destinatario}")

                    else:
                        # Se destinatário estiver offline, mantém como ENVIADA
                        confirmacao = {
                            "tipo": "status",
                            "id": data["id"],
                            "status": "ENVIADA"
                        }
                        clients[telefone].send(json.dumps(confirmacao).encode())

                        print(f"[OFFLINE] {destinatario}")

            
            # CONFIRMAÇÃO DE LEITURA
            
            elif data["tipo"] == "lido":
                id_msg = data["id"]

                # Atualiza status para LIDO no banco
                database.atualizar_status(id_msg, "LIDO")

                # Descobre quem enviou a mensagem originalmente
                remetente = database.buscar_remetente(id_msg)

                # Se o remetente estiver online, envia confirmação
                if remetente and remetente in clients:
                    confirmacao = {
                        "tipo": "status",
                        "id": id_msg,
                        "status": "LIDO"
                    }
                    clients[remetente].send(json.dumps(confirmacao).encode())

                print(f"[LIDO] Mensagem {id_msg}")

            
            # HISTÓRICO DE CONVERSA
            
            elif data["tipo"] == "historico":
                outro = data["com"].strip()

                # Busca todas mensagens entre os dois usuários
                conversa = database.buscar_conversa(telefone, outro)

                # Adiciona nome do remetente em cada mensagem
                for msg in conversa:
                    msg["nome"] = database.buscar_nome(msg["de"]) or msg["de"]

                # Envia o histórico para o cliente
                resposta = {
                    "tipo": "historico",
                    "mensagens": conversa
                }

                conn.send(json.dumps(resposta).encode())

                print(f"[HISTÓRICO] {telefone} com {outro}")

    except Exception as e:
        print(f"[ERRO] {e}")

    finally:
        # Executado quando o cliente desconecta
        print(f"[DESCONECTADO] {addr}")
        conn.close()

        # Remove o cliente das estruturas
        with clients_lock:
            if telefone in clients:
                del clients[telefone]
                del users[telefone]


def start_server():
    # Cria socket TCP
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Associa o servidor ao IP e porta definidos
    server.bind((HOST, PORT))

    # Coloca o servidor em modo de escuta
    server.listen()

    print(f"[SERVIDOR RODANDO] Porta {PORT}")

    # Loop principal para aceitar novas conexões
    while True:
        conn, addr = server.accept()

        # Cria uma thread para cada cliente conectado
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


# Inicializa o servidor
start_server()