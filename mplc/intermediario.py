"""Entrega 4: AST tipada para codigo de tres enderecos.

Cada expressao produz um temporario. Variaveis de blocos diferentes recebem
locais diferentes, inclusive quando possuem o mesmo nome no fonte.
"""
import json


PADROES = {'inteiro': 0, 'real': 0.0, 'logico': False, 'texto': ''}


class Tradutor:
    def __init__(self, tabela):
        self.funcoes = tabela.global_.simbolos

    def emitir(self, op, no, **campos):
        self.instrucoes.append(dict(op=op, linha=no.linha,
                                    coluna=no.coluna, **campos))

    def temporario(self):
        nome = f't{self.ntemp}'
        self.ntemp += 1
        return nome

    def rotulo(self):
        nome = f'L{self.nrotulo}'
        self.nrotulo += 1
        return nome

    def declarar(self, nome, tipo):
        local = f'v{self.nlocal}_{nome}'
        self.nlocal += 1
        self.escopos[-1][nome] = (local, tipo)
        return local

    def buscar(self, nome):
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        raise ValueError(f'variavel sem vinculo semantico: {nome}')

    def converter(self, valor, origem, destino, comando):
        # A conversao ocorre depois da expressao: real x = 7 / 2 vale 3.0.
        if origem == 'inteiro' and destino == 'real':
            convertido = self.temporario()
            self.emitir('real', comando, destino=convertido, origem=valor)
            return convertido
        return valor

    def funcao(self, no):
        _, nome, retorno = no.rotulo.split()
        self.instrucoes = []
        self.escopos = [{}]
        self.ntemp = self.nrotulo = self.nlocal = 0
        self.retorno = retorno
        parametros = []
        for parametro in no.filhos[0].filhos:
            _, nome_param, tipo = parametro.rotulo.split()
            local = self.declarar(nome_param, tipo)
            parametros.append({'nome': nome_param, 'local': local, 'tipo': tipo})
        self.bloco(no.filhos[1])
        if retorno == 'vazio':
            self.emitir('retorne', no, origem=None)
        return {'nome': nome, 'retorno': retorno, 'parametros': parametros,
                'instrucoes': self.instrucoes}

    def bloco(self, no):
        self.escopos.append({})
        for comando in no.filhos:
            self.comando(comando)
        self.escopos.pop()

    def comando(self, no):
        partes = no.rotulo.split()
        classe = partes[0]
        if classe == 'bloco':
            self.bloco(no)
        elif classe == 'declaracao':
            nome, tipo = partes[1:]
            local = self.declarar(nome, tipo)
            self.emitir('constante', no, destino=local, tipo=tipo,
                        valor=PADROES[tipo])
            if no.filhos:
                expr = no.filhos[0]
                valor = self.expressao(expr, no)
                valor = self.converter(valor, expr.extra['tipo'], tipo, no)
                self.emitir('copia', no, destino=local, origem=valor)
        elif classe == 'atribuicao':
            local, tipo = self.buscar(partes[1])
            expr = no.filhos[0]
            valor = self.expressao(expr, no)
            valor = self.converter(valor, expr.extra['tipo'], tipo, no)
            self.emitir('copia', no, destino=local, origem=valor)
        elif classe == 'escreva':
            valor = self.expressao(no.filhos[0], no)
            self.emitir('escreva', no, origem=valor)
        elif classe == 'retorne':
            valor = None
            if no.filhos:
                expr = no.filhos[0]
                valor = self.expressao(expr, no)
                valor = self.converter(valor, expr.extra['tipo'], self.retorno, no)
            self.emitir('retorne', no, origem=valor)
        elif classe == 'chamada':
            self.expressao(no, no)
        elif classe == 'se':
            alternativo = self.rotulo()
            fim = self.rotulo() if len(no.filhos) == 3 else alternativo
            condicao = self.expressao(no.filhos[0], no)
            self.emitir('se_falso', no, origem=condicao, rotulo=alternativo)
            self.bloco(no.filhos[1])
            if len(no.filhos) == 3:
                self.emitir('desvie', no, rotulo=fim)
            self.emitir('rotulo', no, nome=alternativo)
            if len(no.filhos) == 3:
                self.bloco(no.filhos[2])
                self.emitir('rotulo', no, nome=fim)
        elif classe == 'enquanto':
            inicio, fim = self.rotulo(), self.rotulo()
            self.emitir('rotulo', no, nome=inicio)
            condicao = self.expressao(no.filhos[0], no)
            self.emitir('se_falso', no, origem=condicao, rotulo=fim)
            self.bloco(no.filhos[1])
            self.emitir('desvie', no, rotulo=inicio)
            self.emitir('rotulo', no, nome=fim)
        else:
            raise ValueError(f'comando sem traducao: {classe}')

    def expressao(self, no, comando):
        partes = no.rotulo.split(' ', 2)
        classe = partes[0]
        if classe == 'literal':
            tipo, texto = partes[1:]
            if tipo == 'inteiro':
                valor = int(texto)
            elif tipo == 'real':
                valor = float(texto)
            elif tipo == 'logico':
                valor = texto == 'verdadeiro'
            else:
                valor = json.loads(texto)
            destino = self.temporario()
            self.emitir('constante', comando, destino=destino,
                        tipo=tipo, valor=valor)
            return destino
        if classe == 'variavel':
            # Captura o valor agora; expressoes e argumentos seguem a ordem
            # da esquerda para a direita, mesmo quando ha chamadas no meio.
            destino = self.temporario()
            self.emitir('copia', comando, destino=destino,
                        origem=self.buscar(partes[1])[0])
            return destino
        if classe == 'chamada':
            nome = partes[1]
            assinatura = self.funcoes[nome]
            argumentos = []
            for expr, tipo in zip(no.filhos, assinatura.parametros):
                valor = self.expressao(expr, comando)
                argumentos.append(self.converter(
                    valor, expr.extra['tipo'], tipo, comando))
            destino = None if assinatura.tipo == 'vazio' else self.temporario()
            self.emitir('chame', comando, destino=destino,
                        nome=nome, argumentos=argumentos)
            return destino
        if classe == 'unario':
            origem = self.expressao(no.filhos[0], comando)
            destino = self.temporario()
            self.emitir('unario', comando, destino=destino,
                        operador=partes[1], origem=origem)
            return destino
        if classe == 'binario':
            esquerdo, direito = no.filhos
            a = self.expressao(esquerdo, comando)
            b = self.expressao(direito, comando)
            ta, tb = esquerdo.extra['tipo'], direito.extra['tipo']
            if {ta, tb} == {'inteiro', 'real'}:
                a = self.converter(a, ta, 'real', comando)
                b = self.converter(b, tb, 'real', comando)
            destino = self.temporario()
            self.emitir('binario', comando, destino=destino, operador=partes[1],
                        esquerdo=a, direito=b)
            return destino
        raise ValueError(f'expressao sem traducao: {classe}')


