# M4-B trusted-consumption CLI acceptance runner (appends to the M4-B transcript).
# Claims are captured from executed `flip compare` output by build_fixtures.py;
# none of the forged variants are asserted to pass.

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
$req = "fixtures/m4-ux-acceptance/cli-cases/requests"
$cases = @(
    @{ Id = "C22"; Desc = "consume unmodified captured claim"; Args = @("consume", "--project", "$req/consumption-valid.json") }
    @{ Id = "C23"; Desc = "consume forged DIFFERENT verdict"; Args = @("consume", "--project", "$req/consumption-forged-verdict.json") }
    @{ Id = "C24"; Desc = "consume with changed reference pin"; Args = @("consume", "--project", "$req/consumption-changed-reference.json") }
    @{ Id = "C25"; Desc = "consume with CURRENT relabel"; Args = @("consume", "--project", "$req/consumption-current-relabel.json") }
    @{ Id = "C26"; Desc = "consume captured DIFFERENT witness"; Args = @("consume", "--project", "$req/consumption-different.json") }
)

$transcriptPath = Join-Path $execDir "transcript.json"
$transcript = Get-Content -Raw -Path $transcriptPath | ConvertFrom-Json

foreach ($case in $cases) {
    $out = Join-Path $execDir ($case.Id + ".stdout.txt")
    $err = Join-Path $execDir ($case.Id + ".stderr.txt")
    $argList = @("run", "--frozen", "flip") + $case.Args
    $p = Start-Process -FilePath $UvPath -ArgumentList $argList -NoNewWindow -Wait -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $hash = (Get-FileHash -Algorithm SHA256 -Path $out).Hash.ToLowerInvariant()
    $errText = (Get-Content -Raw -Path $err -ErrorAction SilentlyContinue)
    if (-not $errText) { $errText = "" }
    $transcript.cases += [pscustomobject]@{
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

$transcript | ConvertTo-Json -Depth 8 | Set-Content -Path $transcriptPath -Encoding utf8
Write-Output "updated transcript: $transcriptPath"
