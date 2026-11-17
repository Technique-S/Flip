// Independent Node reference for flip-json-v1. No npm dependencies.
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

function canonical(v) {
  if (v === null || typeof v === 'boolean') return JSON.stringify(v);
  if (typeof v === 'number') {
    if (!Number.isSafeInteger(v) || Object.is(v, -0)) throw Error('unsafe integer');
    return JSON.stringify(v);
  }
  if (typeof v === 'string') {
    if (!v.isWellFormed()) throw Error('lone surrogate');
    return JSON.stringify(v);
  }
  if (Array.isArray(v)) return '[' + v.map(canonical).join(',') + ']';
  if (typeof v !== 'object') throw Error('unsupported type');
  return '{' + Object.keys(v).sort().map(k => {
    if (!/^[\x00-\x7f]*$/.test(k)) throw Error('non-ASCII key');
    return JSON.stringify(k) + ':' + canonical(v[k]);
  }).join(',') + '}';
}

const examples = JSON.parse(readFileSync(new URL('./canonical-golden.json', import.meta.url)));
for (const v of examples.vectors) {
  const text = canonical(v.input);
  assert.equal(text, v.canonical);
  assert.equal(Buffer.from(text).toString('hex'), v.utf8Hex);
  assert.equal('0x' + createHash('sha256').update(text, 'utf8').digest('hex'), v.sha256);
}
console.log(`${examples.vectors.length} canonical vectors passed in Node ${process.version}`);
