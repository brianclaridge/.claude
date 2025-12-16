#!/bin/bash

set -eo pipefail
trap 'echo "ERROR: Script failed at line $LINENO" >&2' ERR

# --- Helper functions ---
_run() {
  local msg="$1"
  shift

  printf " \033[90m○\033[0m %s..." "$msg"

  if "$@" &>/dev/null; then
    printf "\r \033[32m✓\033[0m %s   \n" "$msg"
  else
    printf "\r \033[31m✗\033[0m %s - exit code: $?\n" "$msg"
    exit 1
  fi
}

# --- Initialization ---
_run "ca certificates updated" update-ca-certificates

_run "directories created" mkdir -p \
  ${HOME}/.claude \
  ${HOME}/.ssh \
  ${HOME}/.aws \
  ${HOME}/.docker \
  ${HOME}/.config/powershell \
  ${HOME}/.config/htop \
  ${HOME}/.config/ccstatusline \
  /etc/ansible \
  ${CLAUDE_DATA_PATH}/playwright/screencaps \
  ${CLAUDE_DATA_PATH}/playwright/videos \
  ${CLAUDE_DATA_PATH}/playwright/data \
  ${CLAUDE_LOGS_PATH}/playwright

_run "ssh config permissions set" bash -c "touch /root/.ssh/config && chmod 0600 /root/.ssh/config"

_run "htop defaults configured" bash -c 'echo "tree_view=1" > ${HOME}/.config/htop/htoprc'

# --- Delegate to PowerShell ---
case "${1}" in
  shell|pwsh|powershell)
    pwsh -Interactive -NoExit -NoLogo -File /docker-entrypoint.ps1
    ;;

  sh|bash)
    echo " → using sh/bash, executing: ${*}"
    exec "${@}"
    ;;

  *)
    pwsh -NoLogo -NoProfile -File /docker-entrypoint.ps1 "$@"
    exit $?
    ;;
esac
