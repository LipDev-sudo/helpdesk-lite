"""Regras de negócio dos chamados."""

from __future__ import annotations

import csv
import io
import json
import sqlite3
from typing import Any

from .database import conexao_banco

CATEGORIAS_VALIDAS = {"hardware", "software", "rede", "acesso", "outro"}
PRIORIDADES_VALIDAS = {"baixa", "media", "alta", "critica"}
STATUS_VALIDOS = {"aberto", "em andamento", "resolvido"}

ORDENACOES = ("recentes", "antigos", "prioridade")

CAMPOS_EDITAVEIS = ("titulo", "descricao", "solicitante", "categoria", "prioridade")

COLUNAS_EXPORTACAO = (
    "id",
    "titulo",
    "descricao",
    "solicitante",
    "categoria",
    "prioridade",
    "status",
    "criado_em",
    "atualizado_em",
    "resolvido_em",
)

_ORDEM_PRIORIDADE = "CASE prioridade WHEN 'critica' THEN 0 WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END"

Linha = tuple[Any, ...]


def _escolha_valida(valor: str, validos: set[str], mensagem: str) -> str:
    valor = valor.strip().lower()

    if valor not in validos:
        raise ValueError(mensagem)

    return valor


def _registrar(conexao: sqlite3.Connection, chamado_id: int, evento: str, detalhe: str) -> None:
    conexao.execute(
        "INSERT INTO historico (chamado_id, evento, detalhe) VALUES (?, ?, ?)",
        (chamado_id, evento, detalhe),
    )


def cadastrar_chamado(
    titulo: str,
    descricao: str,
    solicitante: str,
    categoria: str,
    prioridade: str = "media",
) -> int:
    titulo = titulo.strip()
    descricao = descricao.strip()
    solicitante = solicitante.strip()

    if not titulo or not descricao or not solicitante:
        raise ValueError("Título, descrição e solicitante são obrigatórios.")

    categoria = _escolha_valida(categoria, CATEGORIAS_VALIDAS, "Categoria inválida.")
    prioridade = _escolha_valida(prioridade, PRIORIDADES_VALIDAS, "Prioridade inválida.")

    with conexao_banco() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO chamados (
                titulo, descricao, solicitante, categoria, prioridade,
                atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (titulo, descricao, solicitante, categoria, prioridade),
        )
        chamado_id = cursor.lastrowid
        _registrar(conexao, chamado_id, "criado", f"prioridade {prioridade}, categoria {categoria}")

        return chamado_id


def _celula_segura(valor: Any) -> Any:
    """Evita injeção de fórmulas ao abrir o CSV em planilhas (valores iniciados por = + - @)."""
    if isinstance(valor, str) and valor.startswith(("=", "+", "-", "@")):
        return "'" + valor

    return valor


def _padrao_like(texto: str) -> str:
    escapado = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


def listar_chamados(
    status: str | None = None,
    *,
    categoria: str | None = None,
    prioridade: str | None = None,
    solicitante: str | None = None,
    busca: str | None = None,
    ordenar: str = "recentes",
) -> list[Linha]:
    """Lista chamados com filtros opcionais.

    Cada linha traz: id, titulo, solicitante, categoria, prioridade, status, criado_em.
    """
    condicoes: list[str] = []
    parametros: list[Any] = []

    if status is not None:
        status = _escolha_valida(status, STATUS_VALIDOS, "Status inválido.")
        condicoes.append("status = ?")
        parametros.append(status)

    if categoria is not None:
        categoria = _escolha_valida(categoria, CATEGORIAS_VALIDAS, "Categoria inválida.")
        condicoes.append("categoria = ?")
        parametros.append(categoria)

    if prioridade is not None:
        prioridade = _escolha_valida(prioridade, PRIORIDADES_VALIDAS, "Prioridade inválida.")
        condicoes.append("prioridade = ?")
        parametros.append(prioridade)

    if solicitante is not None and solicitante.strip():
        condicoes.append("solicitante = ? COLLATE NOCASE")
        parametros.append(solicitante.strip())

    if busca is not None and busca.strip():
        padrao = _padrao_like(busca.strip())
        condicoes.append(
            "(titulo LIKE ? ESCAPE '\\' OR descricao LIKE ? ESCAPE '\\' OR solicitante LIKE ? ESCAPE '\\')"
        )
        parametros.extend([padrao, padrao, padrao])

    if ordenar not in ORDENACOES:
        raise ValueError(f"Ordenação inválida. Use: {', '.join(ORDENACOES)}.")

    ordem = {
        "recentes": "id DESC",
        "antigos": "id ASC",
        "prioridade": f"{_ORDEM_PRIORIDADE}, id DESC",
    }[ordenar]

    consulta = """
        SELECT id, titulo, solicitante, categoria,
               prioridade, status, criado_em
        FROM chamados
    """

    if condicoes:
        consulta += " WHERE " + " AND ".join(condicoes)

    consulta += f" ORDER BY {ordem}"

    with conexao_banco() as conexao:
        return conexao.execute(consulta, parametros).fetchall()


