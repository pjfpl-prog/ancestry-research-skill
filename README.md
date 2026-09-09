# Ancestry Research Skill

Uma *skill* genérica e pública para pesquisa de **ancestralidade / genealogia** com a ajuda de
um agente de IA (Claude Code, Codex ou outro agente capaz de ler instruções e executar scripts).

Reúne **métodos, fontes e ferramentas reutilizáveis** para localizar, ler e cruzar registos
históricos (paroquiais, civis, notariais, inquisitoriais, coloniais) em arquivos públicos —
sobretudo de Portugal e do Brasil, mas com técnicas transponíveis a qualquer país.

> **Este repositório NÃO contém nenhuma genealogia pessoal — apenas métodos e ferramentas
> genéricas.** Não há aqui nenhuma árvore, nenhum nome de família investigada, nenhuma
> credencial. Você fornece os seus próprios dados e as suas próprias contas.

---

## O que é

Um conjunto de instruções (`SKILL.md`), documentos de referência, *scripts* utilitários e
*templates* que ensinam um agente de IA a conduzir uma investigação genealógica disciplinada:

- **Descobrir** registos em arquivos digitais (busca por nome, lugar, período, tipo de assento).
- **Baixar** imagens de documentos em alta resolução e prepará-las para leitura.
- **Ler** paleografia ibérica dos séculos XVI–XVIII (abreviaturas, fórmulas, filiação).
- **Cruzar** fontes para subir gerações e **quebrar muros** (pontos onde a linhagem se perde).
- **Distinguir** o que está **documentado** (com fonte e cota) do que é **tradição/lenda**.
- **Registar** achados com nível de confiança, marcando leituras incertas e homónimos.

Quando houver delegação permitida, divida livros pertinentes em lotes entre subagentes;
caso contrário, use o mesmo protocolo localmente. Conte a carga conjunta sobre o arquivo.

## Para quem

Para **qualquer pessoa** que esteja a pesquisar a própria ancestralidade com o apoio de um
agente de IA — desde curiosos a candidatos a cidadania por descendência, passando por
historiadores de família. Não é preciso ser programador: basta saber instalar a skill, fornecer
os seus dados de partida (nomes, datas, lugares conhecidos) e, quando necessário, autorizar o
agente a usar as suas próprias contas de arquivo.

## Fontes cobertas

- **DigitArq / Arquivo Nacional Torre do Tombo** (Portugal) — busca e detalhe via API pública,
  **sem login**; registos paroquiais, processos da Inquisição, notariais.
- **FamilySearch** — busca de texto completo (OCR/IA), registos indexados e catálogo
  (sessão autorizada, conforme a coleção); exportação GEDCOM é opcional e depende de
  ferramenta e autenticação compatíveis, não sendo requisito de pesquisa.
- **[CRAV](references/16-crav-pedidos-reproducao.md)** — balcão DGLAB para informação,
  pesquisa, reprodução e certidão; login, escopo da cópia e orçamento verificados antes do envio.
- **[CEPESE](references/17-cepese-emigracao.md)** — índices de emigração portuguesa e
  ponte para localizar processos de passaporte no arquivo detentor; resultado é pista,
  não certidão nem prova de embarque.
- **AHU (Arquivo Histórico Ultramarino) / Projeto Resgate** — Brasil colonial.
- **Arquivos Distritais** (AD…) e registo civil/paroquial brasileiro.
- **Hemerotecas digitais** — Biblioteca Nacional (Brasil) e Biblioteca Nacional de Portugal.
- **APIs públicas complementares** — Arquivo.pt para URLs arquivados e OAI-PMH para
  descrições de catálogos, sempre como fontes de orientação/recuperação delimitada.

Os detalhes de *endpoints*, códigos de referência de paróquias, tipos de assento, APIs
públicas complementares e lógica de quebra de muros estão em `references/`.

---

## Instalação

Requisitos prévios: **Git** e **Python 3** (3.9+ recomendado).

### 1. Clonar o repositório

```bash
git clone https://github.com/<owner>/ancestry-research-skill.git
cd ancestry-research-skill
```

### 2. Tornar a skill disponível ao agente

