# Compiladores MPL

Trabalho semestral de Compiladores — implementação da **MPL (Minha Pequena Linguagem)**.

## Entrega 1 — Analisador léxico

O analisador está em `mplc/lexico.py`. Ele percorre o fonte caractere a caractere, mantém linha e coluna iniciando em 1 e produz a lista de tokens terminada por `FIM_ARQUIVO`.

### Tabela de tokens

| Token(s) | Forma reconhecida |
|---|---|
| `FUNCAO`, `RETORNE`, `SE`, `SENAO`, `ENQUANTO`, `ESCREVA` | palavras exatas `funcao`, `retorne`, `se`, `senao`, `enquanto`, `escreva` |
| `TIPO_INTEIRO`, `TIPO_REAL`, `TIPO_LOGICO`, `TIPO_TEXTO`, `TIPO_VAZIO` | palavras exatas `inteiro`, `real`, `logico`, `texto`, `vazio` |
| `LOGICO` | `verdadeiro` ou `falso` |
| `E`, `OU`, `NAO` | palavras exatas `e`, `ou`, `nao` |
| `ID` | `[A-Za-z_][A-Za-z0-9_]*`, desde que não seja palavra reservada |
| `INTEIRO` | `[0-9]+` |
| `REAL` | `[0-9]+\.[0-9]+` — há dígitos obrigatórios dos dois lados do ponto |
| `TEXTO` | aspas duplas; dentro delas são aceitos caracteres de uma única linha e apenas os escapes `\\n`, `\\t`, `\\\"` e `\\\\` |
| `IGUAL`, `DIFERENTE`, `MENOR_IGUAL`, `MAIOR_IGUAL` | `==`, `!=`, `<=`, `>=`; são testados antes dos operadores de um caractere |
| `MAIS`, `MENOS`, `VEZES`, `DIVIDE`, `RESTO` | `+`, `-`, `*`, `/`, `%` |
| `MENOR`, `MAIOR`, `ATRIBUI` | `<`, `>`, `=` |
| `ABRE_PAR`, `FECHA_PAR` | `(`, `)` |
| `ABRE_CHAVE`, `FECHA_CHAVE` | `{`, `}` |
| `VIRGULA`, `PONTO_VIRGULA` | `,`, `;` |
| `FIM_ARQUIVO` | fim da entrada; lexema vazio |

Espaços, tabulações e quebras de linha apenas separam tokens. Comentários `// ...` são ignorados até o fim da linha e comentários `/* ... */` são ignorados até o primeiro fechamento, podendo atravessar linhas.

### Erros léxicos

O lexer interrompe no primeiro erro e gera `ErroMPL` na fase `lexico`. São rejeitados, entre outros, escape de texto desconhecido, comentário de bloco não fechado, texto não fechado, `3.`, `.5` e caracteres que não pertencem à linguagem. A posição apontada é a do caractere que inicia o problema; para texto/comentário não fechado é a posição de abertura.

## Entrega 2 — Analisador sintático e árvore

O parser em `mplc/sintatico.py` usa descida recursiva e produz a árvore descrita em `CONTRATOS.md`. Sua gramática em EBNF usa os nomes de token definidos pelo analisador léxico:

```ebnf
programa       = { funcao }, FIM_ARQUIVO ;
funcao         = FUNCAO, tipo_retorno, ID, ABRE_PAR,
                 [ parametro, { VIRGULA, parametro } ], FECHA_PAR, bloco ;
tipo_retorno   = tipo | TIPO_VAZIO ;
tipo           = TIPO_INTEIRO | TIPO_REAL | TIPO_LOGICO | TIPO_TEXTO ;
parametro      = tipo, ID ;
bloco          = ABRE_CHAVE, { comando }, FECHA_CHAVE ;
comando        = tipo, ID, [ ATRIBUI, expressao ], PONTO_VIRGULA
               | ID, ATRIBUI, expressao, PONTO_VIRGULA
               | chamada, PONTO_VIRGULA
               | SE, ABRE_PAR, expressao, FECHA_PAR, bloco, [ SENAO, bloco ]
               | ENQUANTO, ABRE_PAR, expressao, FECHA_PAR, bloco
               | ESCREVA, ABRE_PAR, expressao, FECHA_PAR, PONTO_VIRGULA
               | RETORNE, [ expressao ], PONTO_VIRGULA
               | bloco ;

expressao      = disjuncao ;
disjuncao      = conjuncao, { OU, conjuncao } ;
conjuncao      = igualdade, { E, igualdade } ;
igualdade      = relacional, { ( IGUAL | DIFERENTE ), relacional } ;
relacional     = aditivo, { ( MENOR | MENOR_IGUAL | MAIOR | MAIOR_IGUAL ), aditivo } ;
aditivo        = multiplicativo, { ( MAIS | MENOS ), multiplicativo } ;
multiplicativo = unario, { ( VEZES | DIVIDE | RESTO ), unario } ;
unario         = ( NAO | MENOS ), unario | primario ;
primario       = chamada | ID | INTEIRO | REAL | LOGICO | TEXTO
               | ABRE_PAR, expressao, FECHA_PAR ;
chamada        = ID, ABRE_PAR, [ expressao, { VIRGULA, expressao } ], FECHA_PAR ;
```

