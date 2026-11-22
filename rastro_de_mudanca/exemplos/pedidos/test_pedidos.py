import unittest

import pedidos


class TestPedidos(unittest.TestCase):
    def test_simulacao_com_cupom(self):
        self.assertEqual(pedidos.simular_compra(8000, "VOLTA10"), {"total_estimado": 8400})

    def test_estoque_vazio(self):
        self.assertFalse(pedidos.validar_estoque(0))
