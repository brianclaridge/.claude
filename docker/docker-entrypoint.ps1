#!/usr/bin/env pwsh

New-Module -ScriptBlock {
  function _attn {
    Write-Host -ForegroundColor "Cyan" $args
  }

  function _info {
    Write-Host -ForegroundColor "Green" $args
  }

  function _msg {
    Write-Host -ForegroundColor "White" $args
  }

  function _warn {
    Write-Host -ForegroundColor "Yellow" $args
  }

  function _err {
    Write-Host -ForegroundColor "Red" $args
  }

  function _value {
    Write-Host -ForegroundColor "Magenta" -NoNewLine "$($args[0]): "
    Write-Host -ForegroundColor "Cyan" "$($args[1..($args.length-1)]) "
  }

  function _ll {
    ls -hal --color=auto ${args}
  }
  Set-Alias -Name ll -Value _ll

  function _lt {
    tree --dirsfirst -h -C
  }
  Set-Alias -Name lt -Value _lt

  function _link_scripts {
    # link baked scripts
    if (Test-Path -Path "/workspace/.claude/scripts") {
      Get-ChildItem "/workspace/.claude/scripts" -Filter *.ps1 |
      Foreach-Object {
        New-Alias `
          -Name $_.BaseName `
          -Value $_.FullName -Force -Scope Global
      }
    }
  }
  Set-Alias -Name link_scripts -Value _link_scripts

  Export-ModuleMember -Function * -Alias * -Variable * | Out-Null
} | Out-Null

_info "Linking shared scripts..."
link_scripts

# setup ssh
setup-ssh-env

_value "CLAUDE_PROJECT_SLUG" ${env:CLAUDE_PROJECT_SLUG}
_value "HOST_HOME" ${env:HOST_HOME}
_value "HOST_PWD" ${env:HOST_PWD}
_value "PARENT_PATH" ${env:PARENT_PATH}

# run any commands
$exit_code = 0
try {
  if ($args.length -gt 0) {
    _attn "Running ``$($args -join ' ')``"
    Invoke-Expression "$($args -join ' ')"
    $exit_code = $LASTEXITCODE
  }
}
catch {
  _err "error: $_"
  $exit_code = 1
}

exit $exit_code
