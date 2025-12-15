#!/bin/bash

set -eo pipefail
trap 'echo "ERROR: Script failed at line $LINENO" >&2' ERR

# update ca trust
update-ca-certificates &>/dev/null

# ensure directories
mkdir -p \
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

# set permissions (gomplate doesn't support mode like confd)
touch /root/.ssh/config
chmod 0600 /root/.ssh/config

# defaults
echo "tree_view=1" > ${HOME}/.config/htop/htoprc

case "${1}" in
  shell|pwsh|powershell)
    pwsh -Interactive -NoExit -NoLogo -File /docker-entrypoint.ps1
    ;;

  sh|bash)
    echo "using sh/bash, executing:"
    echo "${@}"
    exec "${@}"
    ;;

  *)
    pwsh -NoLogo -NoProfile -Interactive -NoExit -File /docker-entrypoint.ps1 "$@"
    exit $?
esac
