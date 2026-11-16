// Programa proprio da Entrega 4: planejamento de uma fila de atividades.
// Demonstra recursao, conversao para real, escopos, repeticao e condicional.
funcao inteiro minutos(inteiro atividades) {
  se (atividades <= 0) {
    retorne 0;
  }
  retorne 30 + minutos(atividades - 1);
}

funcao real progresso(inteiro concluidas, inteiro total) {
  retorne concluidas * 100.0 / total;
}

funcao vazio principal() {
  inteiro total = 6;
  inteiro concluidas = 2;
  inteiro porSemana = 2;
  inteiro semana = 0;
  escreva("PLANEJADOR DE ESTUDOS");
  escreva("Atividades pendentes:");
  escreva(total - concluidas);
  escreva("Minutos previstos:");
  escreva(minutos(total - concluidas));
  enquanto (concluidas < total) {
    semana = semana + 1;
    concluidas = concluidas + porSemana;
    se (concluidas > total) {
      concluidas = total;
    }
    escreva("Semana:");
    escreva(semana);
    escreva("Progresso:");
    escreva(progresso(concluidas, total));
  }
  escreva("Tudo concluido:");
  escreva(concluidas == total);
}