def consultar_chamado(chamado_id: int) -> Linha | None:
    with conexao_banco() as conexao:
        return conexao.execute(
            """
            SELECT id, titulo, descricao, solicitante, categoria,
                   prioridade, status, criado_em
            FROM chamados
            WHERE id = ?
            """,
            (chamado_id,),
        ).fetchone()


def detalhes_chamado(chamado_id: int) -> dict[str, Any] | None:
    """Todos os campos do chamado, incluindo as datas de atualização e resolução."""
    with conexao_banco() as conexao:
        linha = conexao.execute(
            f"SELECT {', '.join(COLUNAS_EXPORTACAO)} FROM chamados WHERE id = ?",
            (chamado_id,),
        ).fetchone()

    return None if linha is None else dict(zip(COLUNAS_EXPORTACAO, linha, strict=True))


def atualizar_status(chamado_id: int, novo_status: str) -> bool:
    novo_status = _escolha_valida(novo_status, STATUS_VALIDOS, "Status inválido.")

    with conexao_banco() as conexao:
        atual = conexao.execute("SELECT status FROM chamados WHERE id = ?", (chamado_id,)).fetchone()

        if atual is None:
            raise ValueError("Chamado não encontrado.")

        if atual[0] == novo_status:
            return True

        conexao.execute(
            """
            UPDATE chamados
            SET status = ?,
                atualizado_em = datetime('now'),
                resolvido_em = CASE WHEN ? = 'resolvido' THEN datetime('now') ELSE NULL END
            WHERE id = ?
            """,
            (novo_status, novo_status, chamado_id),
        )
        _registrar(conexao, chamado_id, "status", f"{atual[0]} -> {novo_status}")

    return True


def editar_chamado(
    chamado_id: int,
    *,
    titulo: str | None = None,
    descricao: str | None = None,
    solicitante: str | None = None,
    categoria: str | None = None,
    prioridade: str | None = None,
) -> list[str]:
    """Altera os campos informados e devolve a lista de campos efetivamente modificados."""
    novos = {
        "titulo": titulo,
        "descricao": descricao,
        "solicitante": solicitante,
        "categoria": categoria,
        "prioridade": prioridade,
    }
    novos = {campo: valor for campo, valor in novos.items() if valor is not None}

    if not novos:
        raise ValueError("Informe ao menos um campo para editar.")

    for campo in ("titulo", "descricao", "solicitante"):
        if campo in novos:
            novos[campo] = novos[campo].strip()
            if not novos[campo]:
                raise ValueError(f"O campo {campo} não pode ficar vazio.")

    if "categoria" in novos:
        novos["categoria"] = _escolha_valida(novos["categoria"], CATEGORIAS_VALIDAS, "Categoria inválida.")

    if "prioridade" in novos:
        novos["prioridade"] = _escolha_valida(novos["prioridade"], PRIORIDADES_VALIDAS, "Prioridade inválida.")

    with conexao_banco() as conexao:
        atual = conexao.execute(
            f"SELECT {', '.join(CAMPOS_EDITAVEIS)} FROM chamados WHERE id = ?", (chamado_id,)
        ).fetchone()

        if atual is None:
            raise ValueError("Chamado não encontrado.")

        valores_atuais = dict(zip(CAMPOS_EDITAVEIS, atual, strict=True))
        alterados = {campo: valor for campo, valor in novos.items() if valores_atuais[campo] != valor}

        if not alterados:
            return []

        atribuicoes = ", ".join(f"{campo} = ?" for campo in alterados)
        conexao.execute(
            f"UPDATE chamados SET {atribuicoes}, atualizado_em = datetime('now') WHERE id = ?",
            [*alterados.values(), chamado_id],
        )

        for campo, valor in alterados.items():
            if campo in ("titulo", "descricao"):
                detalhe = f"{campo} alterado"
            else:
                detalhe = f"{campo}: {valores_atuais[campo]} -> {valor}"
            _registrar(conexao, chamado_id, "editado", detalhe)

    return list(alterados)


