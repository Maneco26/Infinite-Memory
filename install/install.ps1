# Infinite-Memory installer (Windows). Wrapper around install.py.
$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command py -ErrorAction SilentlyContinue).Source }
if (-not $py) { Write-Error "Python 3 is required but was not found in PATH."; exit 1 }
& $py "$dir\install.py" @args
