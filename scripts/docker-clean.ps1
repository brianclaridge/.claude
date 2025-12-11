#!/usr/bin/env pwsh

$containers = "$( docker ps -a | grep -v "${env:HOSTNAME}" | awk 'NR>1 {print $1}' )"

if (-not ([string]::IsNullOrEmpty($containers))) {
    _attn "stopping containers..."
    ${containers}.split() | ForEach-Object { docker stop $_ } 2>&1 | Out-Null

    _attn "removing containers..."
    ${containers}.split() | ForEach-Object { docker rm --force --volumes $_ } 2>&1 | Out-Null

    _attn "killing containers..."
    ${containers}.split() | ForEach-Object { docker kill $_ } 2>&1 | Out-Null
}
else {
    _attn "no containers left to clean..."
}
