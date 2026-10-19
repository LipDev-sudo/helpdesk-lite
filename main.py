
import argparse
import json
import sys

from database import inicializar_banco
from tickets import (
    CATEGORIAS_VALIDAS,
    PRIORIDADES_VALIDAS,
    STATUS_VALIDOS,
    cadastrar_chamado,
    listar_chamados,
    consultar_chamado,
    atualizar_status,
    excluir_chamado,
)


def ler_id_chamado():
    entrada = input("ID do chamado: ").strip()

    if not entrada.isdigit():
        raise ValueError("Digite apenas o número do ID, por exemplo: 2.")

    chamado_id = int(entrada)

    if chamado_id <= 0:
        raise ValueError("O ID deve ser um número positivo.")

    return chamado_id



def exibir_menu():
    print("\n=== HELPDESK LITE ===")
    print("1. Cadastrar chamado")
    print("2. Listar chamados")
    print("3. Consultar chamado")
    print("4. Atualizar status")
    print("5. Excluir chamado")
    print("0. Sair")




def menu_cadastrar():
    print("\n--- Novo chamado ---")

    titulo = input("Título: ").strip()
    descricao = input("Descrição: ").strip()
    solicitante = input("Solicitante: ").strip()

    print("\nCategorias disponíveis:")
    print("- hardware")
    print("- software")
    print("- rede")
    print("- acesso")
    print("- outro")
    categoria = input("Categoria: ").strip().lower()

    prioridades_validas = {"baixa", "media", "alta", "critica"}

    print("\nPrioridades disponíveis:")
    print("- baixa")
    print("- media")
    print("- alta")
    print("- critica")

    while True:
        prioridade = input("Prioridade [media]: ").strip().lower()

        if not prioridade:
            prioridade = "media"

        if prioridade in prioridades_validas:
            break

        print("Prioridade inválida. Escolha: baixa, media, alta ou critica.")

    chamado_id = cadastrar_chamado(
        titulo,
        descricao,
        solicitante,
        categoria,
        prioridade,
    )

    print(f"\nChamado #{chamado_id} cadastrado com sucesso.")





def menu_listar():
    print("\n--- Listar chamados ---")
    print("1. Todos os chamados")
    print("2. Chamados abertos")
    print("3. Chamados em andamento")
    print("4. Chamados resolvidos")

    opcao = input("\nEscolha uma opção: ").strip()

    filtros = {
        "1": None,
        "2": "aberto",
        "3": "em andamento",
        "4": "resolvido",
    }

    if opcao not in filtros:
        print("Opção inválida.")
        return

    chamados = listar_chamados(filtros[opcao])

    if not chamados:
        print("Nenhum chamado encontrado.")
        return

    print("\n--- Resultado ---")

    for chamado in chamados:
        print(
            f"#{chamado[0]} | {chamado[1]} | "
            f"{chamado[2]} | {chamado[3]} | "
            f"Prioridade: {chamado[4]} | Status: {chamado[5]}"
        )




def menu_consultar():
    print("\n--- Consultar chamado ---")
    chamado_id = ler_id_chamado()
    chamado = consultar_chamado(chamado_id)

    if chamado is None:
        print("Chamado não encontrado.")
        return

    print(f"\nID: {chamado[0]}")
    print(f"Título: {chamado[1]}")
    print(f"Descrição: {chamado[2]}")
    print(f"Solicitante: {chamado[3]}")
    print(f"Categoria: {chamado[4]}")
    print(f"Prioridade: {chamado[5]}")
    print(f"Status: {chamado[6]}")
    print(f"Criado em: {chamado[7]}")





def menu_atualizar_status():
    print("\n--- Atualizar status ---")
    chamado_id = ler_id_chamado()

    chamado = consultar_chamado(chamado_id)

    if chamado is None:
        print("Chamado não encontrado.")
        return

    novo_status = input(
        "Novo status (aberto/em andamento/resolvido): "
    )

    atualizar_status(chamado_id, novo_status)
    print(f"Status do chamado #{chamado_id} atualizado.")



