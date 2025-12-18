# Source .claude/.env if it exists (environment variables for Claude tools)
$envFile = "${env:CLAUDE_PATH}/.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            [Environment]::SetEnvironmentVariable($name, $value, 'Process')
        }
    }
}

Function ll {
  ls -hal --color=auto
}

oh-my-posh init pwsh --config "${env:POSH_THEMES_PATH}/${env:POSH_THEME}.omp.json" | Invoke-Expression

$env:PATH = "${env:PATH}:/root/.local/bin"
