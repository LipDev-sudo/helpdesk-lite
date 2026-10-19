"""Interface de linha de comando: menu interativo e subcomandos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__, database
from .database import inicializar_banco
from .tickets import (
    CATEGORIAS_VALIDAS,
    ORDENACOES,
    PRIORIDADES_VALIDAS,
    STATUS_VALIDOS,
    atualizar_status,
    cadastrar_chamado,
    consultar_chamado,
    detalhes_chamado,
    editar_chamado,
    excluir_chamado,
    exportar_chamados,
    historico_chamado,
    listar_chamados,
    resumo,
)

PRIORIDADES_ORDENADAS = ["baixa", "media", "alta", "critica"]
CAMPOS_LISTAGEM = ("id", "titulo", "solicitante", "categoria", "prioridade", "status", "criado_em")


def ler_id_chamado() -> int:
    entrada = input("ID do chamado: ").strip()

    if not entrada.isdigit():
        raise ValueError("Digite apenas o número do ID, por exemplo: 2.")

    chamado_id = int(entrada)

    if chamado_id <= 0:
        raise ValueError("O ID deve ser um número positivo.")

    return chamado_id


def exibir_menu() -> None:
    print("\n=== HELPDESK LITE ===")
    print("1. Cadastrar chamado")
    print("2. Listar chamados")
    print("3. Consultar chamado")
    print("4. Atualizar status")
    print("5. Excluir chamado")
    print("6. Editar chamado")
    print("7. Resumo")
    print("0. Sair")


def _linha_listagem(c: tuple[Any, ...]) -> str:
    return f"#{c[0]} | {c[1]} | {c[2]} | {c[3]} | Prioridade: {c[4]} | Status: {c[5]}"


def menu_cadastrar() -> None:
    print("\n--- Novo chamado ---")

    titulo = input("Título: ").strip()
    descricao = input("Descrição: ").strip()
    solicitante = input("Solicitante: ").strip()

    print("\nCategorias disponíveis:")
    for categoria_valida in sorted(CATEGORIAS_VALIDAS):
        print(f"- {categoria_valida}")
    categoria = input("Categoria: ").strip().lower()

    prioridades_validas = set(PRIORIDADES_VALIDAS)

    print("\nPrioridades disponíveis:")
    for prioridade_valida in PRIORIDADES_ORDENADAS:
        print(f"- {prioridade_valida}")

    while True:
        prioridade = input("Prioridade [media]: ").strip().lower()

        if not prioridade:
            prioridade = "media"

        if prioridade in prioridades_validas:
            break

        print("Prioridade inválida. Escolha: baixa, media, alta ou critica.")

    chamado_id = cadastrar_chamado(titulo, descricao, solicitante, categoria, prioridade)

    print(f"\nChamado #{chamado_id} cadastrado com sucesso.")


def menu_listar() -> None:
    print("\n--- Listar chamados ---")
    print("1. Todos os chamados")
    print("2. Chamados abertos")
    print("3. Chamados em andamento")
    print("4. Chamados resolvidos")
    print("5. Buscar por texto")

    opcao = input("\nEscolha uma opção: ").strip()

    filtros = {"1": None, "2": "aberto", "3": "em andamento", "4": "resolvido"}

    if opcao == "5":
        chamados = listar_chamados(busca=input("Texto a buscar: "), ordenar="prioridade")
    elif opcao in filtros:
        chamados = listar_chamados(filtros[opcao])
    else:
        print("Opção inválida.")
        return

    if not chamados:
        print("Nenhum chamado encontrado.")
        return

    print("\n--- Resultado ---")

    for chamado in chamados:
        print(_linha_listagem(chamado))


def _exibir_detalhes(detalhes: dict[str, Any], historico: list[dict[str, str]]) -> None:
    rotulos = {
        "id": "ID",
        "titulo": "Título",
        "descricao": "Descrição",
        "solicitante": "Solicitante",
        "categoria": "Categoria",
        "prioridade": "Prioridade",
        "status": "Status",
        "criado_em": "Criado em",
        "atualizado_em": "Atualizado em",
        "resolvido_em": "Resolvido em",
    }

    for campo, rotulo in rotulos.items():
        if detalhes.get(campo) is not None:
            print(f"{rotulo}: {detalhes[campo]}")

    if historico:
        print("\nHistórico:")
        for item in historico:
            print(f"- {item['em']} | {item['evento']}: {item['detalhe']}")


def menu_consultar() -> None:
    print("\n--- Consultar chamado ---")
    chamado_id = ler_id_chamado()
    detalhes = detalhes_chamado(chamado_id)

    if detalhes is None:
        print("Chamado não encontrado.")
        return

    print()
    _exibir_detalhes(detalhes, historico_chamado(chamado_id))


def menu_atualizar_status() -> None:
    print("\n--- Atualizar status ---")
    chamado_id = ler_id_chamado()

    if consultar_chamado(chamado_id) is None:
        print("Chamado não encontrado.")
        return

    novo_status = input("Novo status (aberto/em andamento/resolvido): ")

    atualizar_status(chamado_id, novo_status)
    print(f"Status do chamado #{chamado_id} atualizado.")


def menu_editar() -> None:
    print("\n--- Editar chamado ---")
    chamado_id = ler_id_chamado()

    if consultar_chamado(chamado_id) is None:
        print("Chamado não encontrado.")
        return

    print("Deixe em branco para manter o valor atual.")
    campos = {
        "titulo": input("Novo título: ").strip() or None,
        "descricao": input("Nova descrição: ").strip() or None,
        "solicitante": input("Novo solicitante: ").strip() or None,
        "categoria": input("Nova categoria: ").strip() or None,
        "prioridade": input("Nova prioridade: ").strip() or None,
    }

    if not any(campos.values()):
        print("Nenhuma alteração.")
        return

    alterados = editar_chamado(chamado_id, **campos)

    if alterados:
        print(f"Chamado #{chamado_id} atualizado: {', '.join(alterados)}.")
    else:
        print("Nenhuma alteração.")


def menu_excluir() -> None:
    print("\n--- Excluir chamado ---")
    chamado_id = ler_id_chamado()

    chamado = consultar_chamado(chamado_id)

    if chamado is None:
        print("Chamado não encontrado.")
        return

    confirmacao = input(f"Excluir o chamado #{chamado_id} ({chamado[1]})? [s/N]: ").strip().lower()

    if confirmacao != "s":
        print("Exclusão cancelada.")
        return

    excluir_chamado(chamado_id)
    print(f"Chamado #{chamado_id} excluído.")


def _exibir_resumo(dados: dict[str, Any]) -> None:
    print(f"Total de chamados: {dados['total']}")
    print(f"Pendentes de alta prioridade: {dados['pendentes_alta_prioridade']}")

    horas = dados["tempo_medio_resolucao_horas"]
    print(f"Tempo médio de resolução: {'N/D' if horas is None else f'{horas:g} h'}")

    for titulo, chave in (
        ("Por status", "por_status"),
        ("Por prioridade", "por_prioridade"),
        ("Por categoria", "por_categoria"),
    ):
        print(f"\n{titulo}:")
        for nome, quantidade in dados[chave].items():
            print(f"- {nome}: {quantidade}")


def menu_resumo() -> None:
    print("\n--- Resumo ---")
    _exibir_resumo(resumo())


def menu_interativo() -> None:
    inicializar_banco()

    acoes = {
        "1": menu_cadastrar,
        "2": menu_listar,
        "3": menu_consultar,
        "4": menu_atualizar_status,
        "5": menu_excluir,
        "6": menu_editar,
        "7": menu_resumo,
    }

    while True:
        exibir_menu()
        opcao = input("\nEscolha uma opção: ").strip()

        if not opcao:
            continue

        try:
            if opcao == "0":
                print("Encerrando o HelpDesk Lite.")
                break

            acao = acoes.get(opcao)

            if acao is None:
                print("Opção inválida. Tente novamente.")
            else:
                acao()

        except ValueError as erro:
            print(f"Erro: {erro}")

        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")

        input("\nPressione Enter para continuar...")


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="helpdesk",
        description="HelpDesk Lite: chamados de suporte com SQLite.",
        epilog="Sem subcomando, abre o menu interativo.",
    )
    parser.add_argument("--db", metavar="ARQUIVO", help="arquivo do banco SQLite (padrão: helpdesk.db ou $HELPDESK_DB)")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="comando")

    novo = sub.add_parser("novo", help="cadastra um chamado")
    novo.add_argument("--titulo", required=True)
    novo.add_argument("--descricao", required=True)
    novo.add_argument("--solicitante", required=True)
    novo.add_argument("--categoria", required=True, choices=sorted(CATEGORIAS_VALIDAS))
    novo.add_argument("--prioridade", default="media", choices=PRIORIDADES_ORDENADAS)

    listar = sub.add_parser("listar", help="lista chamados, com filtros e busca")
    listar.add_argument("--status", choices=sorted(STATUS_VALIDOS))
    listar.add_argument("--categoria", choices=sorted(CATEGORIAS_VALIDAS))
    listar.add_argument("--prioridade", choices=PRIORIDADES_ORDENADAS)
    listar.add_argument("--solicitante")
    listar.add_argument("--busca", help="texto no título, descrição ou solicitante")
    listar.add_argument("--ordenar", choices=ORDENACOES, default="recentes")
    listar.add_argument("--json", action="store_true", dest="formato_json")

    ver = sub.add_parser("ver", help="mostra um chamado e o seu histórico")
    ver.add_argument("id", type=int)
    ver.add_argument("--json", action="store_true", dest="formato_json")

    editar = sub.add_parser("editar", help="edita campos de um chamado")
    editar.add_argument("id", type=int)
    editar.add_argument("--titulo")
    editar.add_argument("--descricao")
    editar.add_argument("--solicitante")
    editar.add_argument("--categoria", choices=sorted(CATEGORIAS_VALIDAS))
    editar.add_argument("--prioridade", choices=PRIORIDADES_ORDENADAS)

    status = sub.add_parser("status", help="atualiza o status de um chamado")
    status.add_argument("id", type=int)
    status.add_argument("novo_status", choices=sorted(STATUS_VALIDOS))

    excluir = sub.add_parser("excluir", help="exclui um chamado")
    excluir.add_argument("id", type=int)
    excluir.add_argument("--sim", action="store_true", help="não pede confirmação")

    resumo_cmd = sub.add_parser("resumo", help="indicadores gerais dos chamados")
    resumo_cmd.add_argument("--json", action="store_true", dest="formato_json")

    exportar = sub.add_parser("exportar", help="exporta os chamados em CSV ou JSON")
    exportar.add_argument("--formato", choices=("csv", "json"), default="csv")
    exportar.add_argument("--status", choices=sorted(STATUS_VALIDOS))
    exportar.add_argument("-o", "--saida", metavar="ARQUIVO", help="grava em arquivo em vez de imprimir")

    return parser


def _imprimir_json(dados: Any) -> None:
    print(json.dumps(dados, ensure_ascii=False, indent=2))


def executar_comando(args: argparse.Namespace) -> None:
    if args.comando == "novo":
        chamado_id = cadastrar_chamado(args.titulo, args.descricao, args.solicitante, args.categoria, args.prioridade)
        print(f"Chamado #{chamado_id} cadastrado com sucesso.")

    elif args.comando == "listar":
        chamados = listar_chamados(
            args.status,
            categoria=args.categoria,
            prioridade=args.prioridade,
            solicitante=args.solicitante,
            busca=args.busca,
            ordenar=args.ordenar,
        )

        if args.formato_json:
            _imprimir_json([dict(zip(CAMPOS_LISTAGEM, c, strict=True)) for c in chamados])
        elif not chamados:
            print("Nenhum chamado encontrado.")
        else:
            for c in chamados:
                print(_linha_listagem(c))

    elif args.comando == "ver":
        detalhes = detalhes_chamado(args.id)

        if detalhes is None:
            raise ValueError("Chamado não encontrado.")

        historico = historico_chamado(args.id)

        if args.formato_json:
            _imprimir_json({**detalhes, "historico": historico})
        else:
            _exibir_detalhes(detalhes, historico)

    elif args.comando == "editar":
        alterados = editar_chamado(
            args.id,
            titulo=args.titulo,
            descricao=args.descricao,
            solicitante=args.solicitante,
            categoria=args.categoria,
            prioridade=args.prioridade,
        )
        print(f"Chamado #{args.id} atualizado: {', '.join(alterados)}." if alterados else "Nenhuma alteração.")

    elif args.comando == "status":
        atualizar_status(args.id, args.novo_status)
        print(f"Status do chamado #{args.id} atualizado.")

    elif args.comando == "excluir":
        if consultar_chamado(args.id) is None:
            raise ValueError("Chamado não encontrado.")

        if not args.sim:
            resposta = input(f"Excluir o chamado #{args.id}? [s/N]: ").strip().lower()
            if resposta != "s":
                print("Exclusão cancelada.")
                return

        excluir_chamado(args.id)
        print(f"Chamado #{args.id} excluído.")

    elif args.comando == "resumo":
        dados = resumo()
        if args.formato_json:
            _imprimir_json(dados)
        else:
            _exibir_resumo(dados)

    elif args.comando == "exportar":
        conteudo = exportar_chamados(args.formato, args.status)

        if args.saida:
            Path(args.saida).write_text(conteudo, encoding="utf-8", newline="")
            print(f"Chamados exportados para {args.saida}.")
        else:
            print(conteudo, end="" if conteudo.endswith("\n") else "\n")


def main(argv: list[str] | None = None) -> int:
    args = criar_parser().parse_args(argv)

    if args.db:
        database.definir_caminho(args.db)

    if args.comando is None:
        menu_interativo()
        return 0

    inicializar_banco()

    try:
        executar_comando(args)
    except ValueError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