**Claude Code** — copie a pasta para o diretório de skills:

```bash
# skill por projeto
mkdir -p .claude/skills/ancestry-research
cp -r references scripts templates examples SKILL.md LICENSE .claude/skills/ancestry-research/

# OU skill global (todos os projetos)
mkdir -p ~/.claude/skills/ancestry-research
cp -r references scripts templates examples SKILL.md LICENSE ~/.claude/skills/ancestry-research/
```

No Windows (PowerShell), use `Copy-Item -Recurse` e o caminho equivalente do seu perfil.

**Codex ou outro agente** — não há diretório de skills padronizado; basta **apontar o agente
para o `SKILL.md`** na raiz do repositório (passe-o como contexto/instrução inicial). Todos os
caminhos de `references/`, `scripts/`, `templates/` e `examples/` são relativos à raiz.

### 3. Instalar as dependências Python

```bash
python -m venv .venv
# Linux/macOS:  source .venv/bin/activate
# Windows:      .venv\Scripts\activate
pip install -r scripts/requirements.txt
```

## Dependências

- **Python 3** (3.9+).
- Pacotes Python listados em [`scripts/requirements.txt`](scripts/requirements.txt) — tipicamente:
  - `requests` — chamadas às APIs dos arquivos.
  - `Pillow` (PIL) — recorte, ampliação, *autocontrast* e *threshold* das imagens para leitura.
  - `getmyancestors` — **opcional**, em `scripts/requirements-familysearch.txt`: extração de árvore
    do FamilySearch para GEDCOM (login do próprio utilizador).

Instale com `pip install -r scripts/requirements.txt`. As dependências têm **limites de versão**
(intervalos, não pinos exactos): a skill é copiada para ambientes alheios, e pino exacto gera
conflito com o que já lá está. `getmyancestors` fica em `scripts/requirements-familysearch.txt`,
à parte, porque só serve a quem usa o FamilySearch.

---

## Configuração (variáveis de ambiente)

**Nenhum segredo é guardado no repositório.** Toda a configuração sensível é lida de variáveis
de ambiente, definidas pelo próprio utilizador. Nada disto é obrigatório para começar (o DigitArq
funciona sem login); são opcionais conforme as fontes que quiser usar.

| Variável | Lida por | Para quê | Obrigatória? |
|---|---|---|---|
| `NOTIFY_TELEGRAM_TOKEN` | `scripts/notify.py` | Token de bot para receber notificações de progresso | Opcional |
| `NOTIFY_TELEGRAM_CHAT` | `scripts/notify.py` | ID de chat de destino das notificações | Opcional |

**Não há variável de ambiente para o FamilySearch.** Nenhum script deste repositório faz login
no FamilySearch: a extração da árvore é feita pela ferramenta externa `getmyancestors`, que pede
a senha interativamente. Não passe a senha em argumento de linha de comando (fica visível na
lista de processos da máquina). Ver `references/02-familysearch.md`.

Use a entrada mascarada/gestor protegido do ambiente para a configuração sensível;
não cole credenciais no chat, em comandos, URLs, argumentos ou logs. Não execute o
notificador se a integração não oferecer um fluxo seguro. Uma conta FamilySearch
autorizada não elimina as restrições de uma coleção nem concede acesso à API.
Veja [o guia de acesso e exportação](references/02-familysearch.md).


---

## Estrutura de pastas

```
ancestry-research-skill/
├── README.md            # este ficheiro
├── SKILL.md             # instruções principais para o agente (ponto de entrada)
├── LICENSE              # MIT
├── references/          # conhecimento de referência: endpoints, tipos de assento,
│                        #   paleografia, lógica de quebra de muros, fontes por país
├── scripts/             # utilitários Python (busca, download, preparação de imagem...)
│   └── requirements.txt #   dependências Python
├── templates/           # modelos de saída: ficha de achado, dossiê, registo de fontes
└── examples/            # exemplos com PLACEHOLDERS / registos públicos neutros
                         #   (nenhuma família real)
```

- **`references/`** — o "manual": como falar com cada arquivo, o que cada tipo de documento
  nomeia, e como ler escrita antiga. Consultável pelo agente a qualquer momento.
