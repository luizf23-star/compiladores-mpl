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
