import csv
import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from helpdesk_lite import cli, database
from helpdesk_lite.tickets import (
    atualizar_status,
    cadastrar_chamado,
    detalhes_chamado,
    editar_chamado,
    excluir_chamado,
    exportar_chamados,
    historico_chamado,
    listar_chamados,
    resumo,
)


class BaseBanco(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.caminho = Path(self.temp_dir.name) / "teste.db"
        self.patch_db = patch.object(database, "DATABASE_PATH", self.caminho)
        self.patch_db.start()
        database.inicializar_banco()

    def tearDown(self):
        self.patch_db.stop()
        self.temp_dir.cleanup()

    def criar(self, titulo="Sem rede", descricao="Sem acesso", solicitante="Ana", categoria="rede", prioridade="media"):
        return cadastrar_chamado(titulo, descricao, solicitante, categoria, prioridade)


class TestMigracao(unittest.TestCase):
    def test_atualiza_banco_antigo_sem_perder_dados(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "antigo.db"

            with sqlite3.connect(caminho) as conexao:
                conexao.execute("""
                    CREATE TABLE chamados (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        titulo TEXT NOT NULL, descricao TEXT NOT NULL, solicitante TEXT NOT NULL,
                        categoria TEXT NOT NULL, prioridade TEXT NOT NULL DEFAULT 'media',
                        status TEXT NOT NULL DEFAULT 'aberto',
                        criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conexao.execute(
                    "INSERT INTO chamados (titulo, descricao, solicitante, categoria, status, criado_em) "
                    "VALUES ('Antigo', 'd', 'Ana', 'rede', 'resolvido', '2026-01-01 10:00:00')"
                )
            sqlite3.connect(caminho).close()

            with patch.object(database, "DATABASE_PATH", caminho):
                database.inicializar_banco()
                database.inicializar_banco()  # idempotente

                chamado = detalhes_chamado(1)
                versao = database.conectar().execute("PRAGMA user_version").fetchone()[0]

            self.assertEqual(versao, database.SCHEMA_ATUAL)
            self.assertEqual(chamado["titulo"], "Antigo")
            self.assertEqual(chamado["atualizado_em"], "2026-01-01 10:00:00")
            self.assertEqual(chamado["resolvido_em"], "2026-01-01 10:00:00")

    def test_banco_novo_ja_nasce_na_versao_atual(self):
        with tempfile.TemporaryDirectory() as pasta:
            with patch.object(database, "DATABASE_PATH", Path(pasta) / "novo.db"):
                database.inicializar_banco()
                versao = database.conectar().execute("PRAGMA user_version").fetchone()[0]

            self.assertEqual(versao, database.SCHEMA_ATUAL)


class TestListagem(BaseBanco):
    def test_filtra_por_categoria_prioridade_e_solicitante(self):
        self.criar("A", categoria="rede", prioridade="alta", solicitante="Ana")
        self.criar("B", categoria="hardware", prioridade="alta", solicitante="Bia")
        self.criar("C", categoria="rede", prioridade="baixa", solicitante="Ana")

        titulos = lambda **filtros: [c[1] for c in listar_chamados(**filtros)]  # noqa: E731

        self.assertEqual(titulos(categoria="rede"), ["C", "A"])
        self.assertEqual(titulos(prioridade="alta"), ["B", "A"])
        self.assertEqual(titulos(solicitante="ana"), ["C", "A"])
        self.assertEqual(titulos(categoria="rede", prioridade="alta"), ["A"])

    def test_busca_por_texto_ignora_maiusculas(self):
        self.criar("Impressora quebrada", "Papel preso")
        self.criar("Sem internet", "Roteador desligado")

        self.assertEqual([c[1] for c in listar_chamados(busca="IMPRESSORA")], ["Impressora quebrada"])
        self.assertEqual([c[1] for c in listar_chamados(busca="roteador")], ["Sem internet"])

    def test_busca_trata_porcentagem_como_texto(self):
        self.criar("Uso de 100% da CPU")
        self.criar("Outro chamado")

        self.assertEqual(len(listar_chamados(busca="100%")), 1)
        self.assertEqual(len(listar_chamados(busca="%")), 1)

    def test_ordenacao(self):
        self.criar("baixa", prioridade="baixa")
        self.criar("critica", prioridade="critica")
        self.criar("media", prioridade="media")

        self.assertEqual([c[1] for c in listar_chamados(ordenar="prioridade")], ["critica", "media", "baixa"])
        self.assertEqual([c[1] for c in listar_chamados(ordenar="antigos")], ["baixa", "critica", "media"])
        self.assertEqual([c[1] for c in listar_chamados()], ["media", "critica", "baixa"])

    def test_filtros_invalidos(self):
        for filtros in ({"categoria": "x"}, {"prioridade": "x"}, {"status": "x"}, {"ordenar": "x"}):
            with self.subTest(filtros=filtros), self.assertRaises(ValueError):
                listar_chamados(**filtros)


class TestEdicaoEHistorico(BaseBanco):
    def test_editar_registra_historico_e_data(self):
        chamado_id = self.criar(prioridade="media")

        alterados = editar_chamado(chamado_id, prioridade="alta", titulo="  Novo título  ")

        detalhes = detalhes_chamado(chamado_id)
        self.assertEqual(sorted(alterados), ["prioridade", "titulo"])
        self.assertEqual(detalhes["titulo"], "Novo título")
        self.assertEqual(detalhes["prioridade"], "alta")
        eventos = [(h["evento"], h["detalhe"]) for h in historico_chamado(chamado_id)]
        self.assertIn(("editado", "prioridade: media -> alta"), eventos)
        self.assertIn(("editado", "titulo alterado"), eventos)

    def test_editar_sem_mudancas_nao_registra_nada(self):
        chamado_id = self.criar(prioridade="media")

        self.assertEqual(editar_chamado(chamado_id, prioridade="media"), [])
        self.assertEqual(len(historico_chamado(chamado_id)), 1)  # só o "criado"

    def test_editar_validacoes(self):
        chamado_id = self.criar()
        casos = (
            {},
            {"titulo": "   "},
            {"categoria": "x"},
            {"prioridade": "x"},
        )

        for campos in casos:
            with self.subTest(campos=campos), self.assertRaises(ValueError):
                editar_chamado(chamado_id, **campos)

        with self.assertRaises(ValueError):
            editar_chamado(999, titulo="x")

    def test_status_registra_historico_e_datas(self):
        chamado_id = self.criar()

        atualizar_status(chamado_id, "resolvido")
        resolvido = detalhes_chamado(chamado_id)["resolvido_em"]
        atualizar_status(chamado_id, "aberto")

        self.assertIsNotNone(resolvido)
        self.assertIsNone(detalhes_chamado(chamado_id)["resolvido_em"])
        detalhes = [h["detalhe"] for h in historico_chamado(chamado_id) if h["evento"] == "status"]
        self.assertEqual(detalhes, ["aberto -> resolvido", "resolvido -> aberto"])

    def test_mesmo_status_nao_gera_historico(self):
        chamado_id = self.criar()

        atualizar_status(chamado_id, "aberto")

        self.assertEqual(len(historico_chamado(chamado_id)), 1)

    def test_excluir_remove_o_historico(self):
        chamado_id = self.criar()
        excluir_chamado(chamado_id)

        self.assertEqual(historico_chamado(chamado_id), [])


class TestResumoEExportacao(BaseBanco):
    def test_resumo_vazio(self):
        dados = resumo()

        self.assertEqual(dados["total"], 0)
        self.assertEqual(dados["por_status"], {"aberto": 0, "em andamento": 0, "resolvido": 0})
        self.assertIsNone(dados["tempo_medio_resolucao_horas"])

    def test_resumo_com_dados(self):
        self.criar(prioridade="critica", categoria="rede")
        resolvido = self.criar(prioridade="alta", categoria="rede")
        self.criar(prioridade="baixa", categoria="hardware")
        atualizar_status(resolvido, "resolvido")

        dados = resumo()

        self.assertEqual(dados["total"], 3)
        self.assertEqual(dados["por_status"]["resolvido"], 1)
        self.assertEqual(dados["por_prioridade"]["critica"], 1)
        self.assertEqual(dados["por_categoria"]["rede"], 2)
        self.assertEqual(dados["pendentes_alta_prioridade"], 1)
        self.assertIsNotNone(dados["tempo_medio_resolucao_horas"])

    def test_exportar_csv_neutraliza_formulas(self):
        self.criar(titulo="=SOMA(A1)", solicitante="@x")

        linhas = list(csv.reader(io.StringIO(exportar_chamados("csv"))))

        self.assertEqual(linhas[0][:3], ["id", "titulo", "descricao"])
        self.assertEqual(linhas[1][1], "'=SOMA(A1)")
        self.assertEqual(linhas[1][3], "'@x")

    def test_exportar_json_filtrando_por_status(self):
        self.criar("A")
        outro = self.criar("B")
        atualizar_status(outro, "resolvido")

        dados = json.loads(exportar_chamados("json", status="resolvido"))

        self.assertEqual([c["titulo"] for c in dados], ["B"])

    def test_exportar_formato_invalido(self):
        with self.assertRaises(ValueError):
            exportar_chamados("xml")


class TestCLINova(BaseBanco):
    def executar(self, *argv):
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = cli.main(list(argv))
        return codigo, saida.getvalue(), erro.getvalue()

    def test_listar_com_filtros_e_busca(self):
        self.criar("Impressora", categoria="hardware", prioridade="alta")
        self.criar("Rede lenta", categoria="rede")

        _, saida, _ = self.executar("listar", "--busca", "impres", "--prioridade", "alta", "--json")

        self.assertEqual([c["titulo"] for c in json.loads(saida)], ["Impressora"])

    def test_editar_e_ver_com_historico(self):
        chamado_id = self.criar()

        codigo, saida, _ = self.executar("editar", str(chamado_id), "--prioridade", "critica")
        self.assertEqual(codigo, 0)
        self.assertIn("prioridade", saida)

        _, saida, _ = self.executar("ver", str(chamado_id), "--json")
        dados = json.loads(saida)
        self.assertEqual(dados["prioridade"], "critica")
        self.assertEqual(dados["historico"][-1]["detalhe"], "prioridade: media -> critica")

    def test_editar_sem_campos_retorna_erro(self):
        chamado_id = self.criar()

        codigo, _, erro = self.executar("editar", str(chamado_id))

        self.assertEqual(codigo, 1)
        self.assertIn("ao menos um campo", erro)

    def test_resumo_json(self):
        self.criar()

        _, saida, _ = self.executar("resumo", "--json")

        self.assertEqual(json.loads(saida)["total"], 1)

    def test_exportar_para_arquivo(self):
        self.criar("Exportado")
        destino = Path(self.temp_dir.name) / "saida.csv"

        codigo, _, _ = self.executar("exportar", "-o", str(destino))

        self.assertEqual(codigo, 0)
        self.assertIn("Exportado", destino.read_text(encoding="utf-8"))

    def test_opcao_db_usa_outro_arquivo(self):
        outro = Path(self.temp_dir.name) / "outro.db"

        with patch.object(database, "DATABASE_PATH", self.caminho):  # restaura o caminho após o teste
            self.executar(
                "--db",
                str(outro),
                "novo",
                "--titulo",
                "x",
                "--descricao",
                "y",
                "--solicitante",
                "Ana",
                "--categoria",
                "rede",
            )

        self.assertTrue(outro.exists())
        self.assertEqual(sqlite3.connect(outro).execute("SELECT COUNT(*) FROM chamados").fetchone()[0], 1)
        self.assertEqual(len(listar_chamados()), 0)

    def test_versao(self):
        with redirect_stdout(io.StringIO()) as saida, self.assertRaises(SystemExit) as codigo:
            cli.main(["--version"])

        self.assertEqual(codigo.exception.code, 0)
        self.assertIn("2.0.0", saida.getvalue())


if __name__ == "__main__":
    unittest.main()