- **`scripts/`** — ferramentas concretas que o agente executa (com placeholders `{GUID}`,
  `{fileId}`, `TERMO`, `<ARK>`).
- **`templates/`** — formatos de registo dos resultados, já com a disciplina de qualidade
  (DOCUMENTADO vs. TRADIÇÃO, marca `[?]` para incerteza, sinalização de homónimos).
- **`examples/`** — demonstrações de uso usando apenas **placeholders** ou registos públicos
  bem conhecidos; **nunca** a genealogia de um utilizador.

---

## Aviso legal e ético

- **Respeite os termos de uso** de cada arquivo e biblioteca. APIs públicas como a do DigitArq
  são para consulta; não as sobrecarregue. Os scripts deste repositório pausam entre pedidos e
  têm teto de resultados por execução, mas o teto é por processo: **vários agentes em paralelo
  multiplicam a carga** sobre o mesmo servidor. Conte os pedidos do conjunto, não de cada um.
- **FamilySearch: os termos restringem recolha automatizada e descarregamento em massa.** Usar a
  sua própria conta **não** é autorização para varrer o acervo. Exporte a **sua** árvore, em
  volume razoável. Se quiser ir além disso, leia os termos e, se for o caso, peça autorização.
- **Use apenas as suas próprias contas**, com as suas credenciais, nunca as de terceiros.
- **Licença das imagens não é a licença deste repositório.** Os conteúdos da rede de arquivos
  portuguesa são disponibilizados sob licença própria (a DGLAB indica CC BY-SA 4.0, e o DigitArq
  apresenta a licença aplicável no visualizador). O download direto pelo endpoint **não** traz
  essa informação junto. Registe a licença ao lado da proveniência no diário de pesquisa,
  sobretudo antes de redistribuir um recorte, publicar num sítio ou juntar a um processo.
- **Não publique dados de pessoas vivas.** Genealogia toca em dados pessoais. Mantenha privados
  os dados de familiares vivos e de terceiros; partilhe apenas o que for histórico e público,
  e mesmo assim com bom senso.
- **Cuidado redobrado com origem étnica e religião.** Uma parte desta skill trata de processos
  da Inquisição e de ascendência cristã-nova. Ligar essa inferência a uma pessoa identificável é
  tratar dado sensível, e "o documento é histórico e público" não resolve a questão sozinho: no
  Brasil a LGPD define origem racial ou étnica e convicção religiosa como dados sensíveis
  (art. 5º, II) e trata de forma diferente o uso exclusivamente particular e não económico. Se o
  resultado da pesquisa vai além do seu uso pessoal, pense antes de publicar.
- **O que sai da skill também é dado pessoal.** O auditor de GEDCOM imprime nomes, datas, lugares
  e vínculos, e o notificador envia o ficheiro inteiro. Isso vale para logs de agente, tickets,
  capturas de ecrã e ficheiros de teste: não cole a saída onde não colaria a árvore.
- **Distinga o documentado da lenda.** Toda afirmação deve ter fonte e cota; o que é tradição
  oral ou hipótese tem de ser rotulado como tal. Marque leituras paleográficas incertas com
  `[?]`. **Nunca invente** nomes, datas ou cotas. **Nunca apresente um homónimo como prova.**
- **Permita revisão humana.** Entregue imagem, transcrição e justificativa de cada elo;
  isso não exige interromper cada atualização local que o utilizador já autorizou.
- **Direitos de imagem.** As imagens de documentos pertencem aos arquivos de origem; respeite
  as condições de reprodução e atribuição de cada instituição.

---

## Licença

**MIT**, nos termos do ficheiro [`LICENSE`](LICENSE). A licença abrange **apenas** o código e a
documentação deste repositório — não confere quaisquer direitos sobre os documentos, imagens ou
dados de arquivos de terceiros, que continuam sujeitos às condições das respetivas instituições.

Se copiar esta skill para outro sítio, leve o `LICENSE` junto: a própria MIT exige que o aviso de
copyright seja preservado nas cópias.

```
SPDX-License-Identifier: MIT
```

---

## Contribuir

