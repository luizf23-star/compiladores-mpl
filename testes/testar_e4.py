"""Casos extras de integracao: compilacao real e execucao pelo lancador."""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[1]


class IntegracaoE4(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.pasta = Path(self.temporario.name)
        self.contador = 0

    def rodar(self, comando, arquivo):
        return subprocess.run([str(RAIZ / comando), str(arquivo)], cwd=RAIZ,
                              capture_output=True, text=True,
                              encoding='utf-8', timeout=15)

    def compilar(self, fonte):
        self.contador += 1
        caminho = self.pasta / f'programa{self.contador}.mpl'
        caminho.write_text(fonte, encoding='utf-8')
        r = self.rodar('compilar', caminho)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((r.stdout, r.stderr), ('', ''))
        bytecode = caminho.with_suffix('.mplb')
        self.assertTrue(bytecode.is_file())
        self.assertTrue(bytecode.read_text(encoding='utf-8').startswith('MPLB 1\n'))
        return caminho, bytecode

    def conferir(self, fonte, esperado):
        _, bytecode = self.compilar(fonte)
        r = self.rodar('executar', bytecode)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, '')
        self.assertEqual(r.stdout, esperado)

    def erro_execucao(self, fonte, linha):
        _, bytecode = self.compilar(fonte)
        r = self.rodar('executar', bytecode)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertRegex(r.stderr, rf'^erro execucao: linha {linha}, coluna \d+:')
        self.assertNotIn('Traceback', r.stderr)

    def test_divisao_e_resto_com_todos_os_sinais(self):
        self.conferir('''funcao vazio principal() {
  escreva(7 / 3); escreva(-7 / 3);
  escreva(7 / -3); escreva(-7 / -3);
  escreva(7 % 3); escreva(-7 % 3);
  escreva(7 % -3); escreva(-7 % -3);
}''', '2\n-2\n-2\n2\n1\n-1\n1\n-1\n')

    def test_inteiro_grande_nao_passa_por_float(self):
        self.conferir('''funcao vazio principal() {
  escreva(9007199254740993 / 1);
  escreva(-9007199254740993 / 2);
  escreva(-9007199254740993 % 2);
}''', '9007199254740993\n-4503599627370496\n-1\n')

    def test_conversoes_atribuicao_argumento_retorno(self):
        self.conferir('''funcao real recebe(real x) { retorne x / 2; }
funcao real devolve() { retorne 7 / 2; }
funcao vazio principal() {
  real x = 7 / 2; escreva(x);
  x = 9 / 2; escreva(x);
  escreva(recebe(7 / 2)); escreva(devolve());
  escreva(1 + 0.5); escreva(2 == 2.0);
}''', '3.000000\n4.000000\n1.500000\n3.000000\n1.500000\nverdadeiro\n')

    def test_valores_padrao_e_sombreamento(self):
        self.conferir('''funcao vazio principal() {
  inteiro x; real r; logico l; texto t;
  escreva(x); escreva(r); escreva(l); escreva(t);
  x = 8;
  { inteiro x = 2; escreva(x); }
  escreva(x);
}''', '0\n0.000000\nfalso\n\n2\n8\n')

    def test_declaracao_dentro_do_laco_reinicializa(self):
        self.conferir('''funcao vazio principal() {
  inteiro i = 0;
  enquanto (i < 3) {
    inteiro n; n = n + 1; escreva(n);
    i = i + 1;
  }
}''', '1\n1\n1\n')

    def test_quadros_isolados_e_recursao_profunda(self):
        self.conferir('''funcao inteiro conta(inteiro n) {
  inteiro salvo = n;
  se (n == 0) { retorne 0; }
  inteiro menor = conta(n - 1);
  se (salvo != n) { retorne -9999; }
  retorne menor + 1;
}
funcao vazio principal() { escreva(conta(900)); }''', '900\n')

    def test_recursao_mutua_e_chamadas_adiantadas(self):
        self.conferir('''funcao logico par(inteiro n) {
  se (n == 0) { retorne verdadeiro; }
  retorne impar(n - 1);
}
funcao logico impar(inteiro n) {
  se (n == 0) { retorne falso; }
  retorne par(n - 1);
}
funcao vazio principal() { escreva(par(20)); escreva(impar(19)); }''',
                      'verdadeiro\nverdadeiro\n')

    def test_e_ou_avaliam_os_dois_lados_em_ordem(self):
        self.conferir('''funcao logico marca(inteiro n, logico valor) {
  escreva(n); retorne valor;
}
funcao vazio principal() {
  escreva(marca(1, falso) e marca(2, verdadeiro));
  escreva(marca(3, verdadeiro) ou marca(4, falso));
}''', '1\n2\nfalso\n3\n4\nverdadeiro\n')

    def test_parametros_por_valor_e_retorno_vazio(self):
        self.conferir('''funcao vazio muda(inteiro x) { x = 99; escreva(x); }
funcao vazio mensagem(inteiro n) {
  se (n == 0) { retorne; }
  escreva(n);
}
funcao vazio principal() {
  inteiro x = 5; muda(x); escreva(x);
  mensagem(0); mensagem(2);
}''', '99\n5\n2\n')

    def test_resultado_descartado_nao_suja_pilha(self):
        self.conferir('''funcao inteiro dobro(inteiro x) { retorne x * 2; }
funcao vazio principal() {
  inteiro i = 0;
  enquanto (i < 4) { dobro(i); i = i + 1; }
  escreva(dobro(dobro(3)));
}''', '12\n')

    def test_argumentos_avaliados_em_ordem(self):
        self.conferir('''funcao inteiro marca(inteiro n) { escreva(n); retorne n; }
funcao inteiro soma(inteiro a, inteiro b) { retorne a + b; }
funcao vazio principal() { escreva(soma(marca(10), marca(20))); }''',
                      '10\n20\n30\n')

    def test_texto_unicode_escapes_e_concatenacao(self):
        self.conferir(r'''funcao vazio principal() {
  texto t = "ação\n"; escreva(t + "fim");
  escreva("aspas: \"ok\"\t\\");
  escreva("a" == "a"); escreva("a" != "b");
}''', 'ação\nfim\naspas: "ok"\t\\\nverdadeiro\nverdadeiro\n')

    def test_nomes_nao_colidem_com_temporarios(self):
        self.conferir('''funcao vazio principal() {
  inteiro t0 = 1; inteiro v0_t0 = 2; inteiro L0 = 3;
  escreva(t0 + v0_t0 + L0);
  se (falso) { escreva(99); } senao { escreva(7); }
}''', '6\n7\n')

    def test_multiplos_lacos_e_desvios(self):
        self.conferir('''funcao vazio principal() {
  inteiro i = 0; inteiro soma = 0;
  enquanto (i < 3) {
    inteiro j = 0;
    enquanto (j < 2) {
      se ((i + j) % 2 == 0) { soma = soma + 1; }
      senao { soma = soma + 10; }
      j = j + 1;
    }
    i = i + 1;
  }
  escreva(soma);
}''', '33\n')

    def test_divisao_zero_aponta_comando_multilinha(self):
        self.erro_execucao('''funcao vazio principal() {
  real x =
    1.0 /
    0;
}''', 2)

    def test_resto_zero(self):
        self.erro_execucao('''funcao vazio principal() {
  escreva(3 % 0);
}''', 2)

    def test_estouro_pilha_aponta_chamada_recursiva(self):
        self.erro_execucao('''funcao inteiro sempre(inteiro n) {
  retorne sempre(n + 1);
}
funcao vazio principal() { escreva(sempre(0)); }''', 2)

    def test_ir_expoe_funcoes_e_rotulos_sem_gravar_bytecode(self):
        fonte = self.pasta / 'ir.mpl'
        fonte.write_text('''funcao inteiro f(inteiro n) {
  se (n > 0) { retorne n * (n + 1); }
  retorne 0;
}
funcao vazio principal() { escreva(f(2)); }''', encoding='utf-8')
        r = subprocess.run([str(RAIZ / 'compilar'), '--ir', str(fonte)],
                           cwd=RAIZ, capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('funcao f inteiro', r.stdout)
        self.assertIn('funcao principal vazio', r.stdout)
        destinos = set(re.findall(r'\bdesvie (L\d+)', r.stdout))
        rotulos = set(re.findall(r'^(L\d+):$', r.stdout, re.MULTILINE))
        self.assertTrue(destinos)
        self.assertLessEqual(destinos, rotulos)
        self.assertFalse(fonte.with_suffix('.mplb').exists())

    def test_bytecode_independe_do_arquivo_fonte(self):
        fonte, bytecode = self.compilar(
            'funcao vazio principal() { escreva(6 * 7); }')
        fonte.unlink()
        r = self.rodar('executar', bytecode)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, '42\n')

    def test_bytecode_invalido_tem_diagnostico(self):
        bytecode = self.pasta / 'invalido.mplb'
        bytecode.write_text('nao e um executavel MPLB\n', encoding='utf-8')
        r = self.rodar('executar', bytecode)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertTrue(r.stderr.startswith('erro execucao: linha 1, coluna 1:'))
        self.assertNotIn('Traceback', r.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
