import socket
import threading
import json
import time

HOST = '127.0.0.1'  # Endereço
PORT = 12345        # Porta servidor

def receive_messages(client):
    # Função que roda em paralelo para receber mensagens do servidor
    while True:
        try:
            # Recebe mensagem do servidor
            msg = client.recv(1024).decode()
            data = json.loads(msg)

            
            # recebimento de mensagem
            
            if data["tipo"] == "mensagem":
                # Usa o nome se existir, senão usa o telefone
                nome = data.get("nome", data["de"])
                print(f"\n[{nome}] {data['conteudo']}")

                # Envia confirmação de leitura automaticamente
                confirmacao = {
                    "tipo": "lido",
                    "id": data["id"]
                }
                client.send(json.dumps(confirmacao).encode())

            
            # ATUALIZAÇÃO DE STATUS
            
            elif data["tipo"] == "status":
                print(f"[STATUS] Mensagem {data['id']} -> {data['status']}")

            
            # EXIBIÇÃO DE HISTÓRICO
            
            elif data["tipo"] == "historico":
                print("\n--- HISTÓRICO ---")
                for msg in data["mensagens"]:
                    nome = msg.get("nome", msg["de"])
                    print(f"[{nome}] {msg['conteudo']}")
                print("-----------------\n")

        except:
            # Caso perca conexão com o servidor
            print("[DESCONECTADO DO SERVIDOR]")
            client.close()
            break


def start_client():
    # Cria socket TCP
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Conecta ao servidor
    client.connect((HOST, PORT))

    # Identificação do usuário
    telefone = input("Digite seu telefone: ").strip()
    nome = input("Digite seu nome: ").strip()

    # Envia dados iniciais para o servidor (formato: telefone|nome)
    client.send(f"{telefone}|{nome}".encode())

    # Inicia thread para receber mensagens em paralelo
    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    print("\nDigite mensagens normalmente ou use:")
    print("/historico <telefone>\n")

    # Loop principal para envio de mensagens
    while True:
        entrada = input()

        
        # comando de histórico
        
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

        
        # envio de mensagem
        
        else:
            # Pergunta o destinatário
            para = input("Enviar para (telefone): ")

            # Monta a mensagem
            mensagem = {
                "tipo": "mensagem",
                "id": str(time.time()),  # ID baseado no timestamp
                "de": telefone,
                "para": para,
                "conteudo": entrada,
                "status": "ENVIADA"
            }

            # Envia mensagem ao servidor
            client.send(json.dumps(mensagem).encode())


# inicia cliente
start_client()