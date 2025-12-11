#!/usr/bin/env pwsh
param (
    [Parameter(Mandatory=$true, Position = 0)]
    [string]
    $container_path,

    [Parameter(Position = 1)]
    [string]
    $container_name = "${env:HOSTNAME}"
)

$json = docker inspect ${container_name} | ConvertFrom-Json
$source = ${json}.Mounts | where { $_.Destination -eq ${container_path} } | select -ExpandProperty Source
return "${source}"
