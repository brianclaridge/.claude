Function ll {
  ls -hal --color=auto
}

oh-my-posh init pwsh --config "${env:POSH_THEMES_PATH}/${env:POSH_THEME}.omp.json" | Invoke-Expression

$env:PATH = "${env:PATH}:/root/.local/bin"
