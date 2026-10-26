"""Entrega 3: tabela de simbolos, escopos e verificacao de tipos da MPL.

A primeira passada registra todas as assinaturas das funcoes. A segunda
percorre os corpos com escopos lexicos e confere expressoes e retornos.
"""
from mplc.erros import ErroMPL


NUMERICOS = {'inteiro', 'real'}


class Simbolo:
    def __init__(self, nome, categoria, tipo, linha, parametros=()):
        self.nome = nome
        self.categoria = categoria
        self.tipo = tipo
        self.linha = linha
        self.parametros = tuple(parametros)

    def tipo_exibido(self):
        if self.categoria == 'funcao':
            return f'{self.tipo}({",".join(self.parametros)})'
        return self.tipo


class Escopo:
    def __init__(self, numero, descricao, pai=None):
        self.numero = numero
        self.descricao = descricao
        self.pai = pai
        self.simbolos = {}

    def buscar(self, nome):
        escopo = self
        while escopo is not None:
            if nome in escopo.simbolos:
                return escopo.simbolos[nome]
            escopo = escopo.pai
        return None


class Tabela:
    def __init__(self):
        self.escopos = [Escopo(0, 'global')]

    @property
    def global_(self):
        return self.escopos[0]

    def abrir(self, descricao, pai):
        novo = Escopo(len(self.escopos), descricao, pai)
        self.escopos.append(novo)
        return novo


