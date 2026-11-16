# Entrega 4 de Compiladores — guia de envio

Disciplina: Compiladores — Minha Pequena Linguagem (MPL).
Aluno: Luiz Fernando Marinho da Silva Bertáglia.
RA: 1055368-1.

## Enviar no formulário do professor

1. Abra https://profluiz.mantovanitec.com/disciplinas/aulas/compiladores/trabalho.html .
2. Selecione **Entrega 4 — Código intermediário, geração e VM**.
3. Confira os dados dos integrantes cadastrados no formulário.
4. Cole o repositório: https://github.com/luizf23-star/compiladores-mpl .
5. Anexe **evidencias/verificacao-4.txt**.
6. Envie e guarde o protocolo de recebimento.

Arquivo para baixar:
https://raw.githubusercontent.com/luizf23-star/compiladores-mpl/main/evidencias/verificacao-4.txt

Este guia organiza o envio; ele não é um comprovante de submissão.

## Onde conferir o trabalho

| Requisito | Arquivo |
|---|---|
| Código de três endereços | mplc/intermediario.py |
| Tradução para bytecode textual | mplc/gerador.py |
| Máquina virtual com registros de ativação | mplc/vm.py |
| Conjunto de instruções e efeito na pilha | README.md, seção Entrega 4 |
| Programa próprio | exemplos/planejador_estudos.mpl |
| Saída esperada do programa | exemplos/planejador_estudos.saida |
| Saída real do programa | evidencias/programa-proprio.txt |
| Verificação oficial e entregas anteriores | evidencias/verificacao-4.txt |
| Verificação num clone limpo | evidencias/prova-4.txt |
| Testes adicionais | evidencias/testes-extras-4.txt |
| Commit testado e identificação da execução | evidencias/ambiente-4.json |

## Demonstração rápida

Na raiz do repositório, com Python 3 instalado:

```bash
make verificar E=4
./compilar --ir exemplos/planejador_estudos.mpl
./compilar exemplos/planejador_estudos.mpl
./executar exemplos/planejador_estudos.mplb
```

O planejador parte de seis atividades, duas concluídas e duas por semana.
Calcula 120 minutos restantes com uma função recursiva e conclui em duas
semanas. A porcentagem usa conversão numérica e é impressa com seis casas.
Aumente o total para 7 e execute novamente para observar o tratamento da
última semana com menos atividades.

Pontos para explicar: cada temporário da IR tem uma única operação; o
gerador troca essa operação por cargas, operação e armazenamento; a VM
mantém um quadro independente por chamada, permitindo a recursão.
