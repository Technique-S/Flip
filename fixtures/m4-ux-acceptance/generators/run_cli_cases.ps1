# M4-B independent CLI acceptance runner.
# Executes only commands implemented on the accepted M3 baseline and records raw
# stdout, stderr and process exit codes. No claim is inferred from process success.
#
# Usage from repository root:
#   powershell -ExecutionPolicy Bypass -File fixtures/m4-ux-acceptance/generators/run_cli_cases.ps1
# Optional: -UvPath <path-to-uv.exe>

param(
    [string]$UvPath = ""
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
Set-Location $root

if (-not $UvPath) {
    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd) { $UvPath = $cmd.Source }
    else { $UvPath = Join-Path $env:APPDATA "Python\Python314\Scripts\uv.exe" }
}
if (-not (Test-Path $UvPath)) { throw "uv not found: $UvPath" }

$execDir = "docs/evidence/m4-ux-acceptance/executed"
New-Item -ItemType Directory -Force -Path $execDir | Out-Null

$req = "fixtures/m4-ux-acceptance/cli-cases/requests"
$proc = "0x839bdd6fa7a66416a609a735e11de5411b98574e"
$manifest = "$req/import-manifest.json"

$cases = @(
    @{ Id = "C01"; Desc = "version"; Args = @("--version") }
    @{ Id = "C02"; Desc = "help"; Args = @("--help") }
    @{ Id = "C03"; Desc = "compose baseline"; Args = @("compose", "--project", "$req/half-adder-equivalent.json") }
    @{ Id = "C04"; Desc = "compare EQUIVALENT"; Args = @("compare", "--project", "$req/half-adder-equivalent.json") }
    @{ Id = "C05"; Desc = "compare DIFFERENT"; Args = @("compare", "--project", "$req/half-adder-different-output-order.json") }
    @{ Id = "C06"; Desc = "compare UNKNOWN timeout"; Args = @("compare", "--project", "$req/half-adder-unknown-timeout.json") }
    @{ Id = "C07"; Desc = "vectors match"; Args = @("vectors", "--project", "$req/half-adder-vectors.json") }
    @{ Id = "C08"; Desc = "caller CURRENT flag cannot grant freshness"; Args = @("compare", "--project", "$req/half-adder-current-freshness-claim.json") }
    @{ Id = "C09"; Desc = "malformed input"; Args = @("compare", "--project", "$req/malformed-request.json") }
    @{ Id = "C10"; Desc = "unsupported version"; Args = @("compare", "--project", "$req/unsupported-version.json") }
    @{ Id = "C11"; Desc = "wrong chain inspect"; Args = @("inspect", "--chain-id", "8453", "--processor", $proc, "--id", "1") }
    @{ Id = "C12"; Desc = "invalid pin mapping"; Args = @("compare", "--project", "$req/invalid-pin-map.json") }
    @{ Id = "C13"; Desc = "wrong chain import"; Args = @("import", "--chain-id", "8453", "--processor", $proc, "--id", "1") }
    @{ Id = "C14"; Desc = "RPC unavailable"; Args = @("inspect", "--processor", $proc, "--id", "1", "--rpc-url", "http://127.0.0.1:1", "--timeout-ms", "200", "--retries", "0") }
    @{ Id = "C15"; Desc = "validate contract"; Args = @("validate", "circuit-identity", "docs/schema/examples/circuit-identity.json") }
    @{ Id = "C16"; Desc = "canonical contract"; Args = @("canonical", "circuit-identity", "docs/schema/examples/circuit-identity.json") }
    @{ Id = "C17"; Desc = "hash manifest"; Args = @("hash", "manifest", "docs/schema/examples/manifest.json") }
    @{ Id = "C18"; Desc = "preflight reserved"; Args = @("preflight", "--project", "$req/half-adder-equivalent.json") }
    @{ Id = "C19"; Desc = "export reserved"; Args = @("export", "--project", "$req/half-adder-equivalent.json") }
    @{ Id = "C20"; Desc = "sample reserved"; Args = @("sample") }
    @{ Id = "C21"; Desc = "revalidate wrong chain"; Args = @("revalidate", "--chain-id", "8453", "--manifest", $manifest) }
)

$results = @()
foreach ($case in $cases) {
    $out = Join-Path $execDir ($case.Id + ".stdout.txt")
    $err = Join-Path $execDir ($case.Id + ".stderr.txt")
    $argList = @("run", "--frozen", "flip") + $case.Args
    $p = Start-Process -FilePath $UvPath -ArgumentList $argList -NoNewWindow -Wait -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $hash = (Get-FileHash -Algorithm SHA256 -Path $out).Hash.ToLowerInvariant()
    $errText = (Get-Content -Raw -Path $err -ErrorAction SilentlyContinue)
    if (-not $errText) { $errText = "" }
    $results += [pscustomobject]@{
        id = $case.Id
        description = $case.Desc
        command = ("flip " + ($case.Args -join " "))
        exitCode = $p.ExitCode
        stdoutFile = "$execDir/$($case.Id).stdout.txt"
        stdoutSha256 = $hash
        stderr = $errText.Trim()
    }
    Write-Output ("{0} exit={1} {2}" -f $case.Id, $p.ExitCode, $case.Desc)
}

$transcript = [pscustomobject]@{
    schemaVersion = "m4-ux-acceptance-1"
    baseline = "af8ba1f109a2a1c59fe36be044bc025a127ea025"
    runner = "fixtures/m4-ux-acceptance/generators/run_cli_cases.ps1"
    note = "Raw stdout/stderr captured from the pinned M3 baseline; exit codes are process outcomes, not proof verdicts."
    cases = $results
}
$transcript | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $execDir "transcript.json") -Encoding utf8
Write-Output "transcript: $execDir/transcript.json"
