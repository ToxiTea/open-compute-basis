# Creates owner, agent, and recovery Technocore seeds on this machine.
# Writes files under %USERPROFILE%\.ocb\identities\
# Prints only public DIDs. Never commit, email, or paste the .seed files.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "Missing $Python. From the project folder run: python -m venv .venv ; .\.venv\Scripts\python -m pip install -e ."
}

$Out = Join-Path $env:USERPROFILE ".ocb\identities"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

foreach ($role in @("owner", "agent", "recovery")) {
    & $Python -m open_compute_basis technocore identity create --role $role --write-dir $Out
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# Restrict the folder to the current Windows user.
$acl = Get-Acl $Out
$acl.SetAccessRuleProtection($true, $false)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    [System.Security.Principal.WindowsIdentity]::GetCurrent().Name,
    "FullControl",
    "ContainerInherit,ObjectInherit",
    "None",
    "Allow"
)
$acl.AddAccessRule($rule)
Set-Acl -Path $Out -AclObject $acl

Write-Host ""
Write-Host "Done. Public DIDs are the .did files in $Out"
Write-Host "Secret seeds are the .seed files in the same folder."
Write-Host "Next: copy owner and recovery seeds into a password manager, then keep the files offline."
Write-Host "The agent seed later becomes GitHub secret TECHNOCORE_AGENT_SEED. Not now."
Write-Host "Do not paste any .seed contents into chat."
