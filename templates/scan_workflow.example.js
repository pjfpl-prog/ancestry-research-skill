/*
 * scan_workflow.example.js
 * -------------------------------------------------------------------------
 * ESQUELETO (exemplo) de varredura MULTI-AGENTE de um livro nao indexado por
 * nome no DigitArq / Torre do Tombo. Padrao descrito em
 *   references/06-varredura-multiagente.md
 *
 * Padrao: lotear fileIds -> 1 subagente por lote (le imagens em paralelo) ->
 * consolidar JSON -> marcar homonimos -> ranquear candidatos ao alvo.
 *
 * Este e um TEMPLATE com PLACEHOLDERS ({GUID}, fileId, TERMO) e funcoes
 * marcadas TODO onde se liga ao harness de subagentes em uso (Claude Code /
 * Codex / outro) e a leitura de imagem. Sem credenciais: os endpoints do
 * DigitArq sao publicos (sem login). Adapte; nao copie cegamente.
 * -------------------------------------------------------------------------
 */

'use strict';

const BASE = 'https://digitarq.arquivos.pt';
const BATCH_SIZE = 12; // ~10-13; baixe para 8-10 se as imagens forem densas (2 colunas / letra apertada)

// ALVO: o "muro" que se procura. Preencha com placeholders neutros.
// (ver references/00-metodologia.md sobre como definir o muro)
const ALVO = {
  nome: 'TERMO',
  naturalidade: 'Lugar-X', // freguesia, nao so o pais
  anoEvento: null, // ex.: 1718 (casamento ~ANO); null = livro inteiro
  margemAnos: 5, // varre anoEvento +/- margem
  conjuge: 'TERMO', // ancora fortissima de identidade, se conhecido
};

// ---------------------------------------------------------------------------
// FASE A — Coordenador: localizar o livro e obter a lista de fileIds
// ---------------------------------------------------------------------------

/** Lista as imagens de um documento: results[].id = fileId; results[].name = rotulo/folio. */
async function listImages(guid) {
  const url = `${BASE}/rdigital/${guid}?from=0&max=500`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`listImages ${guid}: HTTP ${res.status}`);
  const data = await res.json();
  return (data.results || []).map((r) => ({ fileId: r.id, name: r.name }));
}

/** Ficha do documento (cota + datas) — para a citacao e para confirmar o livro certo. */
async function getDetails(guid) {
  const res = await fetch(`${BASE}/api/docs/details/${guid}`);
  if (!res.ok) throw new Error(`getDetails ${guid}: HTTP ${res.status}`);
  return res.json(); // { referenceCode, dateInitial, dateFinal, ... }
}

/** Divide um array em lotes de tamanho n. */
function chunk(arr, n) {
  const out = [];
  for (let i = 0; i < arr.length; i += n) out.push(arr.slice(i, i + n));
  return out;
}

// ---------------------------------------------------------------------------
// FASE B — Subagente: baixar (curl dissemination) + ler (ferramenta Read) + extrair
// ---------------------------------------------------------------------------

/**
 * Despacha UM subagente para ler um lote de fileIds.
 *
 * O subagente, para cada fileId:
 *   1) baixa hi-res:  GET /rdigital/dissemination?fileId=N  -> N.jpg
 *   2) le com a ferramenta Read sobre N.jpg (recorta/amplia se preciso —
 *      ver scripts/image_tools.py e references/03-paleografia.md)
 *   3) devolve uma lista de achados estruturados (1 por assento legivel)
 *
 * Contrato de saida (ver references/06-varredura-multiagente.md secao 5):
 *   { fileId, folio, anoCabecalho, tipoAssento, transcricao,
 *     pessoas:[{nome,papel,pais,avos,naturalidade,data}],
 *     isAlvo, isHomonimo, confianca, notas }
 *
 * Regras do subagente: le a imagem (nao adivinha); marca [?] no incerto;
 * NAO da veredicto final (so reporta); devolve JSON, nao prosa; CONTA imagens
 * recebidas/legiveis/ilegiveis/falhadas (registo de cobertura).
 *
 * TODO: ligar ao harness real de subagentes (Task/agent do Claude Code, etc.).
 * Aqui fica o prompt/instrucao que o subagente deve receber.
 */
