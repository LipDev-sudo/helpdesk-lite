
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DATABASE_PATH = Path(__file__).parent / "helpdesk.db"


def conectar():
    return sqlite3.connect(DATABASE_PATH)


@contextmanager
def conexao_banco():
    conexao = conectar()

    try:
        with conexao:
            yield conexao
    finally:
        conexao.close()


def inicializar_banco():
    with conexao_banco() as conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                solicitante TEXT NOT NULL,
                categoria TEXT NOT NULL,
                prioridade TEXT NOT NULL DEFAULT 'media',
                status TEXT NOT NULL DEFAULT 'aberto',
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


if __name__ == "__main__":
    inicializar_banco()
    print("Banco de dados inicializado com sucesso.")
