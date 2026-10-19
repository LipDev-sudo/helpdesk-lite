import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import database
import main
from tickets import consultar_chamado, excluir_chamado, cadastrar_chamado


class BaseCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patch_db = patch.object(
            database, "DATABASE_PATH", Path(self.temp_dir.name) / "test.db"
        )
        self.patch_db.start()
        database.inicializar_banco()

    def tearDown(self):
        self.patch_db.stop()
        self.temp_dir.cleanup()

    def executar(self, *argv):
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = main.main(list(argv))
        return codigo, saida.getvalue(), erro.getvalue()

    def criar(self, titulo="Sem rede"):
        return cadastrar_chamado(titulo, "Descrição", "Ana", "rede", "alta")


class TestExcluirChamado(BaseCLI):
    def test_excluir_existente(self):
        chamado_id = self.criar()

        self.assertTrue(excluir_chamado(chamado_id))
        self.assertIsNone(consultar_chamado(chamado_id))

    def test_excluir_inexistente(self):
        with self.assertRaises(ValueError):
            excluir_chamado(99)


class TestSubcomandos(BaseCLI):
    def test_novo_e_listar_json(self):
        codigo, saida, _ = self.executar(
            "novo", "--titulo", "Teclado", "--descricao", "Falha",
            "--solicitante", "Ana", "--categoria", "hardware",
        )
        self.assertEqual(codigo, 0)
        self.assertIn("#1", saida)

        codigo, saida, _ = self.executar("listar", "--json")
        dados = json.loads(saida)
        self.assertEqual(codigo, 0)
        self.assertEqual(dados[0]["titulo"], "Teclado")
        self.assertEqual(dados[0]["prioridade"], "media")
        self.assertEqual(dados[0]["status"], "aberto")

    def test_listar_filtra_por_status(self):
        self.criar("A")
        outro = self.criar("B")
        self.executar("status", str(outro), "resolvido")

        _, saida, _ = self.executar("listar", "--status", "resolvido", "--json")

        self.assertEqual([c["titulo"] for c in json.loads(saida)], ["B"])

    def test_ver_json(self):
        chamado_id = self.criar()

        _, saida, _ = self.executar("ver", str(chamado_id), "--json")

        self.assertEqual(json.loads(saida)["solicitante"], "Ana")

    def test_ver_inexistente_retorna_erro(self):
        codigo, _, erro = self.executar("ver", "42")

        self.assertEqual(codigo, 1)
        self.assertIn("não encontrado", erro)

    def test_atualizar_status(self):
        chamado_id = self.criar()

        codigo, _, _ = self.executar("status", str(chamado_id), "em andamento")

        self.assertEqual(codigo, 0)
        self.assertEqual(consultar_chamado(chamado_id)[6], "em andamento")

    def test_excluir_com_sim(self):
        chamado_id = self.criar()

        codigo, _, _ = self.executar("excluir", str(chamado_id), "--sim")

        self.assertEqual(codigo, 0)
        self.assertIsNone(consultar_chamado(chamado_id))

    @patch("builtins.input", return_value="n")
    def test_excluir_cancelado(self, _input):
        chamado_id = self.criar()

        self.executar("excluir", str(chamado_id))

        self.assertIsNotNone(consultar_chamado(chamado_id))

    def test_titulo_vazio_retorna_erro(self):
        codigo, _, erro = self.executar(
            "novo", "--titulo", " ", "--descricao", "x",
            "--solicitante", "Ana", "--categoria", "rede",
        )

        self.assertEqual(codigo, 1)
        self.assertIn("obrigatórios", erro)

    def test_categoria_invalida_rejeitada_pelo_parser(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
            main.main([
                "novo", "--titulo", "x", "--descricao", "x",
                "--solicitante", "Ana", "--categoria", "invalida",
            ])

        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