def menu_excluir():
    print("\n--- Excluir chamado ---")
    chamado_id = ler_id_chamado()

    chamado = consultar_chamado(chamado_id)

    if chamado is None:
        print("Chamado não encontrado.")
        return

    confirmacao = input(
        f"Excluir o chamado #{chamado_id} ({chamado[1]})? [s/N]: "
    ).strip().lower()

    if confirmacao != "s":
        print("Exclusão cancelada.")
        return

    excluir_chamado(chamado_id)
    print(f"Chamado #{chamado_id} excluído.")



def menu_interativo():
    inicializar_banco()

    while True:
        exibir_menu()
        opcao = input("\nEscolha uma opção: ").strip()

        if not opcao:
            continue

        try:
            if opcao == "1":
                menu_cadastrar()
            elif opcao == "2":
                menu_listar()
            elif opcao == "3":
                menu_consultar()
            elif opcao == "4":
                menu_atualizar_status()
            elif opcao == "5":
                menu_excluir()
            elif opcao == "0":
                print("Encerrando o HelpDesk Lite.")
                break
            else:
                print("Opção inválida. Tente novamente.")

        except ValueError as erro:
            print(f"Erro: {erro}")

        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")

        input("\nPressione Enter para continuar...")


CAMPOS_CHAMADO = (
    "id", "titulo", "descricao", "solicitante",
    "categoria", "prioridade", "status", "criado_em",
)
CAMPOS_LISTAGEM = (
    "id", "titulo", "solicitante", "categoria",
    "prioridade", "status", "criado_em",
)


def chamado_para_dict(linha, campos):
    return dict(zip(campos, linha))



def criar_parser():
    parser = argparse.ArgumentParser(
        prog="helpdesk",
        description="HelpDesk Lite: chamados de suporte com SQLite.",
        epilog="Sem subcomando, abre o menu interativo.",
    )
    sub = parser.add_subparsers(dest="comando")

    novo = sub.add_parser("novo", help="cadastra um chamado")
    novo.add_argument("--titulo", required=True)
    novo.add_argument("--descricao", required=True)
    novo.add_argument("--solicitante", required=True)
    novo.add_argument("--categoria", required=True, choices=sorted(CATEGORIAS_VALIDAS))
    novo.add_argument("--prioridade", default="media", choices=["baixa", "media", "alta", "critica"])

    listar = sub.add_parser("listar", help="lista chamados")
    listar.add_argument("--status", choices=sorted(STATUS_VALIDOS))
    listar.add_argument("--json", action="store_true", dest="formato_json")

    ver = sub.add_parser("ver", help="mostra um chamado")
    ver.add_argument("id", type=int)
    ver.add_argument("--json", action="store_true", dest="formato_json")

    status = sub.add_parser("status", help="atualiza o status de um chamado")
    status.add_argument("id", type=int)
    status.add_argument("novo_status", choices=sorted(STATUS_VALIDOS))

    excluir = sub.add_parser("excluir", help="exclui um chamado")
    excluir.add_argument("id", type=int)
    excluir.add_argument("--sim", action="store_true", help="não pede confirmação")

    return parser



def executar_comando(args):
    if args.comando == "novo":
        chamado_id = cadastrar_chamado(
            args.titulo, args.descricao, args.solicitante,
            args.categoria, args.prioridade,
        )
        print(f"Chamado #{chamado_id} cadastrado com sucesso.")

    elif args.comando == "listar":
        chamados = listar_chamados(args.status)

        if args.formato_json:
            print(json.dumps(
                [chamado_para_dict(c, CAMPOS_LISTAGEM) for c in chamados],
                ensure_ascii=False, indent=2,
            ))
        elif not chamados:
            print("Nenhum chamado encontrado.")
        else:
            for c in chamados:
                print(f"#{c[0]} | {c[1]} | {c[2]} | {c[3]} | Prioridade: {c[4]} | Status: {c[5]}")

    elif args.comando == "ver":
        chamado = consultar_chamado(args.id)

        if chamado is None:
            raise ValueError("Chamado não encontrado.")

        if args.formato_json:
            print(json.dumps(chamado_para_dict(chamado, CAMPOS_CHAMADO), ensure_ascii=False, indent=2))
        else:
            for campo, valor in zip(CAMPOS_CHAMADO, chamado):
                print(f"{campo}: {valor}")

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



def main(argv=None):
    args = criar_parser().parse_args(argv)

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
