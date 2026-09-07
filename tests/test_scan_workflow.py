"""Regressao do template: paginacao real, sem rede nem imagens persistidas."""
import shutil
import subprocess
from pathlib import Path

import pytest

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="Node opcional para validar o template")


def test_template_valida_paginas_e_nao_aceita_cobertura_repetida():
    script = r"""
const assert = require('node:assert/strict');
const workflow = require('./templates/scan_workflow.example.js');
global.setTimeout = (fn) => { fn(); return 0; };
(async () => {
  const offsets = [];
  global.fetch = async (url) => {
    const p = new URL(url).searchParams;
    assert.equal(p.has('from'), false);
    const offset = Number(p.get('fromIndex'));
    offsets.push(offset);
    const n = Math.min(2, 5 - offset);
    return {ok: true, json: async () => ({
      fromIndex: offset, total: 5,
      results: Array.from({length: n}, (_, i) => ({id: offset + i, name: 'imagem'}))
    })};
  };
  const good = await workflow.listImages('guid');
  assert.equal(good.length, 5);
  assert.deepEqual(offsets, [0, 2, 4]);
  for (const mode of ['ignored', 'missing', 'duplicate', 'empty']) {
    let call = 0;
    global.fetch = async () => {
      const offset = call++ === 0 ? 0 : 2;
      return {ok: true, json: async () => ({
        fromIndex: mode === 'missing' ? undefined : mode === 'ignored' ? 0 : offset,
        total: 4,
        results: offset && mode === 'empty' ? [] :
          [{id: mode === 'duplicate' ? 1 : offset + 1}, {id: offset + 2}]
      })};
    };
    await assert.rejects(workflow.listImages('guid'));
    assert.ok(call <= 2);
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
"""
    subprocess.run([NODE, "-e", script], cwd=Path(__file__).resolve().parents[1],
                   check=True, capture_output=True, text=True, timeout=10)
