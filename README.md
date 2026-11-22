# Rastro de Mudança

Prova de conceito para identificar o que precisa ser revisado antes de alterar uma regra em um sistema legado. A ferramenta reúne, por função, caminhos de chamada, referências nos testes existentes e anotações de manutenção classificadas por um modelo de aprendizado de máquina.

## Problema e proposta

No sistema simulado de pedidos, a equipe precisa avaliar se o limite de frete grátis deve usar o valor antes ou depois do desconto. A regra está concentrada em `calcular_total`, mas aparece na simulação de compra, na cobrança e, indiretamente, no recibo. O manual ficou incompleto e os testes disponíveis exercitam apenas parte desses fluxos. As possíveis causas são mudanças comerciais acompanhadas de atualizações parciais no manual e nos testes. A dívida aparece no próximo pedido de mudança como trabalho de investigação adicional e risco de divergência entre a cobrança e a política comercial.

A PoC auxilia quem mantém o código ou revisa uma mudança. O desenvolvedor informa a função que pretende alterar. O programa usa a árvore sintática do código Python para percorrer chamadas no sentido inverso, cruza as funções encontradas com as referências diretas dos testes e recupera as anotações vinculadas a elas. O diferencial é apresentar a triagem das anotações no contexto de uma mudança específica, junto com as evidências que o mantenedor pode abrir e conferir.

## Início rápido

Na raiz do repositório, use Python 3.9 ou superior. A demonstração roda localmente com a biblioteca padrão do Python.

```sh
python3 -m rastro_de_mudanca calcular_total
python3 -m rastro_de_mudanca validar_estoque
python3 -m rastro_de_mudanca --avaliar
```

Na primeira execução, procure o caminho `gerar_recibo -> fechar_pedido -> calcular_total`. O relatório aponta a chamada direta do teste `test_simulacao_com_cupom` a `simular_compra`. A ausência de referência direta à cobrança ou ao recibo precisa ser investigada antes de concluir sobre cobertura. As anotações simuladas `PED-18` e `PED-27` sugerem revisar documentação e testes, respectivamente. `PED-31` vai para revisão humana. A segunda execução mostra que, ao escolher uma função de estoque, o programa recupera a anotação vinculada a estoque.

### Instalação opcional

Em um ambiente virtual Python ativo, instale o pacote e execute o comando de terminal `rastro-de-mudanca`.

```sh
python -m pip install .
rastro-de-mudanca calcular_total
```

### Usar outro caso

```sh
python3 -m rastro_de_mudanca nome_da_funcao --caso caminho/do/caso
```

Use o [exemplo de pedidos](rastro_de_mudanca/exemplos/pedidos/) como referência. O diretório deve conter `pedidos.py` com funções no nível do módulo, `test_pedidos.py` com chamadas no formato `pedidos.nome_da_funcao(...)` dentro de funções `test_...` e `anotacoes.json` com uma lista de registros contendo `id`, `funcao` e `texto`.

## Papel da IA e verificação

O modelo de IA é um classificador Naive Bayes multinomial, treinado localmente com [18 anotações simuladas] rotuladas em português. Ele aprende frequências de palavras por categoria e sugere rótulos de testes, documentação ou implementação. A opção de revisão humana é acionada quando há menos de dois termos reconhecidos ou quando a melhor pontuação supera a segunda por uma margem inferior a `log(2)`. Esse limiar é uma heurística. O programa exibe o vocabulário reconhecido para facilitar a conferência da sugestão. A análise de código e o cruzamento com testes são determinísticos. A PoC dispensa serviços externos, LLMs e credenciais.

O comando `--avaliar` compara previsões com [oito exemplos simulados] que estão fora do treino. Nesta amostra, sete sugestões coincidiram com os rótulos manuais. No exemplo que cita manual, testes e função, o modelo sugeriu testes e a revisão manual indicava ambiguidade. A amostra é pequena e foi escrita para a PoC. Para avaliar generalização, seria preciso rotular uma amostra de anotações reais e medir erros por categoria e frequência de abstenção.

A análise estática desta versão cobre chamadas diretas pelo nome entre funções livres de um módulo Python. Aliases, métodos, chamadas dinâmicas e integrações entre módulos exigiriam uma análise adicional. Uma chamada encontrada em um teste é uma pista para investigar o cenário e suas asserções. A classificação de uma anotação depende do vocabulário do treino e pode errar com sinônimos, contexto implícito ou descrições de várias dívidas.

## Como usar o resultado para decidir

Para mudar a regra de frete, a primeira ação seria confirmar com o responsável pelo produto qual valor define o limite e construir testes de caracterização para cobrança e recibo, especialmente no limite de R$ 100 com cupom. Esses testes registram o comportamento atual que a equipe precisa conhecer antes da intervenção. Após confirmar a mudança, a equipe ajustaria as expectativas do cenário afetado de forma intencional e validaria os demais. O principal da dívida é o esforço de completar os testes e atualizar a documentação. Os juros aparecem na investigação adicional e no retrabalho a cada nova mudança na regra.

## Estrutura e testes

| Caminho | Conteúdo |
| --- | --- |
| [`rastro_de_mudanca/`](rastro_de_mudanca/) | Analisador de chamadas, classificador e interface de terminal. |
| [`rastro_de_mudanca/exemplos/pedidos/`](rastro_de_mudanca/exemplos/pedidos/) | Sistema legado simulado, suas anotações e testes de exemplo. |
| [`rastro_de_mudanca/dados/`](rastro_de_mudanca/dados/) | Amostras rotuladas de treino e avaliação. |
| [`tests/`](tests/) | Testes da ferramenta. |

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s rastro_de_mudanca/exemplos/pedidos -v
```

O GitHub Actions executa as duas suítes e verifica a demonstração após instalar o pacote. Para contribuir, abra uma issue com o cenário e o comando que reproduz o problema ou envie um pull request com a alteração e sua verificação.

## Licença

Projeto desenvolvido para o trabalho integrador LegacyTech de Tópicos em Engenharia de Software da PUC Minas e disponibilizado sob a [licença MIT](LICENSE).

[18 anotações simuladas]: rastro_de_mudanca/dados/treino.json
[oito exemplos simulados]: rastro_de_mudanca/dados/avaliacao.json
