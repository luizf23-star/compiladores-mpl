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

## Comandos

```bash
./compilar --tokens exemplos/ola.mpl
make verificar E=1
make evidencias E=1
make prova E=1
```
