import sqlite3

# Cria e retorna uma conexão com o banco SQLite
def conectar():
    return sqlite3.connect("chat.db")


# Cria as tabelas do sistema caso ainda não existam
def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    # Tabela de usuários cadastrados
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        telefone TEXT PRIMARY KEY,
        nome TEXT
    )
    """)

    # Tabela principal que armazena todas as mensagens do sistema
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mensagens (
        id TEXT PRIMARY KEY,
        remetente TEXT,
        destinatario TEXT,
        conteudo TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


# ==========================
# FUNÇÕES DE USUÁRIOS
# ==========================

# Cadastra um usuário caso ele ainda não exista
def cadastrar_usuario(telefone, nome):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO usuarios (telefone, nome)
    VALUES (?, ?)
    """, (telefone, nome))

    conn.commit()
    conn.close()


# Verifica se um usuário existe
def usuario_existe(telefone):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT telefone
    FROM usuarios
    WHERE telefone = ?
    """, (telefone,))

    resultado = cursor.fetchone()

    conn.close()

    return resultado is not None


# Busca o nome de um usuário
def buscar_nome(telefone):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT nome
    FROM usuarios
    WHERE telefone = ?
    """, (telefone,))

    resultado = cursor.fetchone()

    conn.close()

    return resultado[0] if resultado else None


# ==========================
# FUNÇÕES DE MENSAGENS
# ==========================

# Insere uma nova mensagem no banco
def salvar_mensagem(msg):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO mensagens (id, remetente, destinatario, conteudo, status)
    VALUES (?, ?, ?, ?, ?)
    """, (
        msg["id"],
        msg["de"],
        msg["para"],
        msg["conteudo"],
        msg["status"]
    ))

    conn.commit()
    conn.close()


# Atualiza o status de uma mensagem específica
def atualizar_status(id_msg, status):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE mensagens SET status = ? WHERE id = ?
    """, (status, id_msg))

    conn.commit()
    conn.close()


# Busca mensagens pendentes de entrega
def buscar_pendentes(telefone):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, remetente, destinatario, conteudo, status
    FROM mensagens
    WHERE destinatario = ? AND status = 'ENVIADA'
    """, (telefone,))

    resultados = cursor.fetchall()

    conn.close()

    mensagens = []

    for r in resultados:
        mensagens.append({
            "id": r[0],
            "de": r[1],
            "para": r[2],
            "conteudo": r[3],
            "status": r[4],
            "tipo": "mensagem"
        })

    return mensagens


# Retorna o remetente de uma mensagem
def buscar_remetente(id_msg):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT remetente
    FROM mensagens
    WHERE id = ?
    """, (id_msg,))

    resultado = cursor.fetchone()

    conn.close()

    return resultado[0] if resultado else None


# Busca todo o histórico entre dois usuários
def buscar_conversa(user1, user2):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT remetente, destinatario, conteudo
    FROM mensagens
    WHERE (remetente = ? AND destinatario = ?)
       OR (remetente = ? AND destinatario = ?)
    ORDER BY rowid ASC
    """, (user1, user2, user2, user1))

    resultados = cursor.fetchall()

    conn.close()

    mensagens = []

    for r in resultados:
        mensagens.append({
            "de": r[0],
            "para": r[1],
            "conteudo": r[2]
        })

    return mensagens