class Verificador:
    def __init__(self, arvore):
        self.arvore = arvore
        self.tabela = Tabela()
        self.atual = self.tabela.global_
        self.retorno_atual = None

    @staticmethod
    def erro(no, mensagem):
        raise ErroMPL('semantico', no.linha, no.coluna, mensagem)

    @staticmethod
    def partes(no):
        return no.rotulo.split(' ')

    def declarar(self, escopo, simbolo, no):
        if simbolo.nome in escopo.simbolos:
            self.erro(no, f'{simbolo.nome} ja foi declarado neste escopo')
        escopo.simbolos[simbolo.nome] = simbolo

    @staticmethod
    def compativel(destino, origem):
        return destino == origem or (destino == 'real' and origem == 'inteiro')

    def exigir_tipo(self, destino, origem, no):
        if not self.compativel(destino, origem):
            self.erro(no, f'nao e possivel usar {origem} onde se espera {destino}')

    def analisar(self):
        # Primeiro todas as assinaturas: chamadas adiantadas e recursao mutua.
        for funcao in self.arvore.filhos:
            _, nome, retorno = self.partes(funcao)
            parametros = [self.partes(p)[2] for p in funcao.filhos[0].filhos]
            self.declarar(self.tabela.global_, Simbolo(
                nome, 'funcao', retorno, funcao.linha, parametros), funcao)

        principal = self.tabela.global_.simbolos.get('principal')
        if principal is None:
            self.erro(self.arvore, 'falta a funcao principal')
        if principal.tipo != 'vazio' or principal.parametros:
            principal_no = next(f for f in self.arvore.filhos
                                if self.partes(f)[1] == 'principal')
            self.erro(principal_no, 'principal deve ser vazio e sem parametros')

        for funcao in self.arvore.filhos:
            _, nome, retorno = self.partes(funcao)
            self.retorno_atual = retorno
            anterior = self.atual
            self.atual = self.tabela.abrir(f'funcao {nome}', self.tabela.global_)
            for parametro in funcao.filhos[0].filhos:
                _, nome_param, tipo_param = self.partes(parametro)
                self.declarar(self.atual, Simbolo(
                    nome_param, 'parametro', tipo_param, parametro.linha), parametro)
            garante_retorno = self.bloco(funcao.filhos[1])
            if retorno != 'vazio' and not garante_retorno:
                self.erro(funcao, f'a funcao {nome} nao retorna em todos os caminhos')
            self.atual = anterior
        return self.tabela

    def bloco(self, no):
        pai = self.atual
        self.atual = self.tabela.abrir('bloco', pai)
        garante_retorno = False
        for comando in no.filhos:
            # Continua visitando mesmo depois de retorno, para validar o codigo.
            if self.comando(comando):
                garante_retorno = True
        self.atual = pai
        return garante_retorno

    def comando(self, no):
        partes = self.partes(no)
        classe = partes[0]

        if classe == 'declaracao':
            nome, tipo = partes[1], partes[2]
            self.declarar(self.atual, Simbolo(
                nome, 'variavel', tipo, no.linha), no)
            if no.filhos:
                self.exigir_tipo(tipo, self.expressao(no.filhos[0]), no)
            return False

        if classe == 'atribuicao':
            nome = partes[1]
            simbolo = self.atual.buscar(nome)
            if simbolo is None or simbolo.categoria not in ('variavel', 'parametro'):
                self.erro(no, f'variavel {nome} nao declarada')
            self.exigir_tipo(simbolo.tipo, self.expressao(no.filhos[0]), no)
            return False

        if classe == 'se':
            self.exigir_tipo('logico', self.expressao(no.filhos[0]), no)
            retorno_se = self.bloco(no.filhos[1])
            retorno_senao = self.bloco(no.filhos[2]) if len(no.filhos) == 3 else False
            return retorno_se and retorno_senao

        if classe == 'enquanto':
            self.exigir_tipo('logico', self.expressao(no.filhos[0]), no)
            self.bloco(no.filhos[1])
            return False  # O laco pode nem executar.

        if classe == 'escreva':
            if self.expressao(no.filhos[0]) == 'vazio':
                self.erro(no, 'nao e possivel escrever uma funcao vazio')
            return False

        if classe == 'retorne':
            if self.retorno_atual == 'vazio':
                if no.filhos:
                    self.erro(no, 'funcao vazio nao pode retornar valor')
            else:
                if not no.filhos:
                    self.erro(no, 'retorno exige um valor')
                self.exigir_tipo(self.retorno_atual, self.expressao(no.filhos[0]), no)
            return True

        if classe == 'bloco':
            return self.bloco(no)

        if classe == 'chamada':
            self.expressao(no)
            return False

        self.erro(no, f'comando desconhecido: {classe}')

    def expressao(self, no):
        partes = self.partes(no)
        classe = partes[0]

        if classe == 'literal':
            tipo = partes[1]
            no.extra['tipo'] = tipo
            return tipo

        if classe == 'variavel':
            nome = partes[1]
            simbolo = self.atual.buscar(nome)
            if simbolo is None or simbolo.categoria not in ('parametro', 'variavel'):
                self.erro(no, f'variavel {nome} nao declarada')
            no.extra['tipo'] = simbolo.tipo
            return simbolo.tipo

        if classe == 'chamada':
            nome = partes[1]
            funcao = self.tabela.global_.simbolos.get(nome)
            if funcao is None:
                self.erro(no, f'funcao {nome} nao declarada')
            if len(no.filhos) != len(funcao.parametros):
                self.erro(no, f'funcao {nome} espera {len(funcao.parametros)} argumentos')
            for argumento, tipo_param in zip(no.filhos, funcao.parametros):
                self.exigir_tipo(tipo_param, self.expressao(argumento), no)
            no.extra['tipo'] = funcao.tipo
            return funcao.tipo

        if classe == 'unario':
            operador = partes[1]
            tipo = self.expressao(no.filhos[0])
            if operador == 'nao' and tipo == 'logico':
                resultado = 'logico'
            elif operador == '-' and tipo in NUMERICOS:
                resultado = tipo
            else:
                self.erro(no, f'operador unario {operador} invalido para {tipo}')
            no.extra['tipo'] = resultado
            return resultado

        if classe == 'binario':
            operador = partes[1]
            esquerdo = self.expressao(no.filhos[0])
            direito = self.expressao(no.filhos[1])
            numericos = esquerdo in NUMERICOS and direito in NUMERICOS
            if operador in ('e', 'ou'):
                if esquerdo != 'logico' or direito != 'logico':
                    self.erro(no, f'{operador} exige operandos logicos')
                resultado = 'logico'
            elif operador in ('==', '!='):
                if not (numericos or (esquerdo == direito and esquerdo != 'vazio')):
                    self.erro(no, 'tipos incompativeis para comparacao')
                resultado = 'logico'
            elif operador in ('<', '<=', '>', '>='):
                if not numericos:
                    self.erro(no, 'comparacao relacional exige numeros')
                resultado = 'logico'
            elif operador == '+' and esquerdo == direito == 'texto':
                resultado = 'texto'
            elif operador in ('+', '-', '*', '/') and numericos:
                resultado = 'real' if 'real' in (esquerdo, direito) else 'inteiro'
            elif operador == '%' and esquerdo == direito == 'inteiro':
                resultado = 'inteiro'
            else:
                self.erro(no, f'tipos invalidos para operador {operador}')
            no.extra['tipo'] = resultado
            return resultado

        self.erro(no, f'expressao desconhecida: {classe}')


def analisar(arvore):
    """Percorre a AST e devolve os escopos, depois de conferir a semantica."""
    return Verificador(arvore).analisar()


def despejar(tabela):
    """Converte a tabela para o formato de CONTRATOS.md, secao 4."""
    linhas = []
    for escopo in tabela.escopos:
        if escopo.pai is None:
            linhas.append('escopo 0 global')
        else:
            linhas.append(f'escopo {escopo.numero} {escopo.descricao} pai {escopo.pai.numero}')
        for simbolo in escopo.simbolos.values():
            linhas.append(f'  {simbolo.nome}|{simbolo.categoria}|'
                          f'{simbolo.tipo_exibido()}|{simbolo.linha}')
    return linhas
