"""Rastro de Mudança: evidências estáticas e classificação de anotações."""

import argparse
import ast
import json
import math
import re
from collections import Counter, defaultdict, deque
from pathlib import Path


RAIZ = Path(__file__).resolve().parent
CASO_PADRAO = RAIZ / "exemplos" / "pedidos"
REVISAO = "revisão humana"
PALAVRAS_COMUNS = set(
    "a ao aos as da das de do dos e em há na nas no nos o os ou para por que se um uma".split()
)


def termos(texto):
    return [palavra for palavra in re.findall(r"[^\W\d_]+", texto.casefold())
            if palavra not in PALAVRAS_COMUNS]


def ler_json(caminho):
    return json.loads(caminho.read_text(encoding="utf-8"))


class Classificador:
    """Naive Bayes multinomial com suavização de Laplace e opção de abstenção."""

    def __init__(self, exemplos):
        self.contagens = {
            classe: Counter(termo for frase in frases for termo in termos(frase))
            for classe, frases in exemplos.items()
        }
        self.vocabulario = set().union(*self.contagens.values())
        self.totais = {classe: sum(contagem.values()) for classe, contagem in self.contagens.items()}
        total_exemplos = sum(map(len, exemplos.values()))
        self.priores = {classe: math.log(len(frases) / total_exemplos)
                         for classe, frases in exemplos.items()}

    def prever(self, texto):
        observados = Counter(termos(texto))
        conhecidos = observados.keys() & self.vocabulario
        if len(conhecidos) < 2:
            return REVISAO, sorted(conhecidos)

        pontuacoes = {}
        for classe, contagens in self.contagens.items():
            denominador = self.totais[classe] + len(self.vocabulario)
            pontuacoes[classe] = self.priores[classe] + sum(
                observados[termo] * math.log((contagens[termo] + 1) / denominador)
                for termo in sorted(conhecidos)
            )

        primeira, segunda = sorted(pontuacoes, key=pontuacoes.get, reverse=True)[:2]
        margem = pontuacoes[primeira] - pontuacoes[segunda]
        return (primeira if margem >= math.log(2) else REVISAO), sorted(conhecidos)


def ler_codigo(caminho):
    return ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))


def chamadas(no):
    """Visita chamadas dentro da função, ignorando escopos internos."""
    nos = list(no.body)
    while nos:
        atual = nos.pop()
        if isinstance(atual, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(atual, ast.Call):
            yield atual
        nos.extend(ast.iter_child_nodes(atual))


def caminhos_de_impacto(funcoes, alvo):
    chamadores = defaultdict(set)
    for nome, corpo in funcoes.items():
        for chamada in chamadas(corpo):
            if isinstance(chamada.func, ast.Name) and chamada.func.id in funcoes:
                chamadores[chamada.func.id].add(nome)

    caminhos = {alvo: (alvo,)}
    fila = deque([alvo])
    while fila:
        atual = fila.popleft()
        for chamador in sorted(chamadores[atual] - caminhos.keys()):
            caminhos[chamador] = (chamador,) + caminhos[atual]
            fila.append(chamador)
    return caminhos


def referencias_dos_testes(caminho):
    referencias = defaultdict(list)
    for teste in ast.walk(ler_codigo(caminho)):
        if not isinstance(teste, ast.FunctionDef) or not teste.name.startswith("test_"):
            continue
        for chamada in sorted(chamadas(teste), key=lambda item: item.lineno):
            destino = chamada.func
            if (isinstance(destino, ast.Attribute) and isinstance(destino.value, ast.Name)
                    and destino.value.id == "pedidos"):
                referencias[destino.attr].append((teste.name, chamada.lineno))
    return referencias


def analisar(caso, alvo, classificador):
    codigo = caso / "pedidos.py"
    arquivo_testes = caso / "test_pedidos.py"
    funcoes = {no.name: no for no in ler_codigo(codigo).body if isinstance(no, ast.FunctionDef)}
    if alvo not in funcoes:
        raise ValueError(f"Função desconhecida: {alvo}. Opções: {', '.join(sorted(funcoes))}.")

    caminhos = caminhos_de_impacto(funcoes, alvo)
    referencias = referencias_dos_testes(arquivo_testes)
    anotacoes = ler_json(caso / "anotacoes.json")

    print(f"Mudança proposta em {alvo}\n")
    print("Caminhos estáticos até a função alterada")
    for funcao, caminho in caminhos.items():
        print(f"  {' -> '.join(caminho)} ({codigo.name}:{funcoes[funcao].lineno})")
        for teste, linha in referencias[funcao]:
            print(f"    Referência direta: {teste} ({arquivo_testes.name}:{linha})")
        if not referencias[funcao]:
            print("    Sem chamada direta encontrada nos testes")

    print("\nAnotações vinculadas às funções acima")
    selecionadas = [nota for nota in anotacoes if nota["funcao"] in caminhos]
    for nota in selecionadas:
        classe, conhecidos = classificador.prever(nota["texto"])
        print(f"  {nota['id']} [{nota['funcao']}] {classe}: {nota['texto']}")
        print(f"    Vocabulário reconhecido: {', '.join(conhecidos) or 'nenhum termo'}")
    if not selecionadas:
        print("  Nenhuma anotação vinculada.")
    print("\nValide os caminhos e os rótulos antes de tomar uma decisão.")


def avaliar(classificador):
    exemplos = ler_json(RAIZ / "dados" / "avaliacao.json")
    acertos = 0
    for exemplo in exemplos:
        previsto, _ = classificador.prever(exemplo["texto"])
        esperado = exemplo["classe"]
        acertos += previsto == esperado
        print(f"Esperado: {esperado} | Sugerido: {previsto} | {exemplo['texto']}")
    print(f"\nCoincidências com a rotulagem manual: {acertos}/{len(exemplos)} (amostra simulada).")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alvo", nargs="?", help="nome da função que seria alterada")
    parser.add_argument("--caso", type=Path, default=CASO_PADRAO, help="diretório do caso")
    parser.add_argument("--avaliar", action="store_true", help="compara rótulos em uma amostra separada")
    argumentos = parser.parse_args()
    if bool(argumentos.alvo) == argumentos.avaliar:
        parser.error("informe o nome de uma função ou use --avaliar")

    try:
        classificador = Classificador(ler_json(RAIZ / "dados" / "treino.json"))
        if argumentos.avaliar:
            avaliar(classificador)
        else:
            analisar(argumentos.caso, argumentos.alvo, classificador)
    except (OSError, ValueError, SyntaxError) as erro:
        parser.exit(1, f"Erro: {erro}\n")
