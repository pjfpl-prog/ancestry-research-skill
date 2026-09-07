# examples/

Demonstrações de uso da skill com **placeholders** ou registos públicos neutros.

Esta pasta existe e é copiada junto com a skill (o `README.md` da raiz manda copiá-la).
Ela começa vazia de propósito: exemplo bom nasce do uso real, e exemplo de enchimento
só engorda o repositório.

## Regra inquebrável

**Nada aqui pode conter a genealogia de uma pessoa real.** Sem nomes de família
investigada, sem GUIDs ou `fileId` que apontem para documentos de um antepassado
concreto, sem ARKs reais, sem ficheiros `.ged`, sem imagens descarregadas de um arquivo.

Use sempre os placeholders da skill: `{GUID}`, `{fileId}`, `TERMO`, `<ARK>`,
`{PID_RAIZ}`, `Freguesia X`, `Concelho Y`.

## O que cabe aqui

- Transcrição de uma fórmula de assento, com os nomes substituídos por `TERMO`.
- Sessão de exemplo mostrando a sequência `search` -> `details` -> `images` -> `download`
  com identificadores fictícios.
- Recorte de imagem de um documento **de domínio público e sem ligação a família alguma**,
  usado só para demonstrar `enhance`/`crop`.

## Atenção ao `.gitignore`

A raiz ignora `*.jpg`, `*.png`, `*.pdf` e `*.ged` para impedir que dados de pesquisa
entrem por acidente. Essa regra vale aqui dentro também, de propósito. Se um exemplo
precisar mesmo de uma imagem, acrescente uma excepção explícita para aquele ficheiro,
depois de confirmar que ele não tem ligação a ninguém.