A precedência está codificada pela cadeia `disjuncao → conjuncao → igualdade → relacional → aditivo → multiplicativo → unario → primario`: cada nível chama o seguinte, mais forte. Os laços `{ ... }` dos binários constroem a árvore pela esquerda; `unario` chama a si mesmo à direita.

## Comandos

```bash
./compilar --tokens exemplos/ola.mpl
./compilar --ast exemplos/tudo.mpl
make verificar E=1
make verificar E=2
make evidencias E=2
make prova E=2
```

## Entrega 3 — Tabela de simbolos e verificacao de tipos

Os escopos foram representados com objetos `Escopo` ligados ao escopo-pai, cada um com um dicionario de simbolos. Assim, a busca percorre o escopo atual ate seus pais e permite que uma declaracao interna esconda uma variavel externa sem altera-la. A `Tabela` tambem guarda os escopos na ordem de abertura para gerar o formato solicitado em `--tabela`. A analise passa duas vezes pelas funcoes: primeiro registra as assinaturas globais e depois valida os comandos e os tipos, permitindo chamadas de funcoes declaradas adiante e recursao mutua.

### Verificacao da E3

```bash
./compilar --tabela exemplos/tudo.mpl
make verificar E=3
make evidencias E=3
make prova E=3
```


## Entrega 4 — Código intermediário, geração e máquina virtual

A AST anotada pela semântica vira código de três endereços em
`mplc/intermediario.py`. O módulo `mplc/gerador.py` traduz cada operação
para instruções de pilha; `mplc/vm.py` carrega e executa o arquivo textual
`.mplb`. Só é necessária a biblioteca padrão do Python 3.

### Representação intermediária e tipos

Cada expressão gera um temporário, com no máximo um operador por linha.
Em `x = a + b * c`, a multiplicação e a soma ocupam instruções diferentes.
Rótulos representam os destinos dos desvios do `se` e do `enquanto`.
O laço volta ao rótulo anterior à condição, recalculando-a.

Os locais são renomeados por declaração: `v0_x`, `v1_x` etc. Dois blocos
podem declarar `x` sem compartilhar o mesmo local. Os temporários `t0`,
`t1` etc. ficam separados desses nomes. Declarações dentro de um laço
executam a inicialização a cada passagem.

A conversão de inteiro para real é explícita na IR e vira `I2R`.
Na atribuição, no argumento e no retorno, ela ocorre depois de calcular a
expressão. Assim, `real x = 7 / 2;` imprime `3.000000`. Operandos numéricos
de tipos diferentes são promovidos antes da operação.

A divisão inteira calcula o quociente dos valores absolutos e ajusta o sinal,
sem converter para ponto flutuante. O resto é `a - quociente(a,b) * b`,
mantendo o sinal do dividendo. Os operadores `e` e `ou` avaliam os dois
operandos, da esquerda para a direita, conforme a especificação.

### Formato legível do executável

O arquivo começa com `MPLB 1`. Cada linha seguinte contém uma instrução
seguida de seus argumentos em JSON. A VM não usa `eval` nem `exec`.
Um exemplo reduzido:

```text
MPLB 1
FUNC ["principal", "vazio", []]
LINE [2, 3]
CONST ["inteiro", 42]
STORE ["t0"]
LOAD ["t0"]
WRITE []
RET [0]
END []
```

`FUNC` informa nome, tipo de retorno e pares `[local, tipo]` dos parâmetros.
`LABEL` dá nome à posição da próxima instrução. `LINE` preserva a posição
do comando MPL original. O carregador resolve os rótulos por função.

### Conjunto de instruções da VM

Na coluna de pilha, a direita representa o topo; `S` é o restante da pilha.
Cada registro de ativação possui sua própria pilha de operandos.

