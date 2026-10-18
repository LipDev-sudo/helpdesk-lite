
from database import inicializar_banco
from tickets import (
    cadastrar_chamado,
    listar_chamados,
    consultar_chamado,
    atualizar_status,
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



def main():
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


if __name__ == "__main__":
    main()
