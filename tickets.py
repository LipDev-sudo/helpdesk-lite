
from database import conexao_banco

CATEGORIAS_VALIDAS = {
    "hardware",
    "software",
    "rede",
    "acesso",
    "outro",
}

PRIORIDADES_VALIDAS = {
    "baixa",
    "media",
    "alta",
    "critica",
}


def cadastrar_chamado(titulo, descricao, solicitante, categoria, prioridade="media"):
    titulo = titulo.strip()
    descricao = descricao.strip()
    solicitante = solicitante.strip()
    categoria = categoria.strip().lower()
    prioridade = prioridade.strip().lower()

    if not titulo or not descricao or not solicitante:
        raise ValueError("Título, descrição e solicitante são obrigatórios.")

    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError("Categoria inválida.")

    if prioridade not in PRIORIDADES_VALIDAS:
        raise ValueError("Prioridade inválida.")

    with conexao_banco() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO chamados (
                titulo, descricao, solicitante, categoria, prioridade
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (titulo, descricao, solicitante, categoria, prioridade),
        )

        return cursor.lastrowid



def listar_chamados(status=None):
    consulta = """
        SELECT id, titulo, solicitante, categoria,
               prioridade, status, criado_em
        FROM chamados
    """
    parametros = ()

    if status is not None:
        status = status.strip().lower()

        if status not in {"aberto", "em andamento", "resolvido"}:
            raise ValueError("Status inválido.")

        consulta += " WHERE status = ?"
        parametros = (status,)

    consulta += " ORDER BY id DESC"

    with conexao_banco() as conexao:
        return conexao.execute(consulta, parametros).fetchall()



def consultar_chamado(chamado_id):
    with conexao_banco() as conexao:
        chamado = conexao.execute(
            """
            SELECT id, titulo, descricao, solicitante, categoria,
                   prioridade, status, criado_em
            FROM chamados
            WHERE id = ?
            """,
            (chamado_id,),
        ).fetchone()

    return chamado


STATUS_VALIDOS = {
    "aberto",
    "em andamento",
    "resolvido",
}



def atualizar_status(chamado_id, novo_status):
    novo_status = novo_status.strip().lower()

    if novo_status not in STATUS_VALIDOS:
        raise ValueError("Status inválido.")

    with conexao_banco() as conexao:
        cursor = conexao.execute(
            """
            UPDATE chamados
            SET status = ?
            WHERE id = ?
            """,
            (novo_status, chamado_id),
        )

        if cursor.rowcount == 0:
            raise ValueError("Chamado não encontrado.")

        return True

