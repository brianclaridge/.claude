#!/usr/bin/env pwsh

$ErrorActionPreference = "Stop"

New-Module -ScriptBlock {
  function _run {
    param(
      [string]$Message,
      [scriptblock]$Command,
      [string]$CountSuffix = $null
    )

    Write-Host " " -NoNewline
    Write-Host "○" -ForegroundColor DarkGray -NoNewline
    Write-Host " $Message..." -NoNewline

    try {
      $ErrorActionPreference = "Stop"

      if ($CountSuffix) {
        $result = & $Command 2>&1
      }
      else {
        & $Command *> $null
        $result = $null
      }

      if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        throw "Exit code: $LASTEXITCODE"
      }

      Write-Host "`r " -NoNewline
      Write-Host "✓" -ForegroundColor Green -NoNewline
      Write-Host " $Message" -NoNewline

      if ($CountSuffix -and $result -and $result -gt 0) {
        Write-Host " ($result $CountSuffix)" -ForegroundColor DarkGray
      }
      else {
        Write-Host "   "
      }
    }
    catch {
      $errorMsg = if ($_.Exception.Message) { $_.Exception.Message } else { $_.ToString() }

      Write-Host "`r " -NoNewline
      Write-Host "✗" -ForegroundColor Red -NoNewline
      Write-Host " $Message" -ForegroundColor Red -NoNewline
      Write-Host " - $errorMsg" -ForegroundColor DarkRed
      Write-Host ""

      [Console]::Out.Flush()
      [Console]::Error.Flush()

      [Environment]::Exit(1)
    }
  }

  function _exec {
    param([string]$Cmd)
    Invoke-Expression $Cmd
    if ($LASTEXITCODE -ne 0) {
      throw "Command failed: $Cmd"
    }
  }

  function _ok {
    param([string]$Message)
    Write-Host " " -NoNewline
    Write-Host "✓" -ForegroundColor Green -NoNewline
    Write-Host " $Message"
  }

  function _fail {
    param([string]$Message)
    Write-Host " " -NoNewline
    Write-Host "✗" -ForegroundColor Red -NoNewline
    Write-Host " $Message" -ForegroundColor Red
  }

  function _attn {
    Write-Host -ForegroundColor Cyan " → $args"
  }

  function _info {
    Write-Host -ForegroundColor Green $args
  }

  function _msg {
    Write-Host -ForegroundColor White $args
  }

  function _warn {
    Write-Host " " -NoNewline
    Write-Host "⚠" -ForegroundColor Yellow -NoNewline
    Write-Host " $args" -ForegroundColor Yellow
  }

  function _err {
    Write-Host " " -NoNewline
    Write-Host "✗" -ForegroundColor Red -NoNewline
    Write-Host " $args" -ForegroundColor Red
  }

  function _header {
    param([string]$Message)
    Write-Host ""
    Write-Host " $Message" -ForegroundColor White
    Write-Host " $("-" * $Message.Length)" -ForegroundColor DarkGray
  }

  function _value {
    param(
      [string]$Name,
      [string]$Value
    )
    $padding = 24
    $paddedName = $Name.PadRight($padding)
    Write-Host "   " -NoNewline
    Write-Host $paddedName -ForegroundColor DarkGray -NoNewline
    if ($Value) {
      Write-Host $Value -ForegroundColor Cyan
    }
    else {
      Write-Host "(not set)" -ForegroundColor DarkYellow
    }
  }

  function _ll {
    ls -hal --color=auto @args
  }
  Set-Alias -Name ll -Value _ll

  function _lt {
    tree --dirsfirst -h -C @args
  }
  Set-Alias -Name lt -Value _lt

  function _link_scripts {
    if (Test-Path -Path "${env:CLAUDE_SCRIPTS_PATH}") {
      Get-ChildItem "${env:CLAUDE_SCRIPTS_PATH}" -Filter *.ps1 |
      ForEach-Object {
        New-Alias -Name $_.BaseName -Value $_.FullName -Force -Scope Global
      }
    }
  }
  Set-Alias -Name link_scripts -Value _link_scripts

  Export-ModuleMember -Function * -Alias * -Variable * | Out-Null
} | Out-Null

# --- Initialization ---
_run ".ps1 scripts linked" { link_scripts }
_run "gomplate templates rendered" { run-gomplate }
_run "~/.ssh environment copied & configured" { run-ssh-setup }
_run "playwright cleanup" { run-cleanup-playwright } -CountSuffix "removed"

# --- Environment ---
_header "Environment"
_value "CLAUDE_PROJECT_SLUG" $env:CLAUDE_PROJECT_SLUG
_value "CLAUDE_WORKSPACE_PATH" $env:CLAUDE_WORKSPACE_PATH
_value "CLAUDE_PATH" $env:CLAUDE_PATH
_value "CLAUDE_DATA_PATH" $env:CLAUDE_DATA_PATH
_value "CLAUDE_LOGS_PATH" $env:CLAUDE_LOGS_PATH
_value "CLAUDE_AGENTS_PATH" $env:CLAUDE_AGENTS_PATH
_value "CLAUDE_HOOKS_PATH" $env:CLAUDE_HOOKS_PATH
_value "CLAUDE_SCRIPTS_PATH" $env:CLAUDE_SCRIPTS_PATH
_value "CLAUDE_SKILLS_PATH" $env:CLAUDE_SKILLS_PATH
_value "HOME_CLAUDE_ROOT_PATH" $env:HOME_CLAUDE_ROOT_PATH
_value "PROJECTS_YML_PATH" $env:PROJECTS_YML_PATH
_value "CONFIG_YML_PATH" $env:CONFIG_YML_PATH
_value "HOME_OS" $env:HOME_OS
_value "HOME_DIR" $env:HOME_DIR
_value "DOCKER_SOCK_PATH" $env:DOCKER_SOCK_PATH
_value "AWS_CONFIG_FILE" $env:AWS_CONFIG_FILE
_value "POSH_THEME" $env:POSH_THEME
Write-Host ""

oh-my-posh init pwsh --config "${env:POSH_THEMES_PATH}/${env:POSH_THEME}.omp.json" | Invoke-Expression

# --- Execute command if provided ---
if ($args.Length -gt 0) {
  $cmd = $args[0].ToLower()
  $claudeAliases = @("cc", "claude", "vibe", "ai", "code")

  if ($cmd -in $claudeAliases) {
    $debug = $args -contains "--debug" -or $args -contains "-d"

    if ($debug) {
      & "${env:CLAUDE_SCRIPTS_PATH}/run-claude.ps1" -Debug
    }
    else {
      & "${env:CLAUDE_SCRIPTS_PATH}/run-claude.ps1"
    }

    exit $LASTEXITCODE
  }

  # Default: run arbitrary command
  _attn "Running: $($args -join ' ')"
  try {
    Invoke-Expression "$($args -join ' ')"
    exit $LASTEXITCODE
  }
  catch {
    _err "Command failed: $_"
    exit 1
  }
}
