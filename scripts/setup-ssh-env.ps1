#!/usr/bin/env pwsh

_attn "Setting up SSH environment..."

if (Test-Path -Path "/ssh") {
  _info "Setting up ${HOME}/.ssh directory..."
  rm -rf ${HOME}/.ssh && mkdir -p ${HOME}/.ssh
  if (-Not (Test-Path -Path "/ssh/id_rsa" -PathType Leaf)) {
    _err "An id_rsa private key was not detected. Have you created one?"
    exit 1
  }
  cp /ssh/* ${HOME}/.ssh
  chmod 700 ${HOME}/.ssh
  chmod 600 ${HOME}/.ssh/*
  ls -hal ${HOME}/.ssh
}
