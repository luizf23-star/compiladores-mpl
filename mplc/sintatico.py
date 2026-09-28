"""
Entrega 2 — analise sintatica.

Transformar a lista de tokens numa arvore.

Sugestao forte: descida recursiva, uma funcao por nivel de precedencia, na
ordem da secao 3.3 da especificacao. E como voces vao enxergar a precedencia
virar formato de arvore.

Gerador de parser (ANTLR, PLY, yacc) esta proibido nesta entrega e na
anterior — o objetivo e entender, e o gerador esconde exatamente a parte
que esta sendo ensinada.

Leiam antes: LINGUAGEM.md secoes 3 a 5, e CONTRATOS.md secao 3.
"""
from mplc.erros import ErroMPL


class No:
    """Um no da arvore. O rotulo e o que sai no --ast."""

    def __init__(self, rotulo, filhos=None, linha=0, coluna=0, **extra):
        self.rotulo = rotulo      # 'binario +', 'literal inteiro 1', 'bloco', ...
        self.filhos = filhos or []
        self.linha = linha
        self.coluna = coluna
        self.extra = extra        # o que a semantica quiser pendurar depois


def analisar(tokens):
    """Recebe a lista de Token. Devolve a raiz da arvore (um No 'programa')."""
    return Analisador(tokens).programa()


