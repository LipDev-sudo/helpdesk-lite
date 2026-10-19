"""Acesso ao banco SQLite e migrações de esquema."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# O caminho pode ser trocado pela variável de ambiente HELPDESK_DB ou pela opção --db da CLI.
DATABASE_PATH = Path(os.environ.get("HELPDESK_DB") or Path(__file__).resolve().parent.parent / "helpdesk.db")

SCHEMA_ATUAL = 2


def definir_caminho(caminho: str | Path) -> None:
    global DATABASE_PATH
    DATABASE_PATH = Path(caminho)


def conectar() -> sqlite3.Connection:
    conexao = sqlite3.connect(DATABASE_PATH)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


@contextmanager
def conexao_banco() -> Iterator[sqlite3.Connection]:
    conexao = conectar()

    try:
        with conexao:
            yield conexao
    finally:
        conexao.close()


def _migrar_v1(conexao: sqlite3.Connection) -> None:
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


def _migrar_v2(conexao: sqlite3.Connection) -> None:
    """Adiciona datas de atualização/resolução, histórico e índices."""
    colunas = {linha[1] for linha in conexao.execute("PRAGMA table_info(chamados)")}

    if "atualizado_em" not in colunas:
        conexao.execute("ALTER TABLE chamados ADD COLUMN atualizado_em TEXT")

    if "resolvido_em" not in colunas:
        conexao.execute("ALTER TABLE chamados ADD COLUMN resolvido_em TEXT")

    conexao.execute("UPDATE chamados SET atualizado_em = criado_em WHERE atualizado_em IS NULL")
    conexao.execute(
        "UPDATE chamados SET resolvido_em = atualizado_em WHERE status = 'resolvido' AND resolvido_em IS NULL"
    )

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chamado_id INTEGER NOT NULL REFERENCES chamados(id) ON DELETE CASCADE,
            evento TEXT NOT NULL,
            detalhe TEXT NOT NULL,
            em TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_historico_chamado ON historico(chamado_id)")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_chamados_status ON chamados(status)")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_chamados_prioridade ON chamados(prioridade)")


MIGRACOES = (_migrar_v1, _migrar_v2)


def inicializar_banco() -> None:
    """Cria o banco ou atualiza um banco existente para o esquema atual, sem perder dados."""
    with conexao_banco() as conexao:
        versao = conexao.execute("PRAGMA user_version").fetchone()[0]

        for numero, migracao in enumerate(MIGRACOES, start=1):
            if numero > versao:
                migracao(conexao)

        conexao.execute(f"PRAGMA user_version = {SCHEMA_ATUAL}")


if __name__ == "__main__":
    inicializar_banco()
    print("Banco de dados inicializado com sucesso.")