async function dispatchSubagentForBatch({ guid, referenceCode, fileIds, alvo }) {
  const instrucao = buildSubagentInstruction({ guid, referenceCode, fileIds, alvo });

  // TODO: substituir pela chamada real ao subagente, ex.:
  //   const out = await runSubagent({ prompt: instrucao, allowTools: ['Bash', 'Read'] });
  //   return JSON.parse(out); // lista de achados do lote
  throw new Error(
    'TODO: ligar dispatchSubagentForBatch ao harness de subagentes. ' +
      'Instrucao pronta em `instrucao`. Lote: ' + JSON.stringify(fileIds)
  );
}

/** Monta a instrucao textual entregue a cada subagente (placeholders, sem dados pessoais). */
function buildSubagentInstruction({ guid, referenceCode, fileIds, alvo }) {
  const downloads = fileIds
    .map(
      (id) =>
        `  curl -s '${BASE}/rdigital/dissemination?fileId=${id}' -o ${id}.jpg`
    )
    .join('\n');

  return [
    `Voce le um LOTE de imagens de um livro nao indexado por nome.`,
    `Documento: {GUID}=${guid}  cota=${referenceCode || '<cota>'}`,
    `ALVO procurado: nome="${alvo.nome}", naturalidade="${alvo.naturalidade}",` +
      ` conjuge="${alvo.conjuge}", ano~${alvo.anoEvento ?? '?'}.`,
    ``,
    `Para CADA fileId do lote [${fileIds.join(', ')}]:`,
    `1) Baixe a imagem em alta resolucao:`,
    downloads,
    `2) Leia N.jpg com a ferramenta Read (recorte/amplie o trecho da filiacao se a tinta`,
    `   estiver fraca ou a letra apertada).`,
    `3) Extraia cada assento legivel para um objeto JSON (1 por assento):`,
    `   { fileId, folio, anoCabecalho, tipoAssento, transcricao,`,
    `     pessoas:[{nome,papel,pais,avos,naturalidade,data}],`,
    `     isAlvo, isHomonimo, confianca, notas }`,
    `   Paginas em branco/ilegiveis geram registo de cobertura (pessoas:[]).`,
    ``,
    `REGRAS: leia, nao adivinhe; marque [?] no incerto; NAO de veredicto final`,
    `(so reporte isAlvo/isHomonimo/confianca); transcreva o trecho que prova a`,
    `ligacao; confirme o ANO pelo cabecalho do assento, nao pela posicao na lista;`,
    `os folios podem estar fora de ordem. Conte imagens recebidas/legiveis/ilegiveis.`,
    ``,
    `DEVOLVA APENAS um array JSON de achados. Nada de prosa.`,
  ].join('\n');
}

// ---------------------------------------------------------------------------
// FASE C — Coordenador: consolidar + marcar homonimos + ranquear
// ---------------------------------------------------------------------------

/** Junta os achados de todos os lotes numa lista unica. */
function mergeFindings(batchResults) {
  return batchResults.flat();
}

/**
 * Marca homonimos: agrupa por nome normalizado e, dentro do grupo, conta quantos
 * EIXOS independentes batem entre os achados (naturalidade, filiacao, datas,
 * conjuge). Mesmo nome com contexto divergente => possivel homonimo.
 * Disciplina detalhada em references/00-metodologia.md secao 6.
 */
