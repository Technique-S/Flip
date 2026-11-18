$py = 'C:\Users\Kazi\AppData\Local\Temp\opencode\m3c-venv\Scripts\python.exe'
$env:PYTHONPATH = 'C:\Users\Kazi\Documents\Flip\Flip_M1_Engineering_Starter\flip-m3-independent-review\packages\flip-core\src'
function Workers { @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*solver_worker*' } | ForEach-Object { $_.ProcessId }) }
$code = @'
import sys
sys.path.insert(0, r"C:\Users\Kazi\Documents\Flip\Flip_M1_Engineering_Starter\flip-m3-independent-review\fixtures\m3-independent-review")
import review_common as rc
from flip_core.isolation import run_worker
base = rc.base_request(); p = rc.parse_request(base.model_dump(mode="json")); c = rc.compile_project(p.project, p.imports)
import flip_core.cnf as cnf
enc, inputs = cnf.miter(c.reference, c.candidate, p.project.comparison.inputMap, p.project.comparison.outputMap)
for probe in ("timeout-probe", "crash-probe"):
    r = run_worker(enc.clauses, inputs, p.project.limits, _probe=probe)
    print(probe, r["outcome"], r.get("reason"), r["containment"], flush=True)
'@
$before = Workers
$code | & $py -
$immediate = Workers
Start-Sleep -Seconds 2
$after = Workers
Write-Output "before=$($before -join ',')"
Write-Output "immediate=$($immediate -join ',')"
Write-Output "after2s=$($after -join ',')"
Write-Output "new_workers_persisting=$(@($after | Where-Object { $_ -notin $before }).Count)"
