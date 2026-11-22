"""Módulo simulado de um sistema legado de pedidos. Valores em centavos."""


def calcular_total(subtotal, cupom):
    desconto = subtotal // 10 if cupom == "VOLTA10" else 0
    frete = 0 if subtotal >= 10000 else 1200
    return subtotal - desconto + frete


def simular_compra(subtotal, cupom):
    return {"total_estimado": calcular_total(subtotal, cupom)}


def fechar_pedido(subtotal, cupom):
    return {"status": "fechado", "valor_cobrado": calcular_total(subtotal, cupom)}


def gerar_recibo(subtotal, cupom):
    pedido = fechar_pedido(subtotal, cupom)
    return f"Total pago: {pedido['valor_cobrado']} centavos"


def validar_estoque(quantidade):
    return quantidade > 0
