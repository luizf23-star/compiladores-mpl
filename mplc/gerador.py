"""Entrega 4: tres enderecos para bytecode textual de uma VM de pilha."""
import json


BINARIOS = {
    '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '%': 'MOD',
    '==': 'EQ', '!=': 'NE', '<': 'LT', '<=': 'LE', '>': 'GT', '>=': 'GE',
    'e': 'AND', 'ou': 'OR',
}
UNARIOS = {'-': 'NEG', 'nao': 'NOT'}


def gerar(codigo_intermediario):
    linhas = ['MPLB 1']

    def emitir(op, *args):
        linhas.append(op + ' ' + json.dumps(args, ensure_ascii=False))

    for funcao in codigo_intermediario:
        parametros = [[p['local'], p['tipo']] for p in funcao['parametros']]
        emitir('FUNC', funcao['nome'], funcao['retorno'], parametros)
        for i in funcao['instrucoes']:
            # Cada operacao guarda a posicao do COMANDO MPL, para diagnosticos.
            emitir('LINE', i['linha'], i['coluna'])
            op = i['op']
            if op == 'constante':
                emitir('CONST', i['tipo'], i['valor'])
                emitir('STORE', i['destino'])
            elif op in ('copia', 'real'):
                emitir('LOAD', i['origem'])
                if op == 'real':
                    emitir('I2R')
                emitir('STORE', i['destino'])
            elif op == 'binario':
                emitir('LOAD', i['esquerdo'])
                emitir('LOAD', i['direito'])
                emitir(BINARIOS[i['operador']])
                emitir('STORE', i['destino'])
            elif op == 'unario':
                emitir('LOAD', i['origem'])
                emitir(UNARIOS[i['operador']])
                emitir('STORE', i['destino'])
            elif op == 'chame':
                for argumento in i['argumentos']:
                    emitir('LOAD', argumento)
                emitir('CALL', i['nome'], len(i['argumentos']))
                if i['destino'] is not None:
                    emitir('STORE', i['destino'])
            elif op == 'rotulo':
                emitir('LABEL', i['nome'])
            elif op == 'desvie':
                emitir('JMP', i['rotulo'])
            elif op == 'se_falso':
                emitir('LOAD', i['origem'])
                emitir('JZ', i['rotulo'])
            elif op == 'escreva':
                emitir('LOAD', i['origem'])
                emitir('WRITE')
            elif op == 'retorne':
                if i['origem'] is not None:
                    emitir('LOAD', i['origem'])
                emitir('RET', 0 if i['origem'] is None else 1)
            else:
                raise ValueError(f'instrucao intermediaria desconhecida: {op}')
        emitir('END')
    return linhas
