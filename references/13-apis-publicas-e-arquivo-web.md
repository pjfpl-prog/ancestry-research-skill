# APIs públicas complementares e páginas arquivadas

Esta referência cobre fontes de **metadados públicos** e recuperação de páginas antigas.
Ela não substitui o arquivo detentor do assento e não transforma catálogo em prova de
filiação. Os exemplos usam apenas placeholders e URLs institucionais.

## 1. Escolher pela cobertura, não pela disponibilidade

Defina primeiro o documento ou a descrição procurada. Consulte a documentação oficial e
teste uma amostra limitada. HTTP 200, uma página carregada ou uma lista de conjuntos não
demonstram cobertura genealógica.

Quando o escopo impedir transmitir dados familiares, consulte apenas URLs públicos sem
autenticação e correlacione os metadados localmente. Nunca envie nomes, identificadores,
documentos ou imagens privados para uma API apenas porque ela é pública.

## 2. Recuperar URLs com Arquivo.pt

Para um URL conhecido, use `https://arquivo.pt/textsearch` com `versionHistory` contendo
o URL percent-encoded e `maxItems` pequeno. Reserve `q` para termos, não URLs.

```text
https://arquivo.pt/textsearch?versionHistory=<URL_ENCODED>&maxItems=10
```

Guarde os parâmetros usados, `estimated_nr_results` e os itens efetivamente recebidos.
Uma estimativa do serviço não é uma contagem de documentos genealógicos.

### 2.1 Domínio e protocolo fazem diferença

Se a busca usar `siteSearch`, confira o host de `originalURL` numa captura e teste a forma
observada, inclusive `www`. Não suponha que `example.org`, `www.example.org`, HTTP e HTTPS
sejam equivalentes no índice.

```text
# Teste separadamente as formas observadas; não infira equivalência.
siteSearch=www.example.org
siteSearch=example.org
```

Uma busca sem resultado continua limitada ao endpoint, domínio, protocolo e parâmetros
consultados. Não é uma negativa arquivística.

### 2.2 CDX para um URL exato

Como verificação adicional, teste o CDX do Arquivo.pt quando a documentação atual o
oferecer:

```text
https://arquivo.pt/wayback/cdx?url=<URL_ENCODED>&output=json&limit=100
```

Leia a resposta conforme o formato anunciado. Resposta vazia significa zero capturas
naquele recorte; não significa que o documento nunca existiu.

### 2.3 Validar a captura antes de arquivar

Escolha uma captura com status HTTP 200 e tipo compatível. Baixe pelo `linkToOriginalFile`
retornado, quando existir, e confirme:

- bytes e tipo real do arquivo;
- conteúdo esperado, não apenas uma página de erro ou redirecionamento;
- URL original, URL arquivada e timestamp da captura;
- tamanho e SHA-256 local.

Resolva links relativos contra `originalURL` e consulte o histórico de cada recurso
importante. Não presuma que um PDF, imagem ou página vinculada também foi arquivado.
Preserve o original recebido e extraia texto como derivado separado.

O `tstamp` é data da captura web, não data de publicação nem data do evento genealógico.
Uma página arquivada preserva evidência histórica da página; não é confirmação independente
do ato descrito nela.

## 3. Avaliar catálogos OAI-PMH

Consulte `Identify`, `ListSets` e `ListMetadataFormats` no endpoint oficial. Use exatamente
o `setSpec` e o `metadataPrefix` anunciados; não adivinhe conjuntos ou formatos.

Exemplos públicos:

- PAPIR: `https://papir.cehr.ft.ucp.pt/index.php/;oai`
- RUBI: `https://rubi.casaruibarbosa.gov.br/oai/request`

Fluxo:

1. `ListIdentifiers` com conjunto e formato confirmados.
2. Leia poucos registros com `GetRecord`.
3. Inspecione erros XML mesmo quando o HTTP for 200.
4. Confira cota, nível descritivo, instituição, datas, assunto, conteúdo e links digitais.
5. Registre `resumptionToken`; token não vazio significa que a listagem é parcial.

Não deduza pertinência do nome amplo de um conjunto. Um conjunto religioso, literário ou
pessoal pode reunir itens sem relação com genealogia. OAI-PMH fornece descrições; não
concede automaticamente imagens, acesso restrito ou prova de filiação.

As datas de atualização dos metadados e as datas dos documentos são distintas. Uma
descrição pode apontar para um acervo útil sem conter o registro individual procurado.

## 4. Incorporar resultados

Arquive respostas brutas e uma avaliação de cobertura no acervo privado. Classifique cada
resultado separadamente como:

- recuperação técnica de uma página/URL;
- orientação sobre uma instituição ou coleção;
- descrição de catálogo;
- documento histórico novo;
- prova genealógica efetiva.

Não altere parentescos por metadados de catálogo. Se uma amostra não servir à pergunta,
registre a razão e retome o detentor do registro.

Documentação consultada:

- `https://github.com/arquivo/pwa-technologies/wiki/Arquivo.pt-API`
- `https://github.com/arquivo/pwa-technologies/wiki/URL-search:-CDX-server-API`
- `https://www.openarchives.org/OAI/openarchivesprotocol.html`
