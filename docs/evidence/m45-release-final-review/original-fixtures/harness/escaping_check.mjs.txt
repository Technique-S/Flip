import { text, table } from "file:///C:/Users/Kazi/Documents/Flip/flip-m45-release-final-review/apps/showcase/lib.mjs";
const a = text('<img src=x onerror="attack()">');
console.log("escaped=", a);
if (a !== "&lt;img src=x onerror=&quot;attack()&quot;&gt;") process.exit(1);
const b = table("<script>", ["<img>"], [["<svg onload=attack()>"]]);
if (b.includes("<script>") || b.includes("<img>") || b.includes("<svg")) process.exit(1);
console.log("ESCAPE_OK");
