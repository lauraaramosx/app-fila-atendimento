from datetime import datetime
import sqlite3

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

DATABASE = "fila.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            prioridade TEXT NOT NULL DEFAULT 'Normal'
                CHECK (prioridade IN ('Normal', 'Preferencial')),
            status TEXT NOT NULL DEFAULT 'Aguardando'
                CHECK (status IN ('Aguardando', 'Em Atendimento', 'Concluído', 'Cancelado')),
            criado_em TEXT NOT NULL,
            chamado_em TEXT,
            finalizado_em TEXT
        );

        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atendimento_id INTEGER,
            nome TEXT NOT NULL,
            prioridade TEXT NOT NULL,
            status TEXT NOT NULL,
            acao TEXT NOT NULL,
            realizado_em TEXT NOT NULL,
            FOREIGN KEY (atendimento_id)
                REFERENCES atendimentos(id)
                ON DELETE SET NULL
        );
    """)

    conn.commit()
    conn.close()


def agora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def registrar_historico(conn, atendimento, status, acao):
    conn.execute(
        """
        INSERT INTO historico
            (atendimento_id, nome, prioridade, status, acao, realizado_em)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            atendimento["id"],
            atendimento["nome"],
            atendimento["prioridade"],
            status,
            acao,
            agora(),
        ),
    )


@app.route("/")
def index():
    conn = get_db()

    fila = conn.execute(
        """
        SELECT *
        FROM atendimentos
        WHERE status IN ('Aguardando', 'Em Atendimento')
        ORDER BY
            CASE WHEN prioridade = 'Preferencial' THEN 0 ELSE 1 END,
            criado_em ASC,
            id ASC
        """
    ).fetchall()

    atual = conn.execute(
        """
        SELECT *
        FROM atendimentos
        WHERE status = 'Em Atendimento'
        ORDER BY chamado_em DESC
        LIMIT 1
        """
    ).fetchone()

    conn.close()

    return render_template(
        "index.html",
        fila=fila,
        atual=atual,
    )


@app.post("/cadastrar")
def cadastrar():
    nome = request.form.get("nome", "").strip()
    telefone = request.form.get("telefone", "").strip()
    prioridade = request.form.get("prioridade", "Normal")

    if not nome:
        return redirect(url_for("index"))

    if prioridade not in ("Normal", "Preferencial"):
        prioridade = "Normal"

    conn = get_db()

    criado_em = agora()

    cursor = conn.execute(
        """
        INSERT INTO atendimentos
            (nome, telefone, prioridade, status, criado_em)
        VALUES (?, ?, ?, 'Aguardando', ?)
        """,
        (nome, telefone, prioridade, criado_em),
    )

    atendimento = conn.execute(
        "SELECT * FROM atendimentos WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()

    registrar_historico(
        conn,
        atendimento,
        "Aguardando",
        "Cliente entrou na fila",
    )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.post("/chamar-proximo")
def chamar_proximo():
    conn = get_db()

    # Só permite um atendimento ativo por vez.
    atendimento_ativo = conn.execute(
        """
        SELECT *
        FROM atendimentos
        WHERE status = 'Em Atendimento'
        LIMIT 1
        """
    ).fetchone()

    if atendimento_ativo:
        conn.close()
        return redirect(url_for("index"))

    # Preferenciais vêm primeiro; dentro da mesma prioridade,
    # respeita-se a ordem de chegada.
    proximo = conn.execute(
        """
        SELECT *
        FROM atendimentos
        WHERE status = 'Aguardando'
        ORDER BY
            CASE WHEN prioridade = 'Preferencial' THEN 0 ELSE 1 END,
            criado_em ASC,
            id ASC
        LIMIT 1
        """
    ).fetchone()

    if proximo:
        chamado_em = agora()

        conn.execute(
            """
            UPDATE atendimentos
            SET status = 'Em Atendimento',
                chamado_em = ?
            WHERE id = ?
            """,
            (chamado_em, proximo["id"]),
        )

        atualizado = conn.execute(
            "SELECT * FROM atendimentos WHERE id = ?",
            (proximo["id"],),
        ).fetchone()

        registrar_historico(
            conn,
            atualizado,
            "Em Atendimento",
            "Cliente chamado para atendimento",
        )

        conn.commit()

    conn.close()

    return redirect(url_for("index"))


@app.post("/atendimento/<int:atendimento_id>/concluir")
def concluir(atendimento_id):
    conn = get_db()

    atendimento = conn.execute(
        "SELECT * FROM atendimentos WHERE id = ?",
        (atendimento_id,),
    ).fetchone()

    if atendimento and atendimento["status"] == "Em Atendimento":
        finalizado_em = agora()

        conn.execute(
            """
            UPDATE atendimentos
            SET status = 'Concluído',
                finalizado_em = ?
            WHERE id = ?
            """,
            (finalizado_em, atendimento_id),
        )

        atualizado = conn.execute(
            "SELECT * FROM atendimentos WHERE id = ?",
            (atendimento_id,),
        ).fetchone()

        registrar_historico(
            conn,
            atualizado,
            "Concluído",
            "Atendimento concluído",
        )

        conn.commit()

    conn.close()

    return redirect(url_for("index"))


@app.post("/atendimento/<int:atendimento_id>/cancelar")
def cancelar(atendimento_id):
    conn = get_db()

    atendimento = conn.execute(
        "SELECT * FROM atendimentos WHERE id = ?",
        (atendimento_id,),
    ).fetchone()

    if atendimento and atendimento["status"] in (
        "Aguardando",
        "Em Atendimento",
    ):
        conn.execute(
            """
            UPDATE atendimentos
            SET status = 'Cancelado',
                finalizado_em = ?
            WHERE id = ?
            """,
            (agora(), atendimento_id),
        )

        atualizado = conn.execute(
            "SELECT * FROM atendimentos WHERE id = ?",
            (atendimento_id,),
        ).fetchone()

        registrar_historico(
            conn,
            atualizado,
            "Cancelado",
            "Atendimento cancelado",
        )

        conn.commit()

    conn.close()

    return redirect(url_for("index"))


@app.get("/historico")
def historico():
    conn = get_db()

    registros = conn.execute(
        """
        SELECT *
        FROM historico
        ORDER BY realizado_em DESC, id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "historico.html",
        registros=registros,
    )


@app.get("/api/fila")
def api_fila():
    conn = get_db()

    fila = conn.execute(
        """
        SELECT
            id,
            nome,
            telefone,
            prioridade,
            status,
            criado_em,
            chamado_em
        FROM atendimentos
        WHERE status IN ('Aguardando', 'Em Atendimento')
        ORDER BY
            CASE WHEN prioridade = 'Preferencial' THEN 0 ELSE 1 END,
            criado_em ASC,
            id ASC
        """
    ).fetchall()

    conn.close()

    return jsonify([
        dict(item)
        for item in fila
    ])


@app.get("/api/atual")
def api_atual():
    conn = get_db()

    atual = conn.execute(
        """
        SELECT *
        FROM atendimentos
        WHERE status = 'Em Atendimento'
        ORDER BY chamado_em DESC
        LIMIT 1
        """
    ).fetchone()

    conn.close()

    return jsonify(dict(atual) if atual else None)


if __name__ == "__main__":
    init_db()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000,
    )