function markHomonyms(findings) {
  const norm = (s) => (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').trim();
  const byName = new Map();
  for (const f of findings) {
    for (const p of f.pessoas || []) {
      const key = norm(p.nome);
      if (!key) continue;
      if (!byName.has(key)) byName.set(key, []);
      byName.get(key).push({ finding: f, pessoa: p });
    }
  }
  // Anota homonimos: nome repetido com naturalidade/folio divergentes.
  for (const [, occ] of byName) {
    if (occ.length < 2) continue;
    const naturalidades = new Set(occ.map((o) => norm(o.pessoa.naturalidade)).filter(Boolean));
    if (naturalidades.size > 1) {
      for (const o of occ) o.finding.notas = (o.finding.notas ? o.finding.notas + '; ' : '') + 'possivel homonimo (nome repetido, naturalidade divergente)';
    }
  }
  return findings;
}

/**
 * Ranqueia candidatos ao ALVO por nº de eixos que batem (nome+naturalidade+conjuge+ano).
 * Empate real => manter hipoteses concorrentes (nao escolher o conveniente).
 */
function rankCandidates(findings, alvo) {
  const norm = (s) => (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').trim();
  const score = (f) => {
    let s = 0;
    for (const p of f.pessoas || []) {
      if (norm(p.nome) === norm(alvo.nome)) s += 2; // nome e o gatilho, nao a prova
      if (alvo.naturalidade && norm(p.naturalidade) === norm(alvo.naturalidade)) s += 2;
      if (alvo.conjuge && (f.pessoas || []).some((q) => norm(q.nome) === norm(alvo.conjuge))) s += 3; // conjuge = ancora forte
      if (alvo.anoEvento && Math.abs((f.anoCabecalho || 0) - alvo.anoEvento) <= alvo.margemAnos) s += 1;
    }
    return s;
  };
  return findings
    .map((f) => ({ finding: f, score: score(f) }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score);
}

/** Resumo de cobertura: total varrido, legiveis, ilegiveis (negativo conta como progresso). */
function coverageSummary(findings, fileIdsVarridos) {
  const legiveis = findings.filter((f) => (f.pessoas || []).length > 0).length;
  const ilegiveis = findings.filter((f) => (f.pessoas || []).length === 0).length;
  const anos = [...new Set(findings.map((f) => f.anoCabecalho).filter(Boolean))].sort();
  return { imagensVarridas: fileIdsVarridos.length, assentosLegiveis: legiveis, paginasIlegiveis: ilegiveis, anosCobertos: anos };
}

// ---------------------------------------------------------------------------
// Orquestracao
// ---------------------------------------------------------------------------

async function scanBook(guid) {
  // FASE A
  const details = await getDetails(guid);
  const referenceCode = details.referenceCode || '<cota>';
  let images = await listImages(guid);

  // TODO (opcional): recortar o intervalo de folios pelo ano-alvo usando thumbs
  //   GET /rdigital/thumb?fileId=N  (ver references/06-varredura-multiagente.md secao 3.2)
  // images = filterByYearWindow(images, ALVO);

  const fileIds = images.map((i) => i.fileId);
  const batches = chunk(fileIds, BATCH_SIZE);

  // FASE B — um subagente por lote, EM PARALELO
  const batchResults = await Promise.all(
    batches.map((fileIdsLote) =>
      dispatchSubagentForBatch({ guid, referenceCode, fileIds: fileIdsLote, alvo: ALVO })
    )
  );

  // FASE C
  let findings = mergeFindings(batchResults);
  findings = markHomonyms(findings);
  const ranked = rankCandidates(findings, ALVO);
  const coverage = coverageSummary(findings, fileIds);

  // Registar com fonte + confianca (templates/research_log.template.md). Negativos contam.
  return { guid, referenceCode, ranked, coverage, findings };
}

module.exports = {
  scanBook,
  listImages,
  getDetails,
  chunk,
  buildSubagentInstruction,
  markHomonyms,
  rankCandidates,
  coverageSummary,
};

// Uso (exemplo):
//   const { scanBook } = require('./scan_workflow.example.js');
//   scanBook('{GUID}').then((r) => console.log(JSON.stringify(r, null, 2)));
