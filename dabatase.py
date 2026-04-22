import sqlite3

def conectar():
    return sqlite3.connect("chat.db")

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

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

def atualizar_status(id_msg, status):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE mensagens SET status = ? WHERE id = ?
    """, (status, id_msg))

    conn.commit()
    conn.close()

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


def buscar_remetente(id_msg):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT remetente FROM mensagens WHERE id = ?", (id_msg,))
    result = cursor.fetchone()

    conn.close()

    return result[0] if result else None


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