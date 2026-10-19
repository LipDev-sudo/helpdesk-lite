import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from helpdesk_lite import cli, database
from helpdesk_lite.tickets import cadastrar_chamado, consultar_chamado, detalhes_chamado


class BaseMenu(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patch_db = patch.object(database, "DATABASE_PATH", Path(self.temp_dir.name) / "menu.db")
        self.patch_db.start()
        database.inicializar_banco()

    def tearDown(self):
        self.patch_db.stop()
        self.temp_dir.cleanup()

    def rodar(self, funcao, entradas):
        saida = io.StringIO()
        with patch("builtins.input", side_effect=entradas), redirect_stdout(saida):
            funcao()
        return saida.getvalue()

    def criar(self, titulo="Sem rede", prioridade="media"):
        return cadastrar_chamado(titulo, "Descrição", "Ana", "rede", prioridade)


class TestMenus(BaseMenu):
    def test_listar_todos_e_vazio(self):
        self.assertIn("Nenhum chamado encontrado", self.rodar(cli.menu_listar, ["1"]))

        self.criar("Impressora")
        self.assertIn("Impressora", self.rodar(cli.menu_listar, ["1"]))

    def test_listar_por_status(self):
        self.criar("Aberto")

        self.assertIn("Aberto", self.rodar(cli.menu_listar, ["2"]))
        self.assertIn("Nenhum chamado encontrado", self.rodar(cli.menu_listar, ["4"]))

    def test_listar_busca_por_texto(self):
        self.criar("Impressora quebrada")
        self.criar("Sem internet")

        saida = self.rodar(cli.menu_listar, ["5", "impress"])

        self.assertIn("Impressora quebrada", saida)
        self.assertNotIn("Sem internet", saida)

    def test_listar_opcao_invalida(self):
        self.assertIn("Opção inválida", self.rodar(cli.menu_listar, ["9"]))

    def test_consultar_mostra_historico(self):
        chamado_id = self.criar()

        saida = self.rodar(cli.menu_consultar, [str(chamado_id)])

        self.assertIn("Título: Sem rede", saida)
        self.assertIn("Histórico:", saida)
        self.assertIn("criado", saida)

    def test_consultar_inexistente(self):
        self.assertIn("não encontrado", self.rodar(cli.menu_consultar, ["99"]))

    def test_atualizar_status(self):
        chamado_id = self.criar()

        self.rodar(cli.menu_atualizar_status, [str(chamado_id), "resolvido"])

        self.assertEqual(consultar_chamado(chamado_id)[6], "resolvido")

    def test_atualizar_status_inexistente(self):
        self.assertIn("não encontrado", self.rodar(cli.menu_atualizar_status, ["99"]))

    def test_editar_somente_campos_preenchidos(self):
        chamado_id = self.criar()

        saida = self.rodar(cli.menu_editar, [str(chamado_id), "", "", "", "", "critica"])

        self.assertIn("prioridade", saida)
        self.assertEqual(detalhes_chamado(chamado_id)["prioridade"], "critica")

    def test_editar_sem_alteracoes(self):
        chamado_id = self.criar()

        self.assertIn("Nenhuma alteração", self.rodar(cli.menu_editar, [str(chamado_id), "", "", "", "", ""]))

    def test_editar_inexistente(self):
        self.assertIn("não encontrado", self.rodar(cli.menu_editar, ["99"]))

    def test_excluir_confirmado_e_cancelado(self):
        chamado_id = self.criar()

        self.assertIn("cancelada", self.rodar(cli.menu_excluir, [str(chamado_id), "n"]))
        self.assertIsNotNone(consultar_chamado(chamado_id))

        self.assertIn("excluído", self.rodar(cli.menu_excluir, [str(chamado_id), "s"]))
        self.assertIsNone(consultar_chamado(chamado_id))

    def test_excluir_inexistente(self):
        self.assertIn("não encontrado", self.rodar(cli.menu_excluir, ["99"]))

    def test_resumo(self):
        self.criar(prioridade="critica")

        saida = self.rodar(cli.menu_resumo, [])

        self.assertIn("Total de chamados: 1", saida)
        self.assertIn("Tempo médio de resolução: N/D", saida)


class TestLoopInterativo(BaseMenu):
    def test_navega_pelo_menu_e_sai(self):
        # opção inválida, vazio (ignorado), resumo, e sair
        entradas = ["x", "", "", "7", "", "0"]

        saida = self.rodar(cli.menu_interativo, entradas)

        self.assertIn("Opção inválida", saida)
        self.assertIn("Total de chamados", saida)
        self.assertIn("Encerrando o HelpDesk Lite.", saida)

    def test_erro_de_validacao_nao_derruba_o_menu(self):
        # consultar com ID inválido gera ValueError tratado pelo loop
        entradas = ["3", "abc", "", "0"]

        saida = self.rodar(cli.menu_interativo, entradas)

        self.assertIn("Erro: Digite apenas o número do ID", saida)
        self.assertIn("Encerrando", saida)

    def test_ctrl_d_durante_uma_acao_cancela_a_operacao(self):
        entradas = ["1", EOFError(), "", "0"]

        saida = self.rodar(cli.menu_interativo, entradas)

        self.assertIn("Operação cancelada.", saida)


if __name__ == "__main__":
    unittest.main()