def excluir_chamado(chamado_id: int) -> bool:
    with conexao_banco() as conexao:
        cursor = conexao.execute("DELETE FROM chamados WHERE id = ?", (chamado_id,))

        if cursor.rowcount == 0:
            raise ValueError("Chamado não encontrado.")

        return True


def historico_chamado(chamado_id: int) -> list[dict[str, str]]:
    with conexao_banco() as conexao:
        linhas = conexao.execute(
            "SELECT em, evento, detalhe FROM historico WHERE chamado_id = ? ORDER BY id",
            (chamado_id,),
        ).fetchall()

    return [{"em": em, "evento": evento, "detalhe": detalhe} for em, evento, detalhe in linhas]


def _contagem(conexao: sqlite3.Connection, coluna: str, ordem: tuple[str, ...]) -> dict[str, int]:
    linhas = dict(conexao.execute(f"SELECT {coluna}, COUNT(*) FROM chamados GROUP BY {coluna}").fetchall())
    return {valor: linhas.get(valor, 0) for valor in ordem}


def resumo() -> dict[str, Any]:
    """Indicadores gerais dos chamados."""
    with conexao_banco() as conexao:
        total = conexao.execute("SELECT COUNT(*) FROM chamados").fetchone()[0]
        urgentes = conexao.execute(
            "SELECT COUNT(*) FROM chamados WHERE status != 'resolvido' AND prioridade IN ('alta', 'critica')"
        ).fetchone()[0]
        horas = conexao.execute(
            """
            SELECT AVG((julianday(resolvido_em) - julianday(criado_em)) * 24)
            FROM chamados
            WHERE status = 'resolvido' AND resolvido_em IS NOT NULL
            """
        ).fetchone()[0]

        return {
            "total": total,
            "por_status": _contagem(conexao, "status", ("aberto", "em andamento", "resolvido")),
            "por_prioridade": _contagem(conexao, "prioridade", ("critica", "alta", "media", "baixa")),
            "por_categoria": _contagem(conexao, "categoria", tuple(sorted(CATEGORIAS_VALIDAS))),
            "pendentes_alta_prioridade": urgentes,
            "tempo_medio_resolucao_horas": None if horas is None else round(horas, 1),
        }


def exportar_chamados(formato: str = "csv", status: str | None = None) -> str:
    """Exporta todos os chamados (ou os de um status) em CSV ou JSON."""
    if formato not in ("csv", "json"):
        raise ValueError("Formato inválido. Use csv ou json.")

    consulta = f"SELECT {', '.join(COLUNAS_EXPORTACAO)} FROM chamados"
    parametros: list[str] = []

    if status is not None:
        parametros.append(_escolha_valida(status, STATUS_VALIDOS, "Status inválido."))
        consulta += " WHERE status = ?"

    with conexao_banco() as conexao:
        linhas = conexao.execute(consulta + " ORDER BY id", parametros).fetchall()

    if formato == "json":
        return json.dumps(
            [dict(zip(COLUNAS_EXPORTACAO, linha, strict=True)) for linha in linhas],
            ensure_ascii=False,
            indent=2,
        )

    saida = io.StringIO()
    escritor = csv.writer(saida)
    escritor.writerow(COLUNAS_EXPORTACAO)
    escritor.writerows([_celula_segura(valor) for valor in linha] for linha in linhas)
    return saida.getvalue()
