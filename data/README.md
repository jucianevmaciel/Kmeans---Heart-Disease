# Dados

    raw/heart.csv     base usada em todas as rodadas (Kaggle, fedesoriano; 918 pacientes)
    split/            divisões treino/teste do SVM-Infarto, guardadas só como referência
                      (o K-Means não usa divisão; ver a R8)

Cada paciente recebe um `id` = número da linha dele no `raw/heart.csv`
(começando em 0). É esse id que o cruzamento com os erros do SVM usa (R6).

O `HeartDisease` **não** entra no agrupamento; só é usado depois, para avaliar
os grupos e como critério de escolha nas rodadas (ARI).
