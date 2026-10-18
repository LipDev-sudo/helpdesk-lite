

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from main import ler_id_chamado, menu_cadastrar
from tickets import (
    cadastrar_chamado,
    listar_chamados,
    consultar_chamado,
    atualizar_status,
)



class TestCadastroChamado(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_helpdesk.db"

        self.patch_db = patch.object(
            database,
            "DATABASE_PATH",
            self.db_path,
        )
        self.patch_db.start()

        database.inicializar_banco()

    def tearDown(self):
        self.patch_db.stop()
        self.temp_dir.cleanup()

    def test_cadastrar_chamado_valido(self):
        chamado_id = cadastrar_chamado(
            "Computador sem rede",
            "Sem acesso à internet",
            "Hamilton",
            "rede",
            "alta",
        )

        with database.conexao_banco() as conexao:
            chamado = conexao.execute(
                """
                SELECT titulo, categoria, prioridade, status
                FROM chamados
                WHERE id = ?
                """,
                (chamado_id,),
            ).fetchone()

        self.assertEqual(chamado_id, 1)
        self.assertEqual(
            chamado,
            ("Computador sem rede", "rede", "alta", "aberto"),
        )

    
    def test_normalizar_categoria_e_prioridade(self):
        chamado_id = cadastrar_chamado(
            "  Impressora  ",
            "  Não imprime  ",
            "  Hamilton  ",
            "  HARDWARE  ",
            "  ALTA  ",
        )

        chamado = consultar_chamado(chamado_id)

        self.assertEqual(chamado[1], "Impressora")
        self.assertEqual(chamado[2], "Não imprime")
        self.assertEqual(chamado[3], "Hamilton")
        self.assertEqual(chamado[4], "hardware")
        self.assertEqual(chamado[5], "alta")


    def test_rejeitar_campos_obrigatorios_vazios(self):
        with self.assertRaises(ValueError):
            cadastrar_chamado("", "Descrição", "Hamilton", "rede")

    def test_rejeitar_categoria_invalida(self):
        with self.assertRaises(ValueError):
            cadastrar_chamado(
                "Erro",
                "Descrição",
                "Hamilton",
                "categoria_inexistente",
            )

    def test_rejeitar_prioridade_invalida(self):
        with self.assertRaises(ValueError):
            cadastrar_chamado(
                "Erro",
                "Descrição",
                "Hamilton",
                "rede",
                "urgente_demais",
            )
    
    def test_listar_chamados(self):
        cadastrar_chamado(
            "Computador sem rede",
            "Sem acesso à internet",
            "Hamilton",
            "rede",
            "alta",
        )

        chamados = listar_chamados()

        self.assertEqual(len(chamados), 1)
        self.assertEqual(chamados[0][1], "Computador sem rede")

    def test_filtrar_chamados_por_status(self):
        cadastrar_chamado(
            "Computador sem rede",
            "Sem acesso à internet",
            "Hamilton",
            "rede",
            "alta",
        )

        chamados = listar_chamados("aberto")

        self.assertEqual(len(chamados), 1)
        self.assertEqual(chamados[0][5], "aberto")

    def test_consultar_chamado_existente(self):
        chamado_id = cadastrar_chamado(
            "Impressora com defeito",
            "Impressora não imprime",
            "Maria",
            "hardware",
        )

        chamado = consultar_chamado(chamado_id)

        self.assertIsNotNone(chamado)
        self.assertEqual(chamado[1], "Impressora com defeito")

    def test_consultar_chamado_inexistente(self):
        chamado = consultar_chamado(9999)

        self.assertIsNone(chamado)

    
    def test_atualizar_status(self):
        chamado_id = cadastrar_chamado(
            "Computador sem rede",
            "Sem acesso à internet",
            "Hamilton",
            "rede",
        )

        atualizar_status(chamado_id, "em andamento")

        chamado = consultar_chamado(chamado_id)
        self.assertEqual(chamado[6], "em andamento")

    def test_rejeitar_status_invalido(self):
        chamado_id = cadastrar_chamado(
            "Computador sem rede",
            "Sem acesso à internet",
            "Hamilton",
            "rede",
        )

        with self.assertRaises(ValueError):
            atualizar_status(chamado_id, "urgente")

    def test_atualizar_chamado_inexistente(self):
        with self.assertRaises(ValueError):
            atualizar_status(9999, "resolvido")


class TestLerIdChamado(unittest.TestCase):

    @patch("builtins.input", return_value="2")
    def test_aceitar_id_valido(self, mock_input):
        self.assertEqual(ler_id_chamado(), 2)

    @patch("builtins.input", return_value="abc")
    def test_rejeitar_id_com_letras(self, mock_input):
        with self.assertRaisesRegex(ValueError, "Digite apenas o número"):
            ler_id_chamado()

    @patch("builtins.input", return_value="#2")
    def test_rejeitar_id_com_caractere_especial(self, mock_input):
        with self.assertRaisesRegex(ValueError, "Digite apenas o número"):
            ler_id_chamado()

    @patch("builtins.input", return_value="0")
    def test_rejeitar_id_zero(self, mock_input):
        with self.assertRaisesRegex(ValueError, "número positivo"):
            ler_id_chamado()

    @patch("builtins.input", return_value="-2")
    def test_rejeitar_id_negativo(self, mock_input):
        with self.assertRaisesRegex(ValueError, "Digite apenas o número"):
            ler_id_chamado()


class TestMenuCadastrar(unittest.TestCase):

    @patch("builtins.input", side_effect=[
        "", "Descrição", "Hamilton", "hardware", ""
    ])
    def test_rejeitar_titulo_vazio(self, mock_input):
        with self.assertRaisesRegex(
            ValueError,
            "Título, descrição e solicitante são obrigatórios",
        ):
            menu_cadastrar()

    @patch("builtins.input", side_effect=[
        "Impressora", "Não imprime", "Hamilton", "hardware", ""
    ])
    def test_usar_prioridade_padrao(self, mock_input):
        with patch("main.cadastrar_chamado", return_value=17) as cadastrar:
            menu_cadastrar()

        self.assertEqual(
            cadastrar.call_args.args,
            ("Impressora", "Não imprime", "Hamilton", "hardware", "media"),
        )





if __name__ == "__main__":
    unittest.main()
