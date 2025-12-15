#!/usr/bin/env pwsh

$ErrorActionPreference = "Stop"

if (-Not (Test-Path -Path "/ssh")) {
  exit 0
}

if (-Not (Test-Path -Path "/ssh/id_rsa" -PathType Leaf)) {
  throw "id_rsa private key not found in /ssh"
}

Remove-Item -Recurse -Force "${HOME}/.ssh" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "${HOME}/.ssh" -Force | Out-Null
Copy-Item -Path "/ssh/*" -Destination "${HOME}/.ssh" -Force

chmod 700 "${HOME}/.ssh"
if ($LASTEXITCODE -ne 0) { throw "chmod 700 failed on ~/.ssh" }

chmod 600 ${HOME}/.ssh/*
if ($LASTEXITCODE -ne 0) { throw "chmod 600 failed on ~/.ssh/*" }