class Analisador:
    """Descida recursiva: cada metodo de expressao corresponde a uma precedencia."""

    TIPOS = {'TIPO_INTEIRO', 'TIPO_REAL', 'TIPO_LOGICO', 'TIPO_TEXTO'}

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def atual(self):
        return self.tokens[self.pos]

    def aceitar(self, *tipos):
        if self.atual().tipo in tipos:
            token = self.atual()
            self.pos += 1
            return token
        return None

    def exigir(self, tipo):
        token = self.aceitar(tipo)
        if token is None:
            self.erro(f'esperado {tipo}')
        return token

    def erro(self, mensagem):
        token = self.atual()
        raise ErroMPL('sintatico', token.linha, token.coluna, mensagem)

    @staticmethod
    def no(rotulo, token, filhos=None):
        return No(rotulo, filhos, token.linha, token.coluna)

    def programa(self):
        primeiro = self.atual()
        funcoes = []
        while self.atual().tipo != 'FIM_ARQUIVO':
            funcoes.append(self.funcao())
        self.exigir('FIM_ARQUIVO')
        return self.no('programa', primeiro, funcoes)

    def tipo(self, permite_vazio=False):
        tipos = self.TIPOS | ({'TIPO_VAZIO'} if permite_vazio else set())
        if self.atual().tipo not in tipos:
            self.erro('esperado tipo')
        return self.aceitar(self.atual().tipo)

    def funcao(self):
        inicio = self.exigir('FUNCAO')
        tipo = self.tipo(permite_vazio=True)
        nome = self.exigir('ID')
        self.exigir('ABRE_PAR')
        parametros = []
        if self.atual().tipo != 'FECHA_PAR':
            while True:
                tipo_param = self.tipo()
                nome_param = self.exigir('ID')
                parametros.append(self.no(
                    f'parametro {nome_param.lexema} {tipo_param.lexema}', tipo_param))
                if not self.aceitar('VIRGULA'):
                    break
        self.exigir('FECHA_PAR')
        return self.no(f'funcao {nome.lexema} {tipo.lexema}', inicio,
                       [self.no('parametros', nome, parametros), self.bloco()])

    def bloco(self):
        inicio = self.exigir('ABRE_CHAVE')
        comandos = []
        while self.atual().tipo not in ('FECHA_CHAVE', 'FIM_ARQUIVO'):
            comandos.append(self.comando())
        self.exigir('FECHA_CHAVE')
        return self.no('bloco', inicio, comandos)

    def comando(self):
        token = self.atual()
        if token.tipo in self.TIPOS:
            tipo = self.tipo()
            nome = self.exigir('ID')
            valor = [self.expressao()] if self.aceitar('ATRIBUI') else []
            self.exigir('PONTO_VIRGULA')
            return self.no(f'declaracao {nome.lexema} {tipo.lexema}', tipo, valor)

        if self.aceitar('SE'):
            self.exigir('ABRE_PAR')
            condicao = self.expressao()
            self.exigir('FECHA_PAR')
            filhos = [condicao, self.bloco()]
            if self.aceitar('SENAO'):
                filhos.append(self.bloco())
            return self.no('se', token, filhos)

        if self.aceitar('ENQUANTO'):
            self.exigir('ABRE_PAR')
            condicao = self.expressao()
            self.exigir('FECHA_PAR')
            return self.no('enquanto', token, [condicao, self.bloco()])

        if self.aceitar('ESCREVA'):
            self.exigir('ABRE_PAR')
            valor = self.expressao()
            self.exigir('FECHA_PAR')
            self.exigir('PONTO_VIRGULA')
            return self.no('escreva', token, [valor])

        if self.aceitar('RETORNE'):
            valor = [] if self.atual().tipo == 'PONTO_VIRGULA' else [self.expressao()]
            self.exigir('PONTO_VIRGULA')
            return self.no('retorne', token, valor)

        if token.tipo == 'ABRE_CHAVE':
            return self.bloco()

        if self.aceitar('ID'):
            if self.aceitar('ATRIBUI'):
                valor = self.expressao()
                self.exigir('PONTO_VIRGULA')
                return self.no(f'atribuicao {token.lexema}', token, [valor])
            if self.atual().tipo == 'ABRE_PAR':
                chamada = self.chamada(token)
                self.exigir('PONTO_VIRGULA')
                return chamada
            self.erro('esperada atribuicao ou chamada')

        self.erro('esperado comando')

    def expressao(self):
        return self.ou()

    def binarios(self, proximo, operadores):
        esquerdo = proximo()
        while self.atual().tipo in operadores:
            operador = self.aceitar(self.atual().tipo)
            direito = proximo()
            esquerdo = self.no(f'binario {operador.lexema}', operador,
                               [esquerdo, direito])
        return esquerdo

    def ou(self):
        return self.binarios(self.e, {'OU'})

    def e(self):
        return self.binarios(self.igualdade, {'E'})

    def igualdade(self):
        return self.binarios(self.relacional, {'IGUAL', 'DIFERENTE'})

    def relacional(self):
        return self.binarios(self.aditivo,
                             {'MENOR', 'MENOR_IGUAL', 'MAIOR', 'MAIOR_IGUAL'})

    def aditivo(self):
        return self.binarios(self.multiplicativo, {'MAIS', 'MENOS'})

    def multiplicativo(self):
        return self.binarios(self.unario, {'VEZES', 'DIVIDE', 'RESTO'})

    def unario(self):
        operador = self.aceitar('NAO', 'MENOS')
        if operador:
            return self.no(f'unario {operador.lexema}', operador, [self.unario()])
        return self.primario()

    def chamada(self, nome):
        self.exigir('ABRE_PAR')
        argumentos = []
        if self.atual().tipo != 'FECHA_PAR':
            while True:
                argumentos.append(self.expressao())
                if not self.aceitar('VIRGULA'):
                    break
        self.exigir('FECHA_PAR')
        return self.no(f'chamada {nome.lexema}', nome, argumentos)

    def primario(self):
        token = self.atual()
        if self.aceitar('ABRE_PAR'):
            valor = self.expressao()
            self.exigir('FECHA_PAR')
            return valor
        if self.aceitar('ID'):
            if self.atual().tipo == 'ABRE_PAR':
                return self.chamada(token)
            return self.no(f'variavel {token.lexema}', token)
        if self.aceitar('INTEIRO', 'REAL', 'LOGICO', 'TEXTO'):
            tipo = token.tipo.lower()
            valor = f'{float(token.lexema):.6f}' if tipo == 'real' else token.lexema
            return self.no(f'literal {tipo} {valor}', token)
        self.erro('esperada expressao')


def despejar(no, nivel=0, saida=None):
    """Imprime a arvore no formato do --ast. Ja esta pronto: dois espacos por nivel."""
    saida = saida if saida is not None else []
    saida.append('  ' * nivel + no.rotulo)
    for f in no.filhos:
        despejar(f, nivel + 1, saida)
    return saida