Contribuições são bem-vindas: novas fontes/arquivos, melhorias de paleografia, *scripts* mais
robustos. **Regra inquebrável:** nenhuma contribuição pode incluir dados pessoais reais,
genealogias de famílias específicas ou credenciais. Use sempre placeholders (`{GUID}`,
`{fileId}`, `TERMO`, `<ARK>`) ou registos públicos neutros nos exemplos.

## Integração dos aprendizados de pesquisa — 07/09/2026

Esta revisão parte das melhorias do autor em paginação de busca, `filesCount`, downloads,
auditoria GEDCOM, redacção de tokens, dependências opcionais e CI. Mantém essas
implementações e os seus testes; não repõe cópias antigas dos scripts.

- **Imagens DigitArq:** corrige o deslocamento para `fromIndex`, acrescenta `--start`
  sem alterar a enumeração completa por omissão e recusa respostas com índice errado,
  total alterado, IDs repetidos ou fim prematuro. O template JavaScript usa a mesma
  verificação; o teste live acrescenta duas páginas pequenas e não sobrepostas.
- **[Correlação e arquivo](references/09-correlacao-e-arquivo.md):** filiação cruzada de
  irmãos/cônjuges, nomes alternativos, datas declaradas versus calculadas, fontes
  dependentes, entrevistas não indutivas, originais com hashes e entrega verificável.
- **[Imigração Portugal–Brasil](references/10-imigracao-portugal-brasil.md):** distingue
  passaporte, embarque, chegada e recadastramento; pesquisa prontuários sem presumir
  custódia, viagens conjuntas ou existência do documento.
- **[Inventários](references/11-inventarios-e-certidoes-anexas.md):** leitura dos anexos
  tardios, certidões de batismo e emancipações, com contagem separada de imagens
  arquivadas e lidas e prova explícita dos vínculos.
- **[Gramps e visuais](references/12-gramps-e-arvores-visuais.md):** migração validada por
  reexportação, armazenamento persistente, primeiro acesso privado, atualizações por IDs,
  notas de pesquisa por pessoa e árvores que preservam incerteza e candidatos.
- **[FamilySearch](references/02-familysearch.md):** fontes vinculadas, filtros
  progressivos e requisitos conjuntos no Full-Text; download integral versus captura;
  login, elegibilidade da aplicação, escopo de API e restrição de imagem são estados
  distintos. A documentação não promete uma conexão ou exportação não validada.
- **Manutenção:** guia principal compacto e diário com cobertura, proveniência,
  conflitos e próximo passo. Apenas procedimentos genéricos: nenhum documento,
  identificador familiar, contato pessoal ou credencial foi incorporado.

Para validar: `ruff check scripts tests` e `pytest -q`. O teste de contrato na rede
continua opcional (`DIGITARQ_LIVE=1 pytest -q -m live`), fora do CI, com pausas e
amostra neutra. Os testes offline geram os seus próprios dados temporários.

## Integração operacional e CRAV — 08/09/2026

- **[Execução guiada](references/14-execucao-guiada.md)** e
  **[receitas por tarefa](references/15-receitas-operacionais.md)** tornam as decisões e
  condições de parada explícitas, com [ficha de operação](templates/operation_card.template.md).
  São apoio operacional; não prometem equivalência de capacidade entre modelos.
- **[CRAV](references/16-crav-pedidos-reproducao.md):** escolha da modalidade, cadastro
  protegido, teste real de acesso, referência individual versus livro, cópia digital,
  orçamento prévio, submissão única e conferência de protocolo/comprovativo.
- **[Ficha CRAV](templates/crav_request.template.md):** comentários explicam por que
  uma cópia Total exige atenção ao nível documental e por que clicar não comprova envio.
- A recuperação por login email/senha em perfil separado é alternativa observada para
  uma sessão travada, não correção universal nem permissão para reutilizar tokens.
- O roteiro de APIs complementares permanece disponível; a sincronização preserva
  scripts, testes e comentários explicativos do autor, incluindo o auditor GEDCOM.

Esta contribuição contém apenas procedimentos e templates vazios. Contas, protocolos,
recibos, documentos, dados familiares e resultados individuais permanecem fora do repositório.
