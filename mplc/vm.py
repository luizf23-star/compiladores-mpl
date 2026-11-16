"""Entrega 4: maquina de pilha com um registro de ativacao por chamada.

O interpretador e iterativo: a recursao MPL usa a nossa pilha de quadros,
sem depender do limite de recursao do Python.
"""
import json
from dataclasses import dataclass, field

from mplc.erros import ErroMPL


LIMITE_QUADROS = 1024


def erro(linha, coluna, mensagem):
    raise ErroMPL('execucao', linha, coluna, mensagem)


def carregar(texto):
    linhas = texto.splitlines()
    if not linhas or linhas[0].strip() != 'MPLB 1':
        erro(1, 1, 'cabecalho MPLB 1 ausente')
    funcoes = {}
    atual = None
    try:
        for texto_linha in linhas[1:]:
            if not texto_linha.strip():
                continue
            op, _, argumento = texto_linha.strip().partition(' ')
            args = json.loads(argumento)
            if not isinstance(args, list):
                raise ValueError('argumentos devem formar uma lista')
            if op == 'FUNC':
                if atual is not None:
                    raise ValueError('funcao anterior sem END')
                nome, retorno, parametros = args
                if nome in funcoes:
                    raise ValueError('funcao duplicada')
                atual = {'retorno': retorno, 'parametros': parametros,
                         'codigo': [], 'rotulos': {}}
                funcoes[nome] = atual
            elif op == 'END':
                if atual is None or args:
                    raise ValueError('END fora de funcao')
                atual = None
            elif atual is None:
                raise ValueError('instrucao fora de funcao')
            elif op == 'LABEL':
                rotulo, = args
                if rotulo in atual['rotulos']:
                    raise ValueError('rotulo duplicado')
                atual['rotulos'][rotulo] = len(atual['codigo'])
            else:
                atual['codigo'].append((op, args))
        if atual is not None:
            raise ValueError('funcao sem END')
        if ('principal' not in funcoes or funcoes['principal']['parametros']
                or funcoes['principal']['retorno'] != 'vazio'):
            raise ValueError('entrada principal invalida')
    except (ValueError, TypeError, KeyError) as exc:
        erro(1, 1, f'bytecode invalido: {exc}')
    return funcoes


@dataclass
class Quadro:
    funcao: dict
    locais: dict
    operandos: list = field(default_factory=list)
    ip: int = 0
    linha: int = 1
    coluna: int = 1


def quociente_inteiro(a, b):
    """Trunca para zero sem passar por float, mesmo para inteiros grandes."""
    quociente = abs(a) // abs(b)
    return -quociente if (a < 0) != (b < 0) else quociente


def formatar(valor):
    if type(valor) is bool:
        return 'verdadeiro' if valor else 'falso'
    if type(valor) is float:
        return f'{valor:.6f}'
    return str(valor)


class Maquina:
    def __init__(self, funcoes, saida):
        self.funcoes = funcoes
        self.saida = saida
        self.quadros = [Quadro(funcoes['principal'], {})]

    @staticmethod
    def falhar(q, mensagem):
        erro(q.linha, q.coluna, mensagem)

    def binario(self, q, op):
        b = q.operandos.pop()
        a = q.operandos.pop()
        if op in ('DIV', 'MOD'):
            if b == 0:
                self.falhar(q, 'divisao por zero')
            if op == 'MOD':
                valor = a - quociente_inteiro(a, b) * b
            elif type(a) is int and type(b) is int:
                valor = quociente_inteiro(a, b)
            else:
                valor = a / b
        elif op == 'ADD':
            valor = a + b
        elif op == 'SUB':
            valor = a - b
        elif op == 'MUL':
            valor = a * b
        elif op == 'EQ':
            valor = a == b
        elif op == 'NE':
            valor = a != b
        elif op == 'LT':
            valor = a < b
        elif op == 'LE':
            valor = a <= b
        elif op == 'GT':
            valor = a > b
        elif op == 'GE':
            valor = a >= b
        elif op == 'AND':
            valor = a and b
        elif op == 'OR':
            valor = a or b
        else:
            self.falhar(q, f'operacao desconhecida: {op}')
        q.operandos.append(valor)

    def instrucao(self, q, op, args):
        if op == 'LINE':
            q.linha, q.coluna = args
        elif op == 'CONST':
            tipo, valor = args
            conversores = {'inteiro': int, 'real': float, 'logico': bool, 'texto': str}
            q.operandos.append(conversores[tipo](valor))
        elif op == 'LOAD':
            q.operandos.append(q.locais[args[0]])
        elif op == 'STORE':
            q.locais[args[0]] = q.operandos.pop()
        elif op == 'I2R':
            q.operandos.append(float(q.operandos.pop()))
        elif op in ('ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'EQ', 'NE', 'LT', 'LE',
                    'GT', 'GE', 'AND', 'OR'):
            self.binario(q, op)
        elif op == 'NEG':
            q.operandos.append(-q.operandos.pop())
        elif op == 'NOT':
            q.operandos.append(not q.operandos.pop())
        elif op == 'JMP':
            q.ip = q.funcao['rotulos'][args[0]]
        elif op == 'JZ':
            if not q.operandos.pop():
                q.ip = q.funcao['rotulos'][args[0]]
        elif op == 'CALL':
            nome, quantidade = args
            funcao = self.funcoes[nome]
            if quantidade != len(funcao['parametros']) or quantidade > len(q.operandos):
                self.falhar(q, 'quantidade de argumentos invalida')
            if len(self.quadros) >= LIMITE_QUADROS:
                self.falhar(q, f'estouro de pilha: limite de {LIMITE_QUADROS} chamadas')
            argumentos = q.operandos[-quantidade:] if quantidade else []
            if quantidade:
                del q.operandos[-quantidade:]
            locais = {p[0]: valor for p, valor in zip(funcao['parametros'], argumentos)}
            self.quadros.append(Quadro(funcao, locais))
        elif op == 'RET':
            quantidade, = args
            esperado = 0 if q.funcao['retorno'] == 'vazio' else 1
            if quantidade != esperado:
                self.falhar(q, 'retorno incompativel com a funcao')
            valor = q.operandos.pop() if quantidade else None
            if q.operandos:
                self.falhar(q, 'pilha de operandos desequilibrada no retorno')
            self.quadros.pop()
            if quantidade and self.quadros:
                self.quadros[-1].operandos.append(valor)
        elif op == 'WRITE':
            self.saida.write(formatar(q.operandos.pop()) + '\n')
        else:
            self.falhar(q, f'instrucao desconhecida: {op}')

    def rodar(self):
        while self.quadros:
            q = self.quadros[-1]
            if q.ip >= len(q.funcao['codigo']):
                self.falhar(q, 'fim de funcao sem retorno')
            op, args = q.funcao['codigo'][q.ip]
            q.ip += 1
            try:
                self.instrucao(q, op, args)
            except (IndexError, KeyError, ValueError, TypeError, OverflowError) as exc:
                self.falhar(q, f'instrucao {op} invalida: {exc}')


def executar(texto_mplb, saida):
    Maquina(carregar(texto_mplb), saida).rodar()
