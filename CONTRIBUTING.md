# Contribuir

Contribuições são bem-vindas: novas fontes e arquivos, melhorias de paleografia, scripts
mais robustos, correções nas referências.

## A regra inquebrável

**Nenhuma contribuição pode incluir dados pessoais reais, genealogia de família concreta,
credenciais, ou imagens descarregadas de um arquivo.**

Isto vale para o código, para a documentação, para os exemplos e para os testes. Use sempre
placeholders: `{GUID}`, `{fileId}`, `TERMO`, `<ARK>`, `{PID_RAIZ}`, `Freguesia X`, `Concelho Y`.

Uma excepção estreita, sempre com o motivo escrito no teste: quando uma fixture tem de ser a
resposta **real** de um servidor (o que exige um termo que exista no acervo), o termo pode ser o
nome de uma **figura pública histórica**, morta há mais de um século, sem ligação a quem pesquisa.
Nunca um antepassado, nunca uma pessoa viva.

Ficheiros `.ged` e imagens **não entram no repositório**, nem como ficheiro de teste. Os testes
geram os seus próprios GEDCOM em tempo de execução, em `tmp_path`. É de propósito: um `.ged`
versionado é a árvore de alguém.

## O `.gitignore` é uma lista branca

Tudo é ignorado por omissão e só entra o que está explicitamente listado. Se acrescentar um
ficheiro novo e ele não aparecer no `git status`, é isso a acontecer, e não um erro: acrescente
a linha correspondente no `.gitignore`, depois de pensar no que há dentro do ficheiro.

Antes de cada commit:

```bash
git status --ignored --untracked-files=all
```

## Correr os testes

```bash
pip install -r scripts/requirements.txt -r scripts/requirements-dev.txt
ruff check scripts tests
pytest -q
```

Os testes não tocam na rede. Há um teste `live`, desligado por omissão, que confere o contrato
da API do DigitArq contra o servidor real; corra-o à mão antes de mexer no `digitarq.py`:

```bash
DIGITARQ_LIVE=1 pytest -q -m live
```

## Se um segredo escapar

Se cometer por engano um token, uma senha ou dados de família: **não conte com um commit de
remoção**, porque o histórico continua lá e pode já ter sido clonado. Revogue o segredo na
origem (gere um token novo no BotFather, mude a senha) e depois avise nos *issues* para que se
decida se vale reescrever o histórico.

## Estilo

- Código-fonte dos scripts em ASCII (sem acentos nos comentários); os dados tratados, não.
- Comentário explica **porquê**, não o que a linha já diz. Quando corrigir um defeito, diga na
  linha o que estava errado antes: é o que impede alguém de "simplificar" de volta.
- Documentação em português. Verifique na fonte antes de afirmar como uma API se comporta, e
  registe a data da verificação.