| Instrução | Efeito na pilha e comportamento |
|---|---|
| `CONST [tipo, valor]` | `S → S, valor`: empilha uma constante do tipo indicado. |
| `LOAD [local]` | `S → S, valor`: empilha uma cópia do local do quadro atual. |
| `STORE [local]` | `S, valor → S`: retira o topo e grava no local do quadro atual. |
| `I2R []` | `S, inteiro → S, real`: converte o topo para real. |
| `ADD []` | `S, a, b → S, a+b`: soma números ou concatena dois textos. |
| `SUB []` | `S, a, b → S, a-b`: subtrai. |
| `MUL []` | `S, a, b → S, a*b`: multiplica. |
| `DIV []` | `S, a, b → S, a/b`: divisão inteira truncada para zero ou divisão real; zero é erro. |
| `MOD []` | `S, a, b → S, resto`: resto inteiro com sinal de `a`; zero é erro. |
| `EQ []` | `S, a, b → S, logico`: compara igualdade. |
| `NE []` | `S, a, b → S, logico`: compara diferença. |
| `LT []` | `S, a, b → S, logico`: testa `a < b`. |
| `LE []` | `S, a, b → S, logico`: testa `a <= b`. |
| `GT []` | `S, a, b → S, logico`: testa `a > b`. |
| `GE []` | `S, a, b → S, logico`: testa `a >= b`. |
| `AND []` | `S, a, b → S, logico`: conjunção; ambos já foram avaliados. |
| `OR []` | `S, a, b → S, logico`: disjunção; ambos já foram avaliados. |
| `NEG []` | `S, a → S, -a`: inverte o sinal numérico. |
| `NOT []` | `S, a → S, nao a`: negação lógica. |
| `JMP [rotulo]` | `S → S`: muda o contador de instruções incondicionalmente. |
| `JZ [rotulo]` | `S, condicao → S`: desvia se a condição for falsa. |
| `CALL [nome, n]` | Retira `n` argumentos do chamador, preserva a ordem e cria um quadro com pilha vazia e locais próprios. |
| `RET [0]` | Exige pilha vazia, descarta o quadro e retoma o chamador. |
| `RET [1]` | Retira o retorno, exige que não sobrem operandos, descarta o quadro e empilha o valor no chamador. |
| `WRITE []` | `S, valor → S`: imprime o valor e uma quebra de linha. |
| `LINE [linha, coluna]` | `S → S`: atualiza a posição do comando fonte para mensagens de erro. |
| `FUNC [nome, retorno, parametros]` | Diretiva de carga: abre uma função; não altera a pilha. |
| `LABEL [nome]` | Diretiva de carga: registra o destino de um desvio; não altera a pilha. |
| `END []` | Diretiva de carga: fecha uma função; não altera a pilha. |

O quadro guarda os locais, a pilha de operandos, a próxima instrução e a
posição no fonte. Ao chamar uma função, o quadro do chamador permanece
suspenso. Ao retornar, ele é retomado no ponto seguinte ao `CALL`.
Isso permite recursão direta e mútua sem misturar locais de chamadas
diferentes. Os argumentos são passados por valor.

A VM usa um laço iterativo e uma pilha explícita com limite de **1.024 quadros**,
incluindo `principal`. Ultrapassar esse limite gera erro de execução na linha
da chamada que tentou criar o próximo quadro. Divisão e resto por zero também
geram `erro execucao`, na linha do comando, e o lançador termina com código 2.
Reais são impressos com seis casas decimais e lógicos como
`verdadeiro` ou `falso`.

### Programa próprio: planejador de estudos

[exemplos/planejador_estudos.mpl](exemplos/planejador_estudos.mpl) estima os
minutos restantes de uma fila de atividades e mostra o avanço semanal.
O cenário tem seis atividades, duas já concluídas, duas por semana e
trinta minutos por atividade. A função recursiva calcula os 120 minutos
restantes; o laço mostra os progressos `66.666667` e `100.000000`.

A [saída esperada](exemplos/planejador_estudos.saida) acompanha o programa.
A execução automatizada compara a saída real com esse arquivo e grava
também `evidencias/programa-proprio.txt`.

```bash
./compilar --ir exemplos/planejador_estudos.mpl
./compilar exemplos/planejador_estudos.mpl
./executar exemplos/planejador_estudos.mplb
```

### Verificação e reprodução

```bash
make verificar E=4
make prova E=4
python3 testes/testar_e4.py
make evidencias E=4
```

O verificador oficial da E4 inclui as Entregas 1, 2 e 3. O corpus oficial e
`verificar.py` foram preservados. Os testes extras cobrem divisões com todos
os sinais e inteiros grandes, conversões, escopos, recursão profunda,
ordem de avaliação, parâmetros por valor, diagnósticos e execução sem o fonte.

O fluxo [Verificar E4](.github/workflows/e4-verificacao.yml) executa a prova
num clone limpo, o verificador oficial, os testes extras e o programa próprio.
Somente após sucesso registra as evidências no Git.
`evidencias/ambiente-4.json` identifica o commit testado e a execução auditável;
os resultados são obtidos executando os programas, sem preencher logs à mão.

Para enviar, veja [o guia da E4](entregas/ENVIO-E4.md).
