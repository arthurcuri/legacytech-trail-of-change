import io
import unittest
from contextlib import redirect_stdout

from rastro_de_mudanca.cli import CASO_PADRAO, RAIZ, REVISAO, Classificador, analisar, ler_json


class TestAnalise(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classificador = Classificador(ler_json(RAIZ / "dados" / "treino.json"))

    def test_exibe_impacto_indireto_e_referencia_de_teste(self):
        saida = io.StringIO()
        with redirect_stdout(saida):
            analisar(CASO_PADRAO, "calcular_total", self.classificador)

        relatorio = saida.getvalue()
        self.assertIn("gerar_recibo -> fechar_pedido -> calcular_total", relatorio)
        self.assertIn("Referência direta: test_simulacao_com_cupom", relatorio)
        self.assertIn("PED-18 [calcular_total] documentação", relatorio)
        self.assertNotIn("EST-04", relatorio)

    def test_rejeita_funcao_desconhecida(self):
        with self.assertRaisesRegex(ValueError, "Função desconhecida"):
            analisar(CASO_PADRAO, "inexistente", self.classificador)

    def test_classifica_anotacao_de_testes(self):
        classe, _ = self.classificador.prever("Precisamos de testes automatizados no caminho de erro.")
        self.assertEqual(classe, "testes")

    def test_encaminha_anotacao_com_pouca_evidencia_para_revisao(self):
        classe, _ = self.classificador.prever("O recibo deve ser impresso em papel azul.")
        self.assertEqual(classe, REVISAO)