def gerar(arvore, tabela):
    tradutor = Tradutor(tabela)
    return [tradutor.funcao(funcao) for funcao in arvore.filhos]


def despejar(codigo):
    """Uma unica operacao por linha; rótulos e funções ficam explicitos."""
    linhas = []
    for funcao in codigo:
        parametros = ', '.join(f"{p['local']} {p['tipo']}"
                               for p in funcao['parametros'])
        linhas.append(f"funcao {funcao['nome']} {funcao['retorno']} ({parametros})")
        for instrucao in funcao['instrucoes']:
            i = instrucao
            op = i['op']
            if op == 'constante':
                if i['tipo'] == 'logico':
                    valor = 'verdadeiro' if i['valor'] else 'falso'
                else:
                    valor = json.dumps(i['valor'], ensure_ascii=False)
                linha = f"{i['destino']} = {valor}"
            elif op == 'copia':
                linha = f"{i['destino']} = {i['origem']}"
            elif op == 'real':
                linha = f"{i['destino']} = converte_real {i['origem']}"
            elif op == 'binario':
                linha = (f"{i['destino']} = {i['esquerdo']} "
                         f"{i['operador']} {i['direito']}")
            elif op == 'unario':
                linha = f"{i['destino']} = {i['operador']} {i['origem']}"
            elif op == 'chame':
                chamada = f"chama {i['nome']} " + ', '.join(i['argumentos'])
                linha = f"{i['destino']} = {chamada}" if i['destino'] else chamada
            elif op == 'rotulo':
                linhas.append(f"{i['nome']}:")
                continue
            elif op == 'desvie':
                linha = f"desvie {i['rotulo']}"
            elif op == 'se_falso':
                linha = f"seFalso {i['origem']} desvie {i['rotulo']}"
            elif op == 'escreva':
                linha = f"escreva {i['origem']}"
            elif op == 'retorne':
                linha = 'retorne' if i['origem'] is None else f"retorne {i['origem']}"
            else:
                raise ValueError(f'instrucao intermediaria desconhecida: {op}')
            linhas.append('  ' + linha.rstrip())
        linhas.append('fim')
    return linhas
