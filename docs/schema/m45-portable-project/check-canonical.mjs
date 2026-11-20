import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
const canonical = value => {
 if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
 if (value && typeof value === "object") return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${canonical(value[k])}`).join(",")}}`;
 return JSON.stringify(value);
};
const hash = value => `0x${createHash("sha256").update(canonical(value)).digest("hex")}`;
const vectors = JSON.parse(readFileSync(new URL("./1.1.0/golden.json", import.meta.url)));
for (const [i, p] of vectors.packages.entries()) {
 assert.equal(canonical(p), vectors.canonical[i]);
 assert.equal(hash(p), vectors.hashes[i]);
 assert.equal(hash(p.executionRequest), p.executionRequestHash);
 const metadata = Object.fromEntries(["schemaVersion", "kind", "tests", "noDeclaredTests", "evidenceRefs", "provenance", "agentTaskRef"].map(k => [k, p[k]]));
 assert.equal(hash(metadata), p.revision.metadataHash);
 for (const record of [...p.ancestors, p.revision]) {
  const {revisionHash, ...preimage} = record;
  assert.equal(hash(preimage), revisionHash);
 }
}
console.log(`Portable Python/Node canonical parity: ${vectors.packages.length} packages PASS`);
