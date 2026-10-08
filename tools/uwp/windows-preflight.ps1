param([string]$GameMakerPath = '')
$ErrorActionPreference = 'Stop'
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$vs = if (Test-Path $vswhere) { & $vswhere -latest -products '*' -property installationPath }
$kits = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10'
$sdkVersions = @(Get-ChildItem (Join-Path $kits 'Include') -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
$packageTools = @(Get-ChildItem (Join-Path $kits 'bin') -Filter makeappx.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
$gameMakerCandidates = @(
    "$env:APPDATA\GameMaker-Studio",
    "$env:APPDATA\GameMakerStudio2",
    "$env:ProgramFiles\GameMaker Studio 2",
    "${env:ProgramFiles(x86)}\GameMaker-Studio",
    "${env:ProgramFiles(x86)}\Steam\steamapps\common\GameMaker Studio"
)
if ($GameMakerPath) { $gameMakerCandidates += $GameMakerPath }
$foundGameMaker = @($gameMakerCandidates | Where-Object { Test-Path $_ })
$report = [ordered]@{
    computer = $env:COMPUTERNAME
    visualStudio = $vs
    windowsSDKs = $sdkVersions
    makeAppx = $packageTools
    gameMakerLocations = $foundGameMaker
    gameMakerUwpExporterVerified = $false
    buildReady = $false
    note = 'No deployment. A compatible licensed GameMaker compiler/exporter and populated source are still required; directory presence does not verify a license or exporter.'
}
$report | ConvertTo-Json -Depth 5
if (!$vs -or !$packageTools.Count -or !$foundGameMaker.Count) { exit 1 }
# Even when installed, export entitlement/version needs a real compile probe.
exit 2
