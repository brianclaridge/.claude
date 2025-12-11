#!/bin/bash

clear

# update ca trust
update-ca-trust --fresh &>/dev/null

# ensure directories
mkdir -p \
    ${HOME}/.ssh \
    ${HOME}/.aws \
    ${HOME}/.docker \
    ${HOME}/.config/powershell \
    ${HOME}/.config/htop \
    /etc/ansible \
    /workspace/.claude \
    /workspace/.claude/.data/logs \
    /workspace/.claude/.data/playwright/screencaps \
    /workspace/.claude/.data/playwright/videos \
    /workspace/.claude/.data/playwright/data \
    /workspace/.claude/.data/logs/playwright

# Clean stale Playwright browser locks (older than 30 minutes)
find /usr/local/share/playwright -name "mcp-*" -type d -mmin +30 -exec rm -rf {} + 2>/dev/null || true
find /tmp -name "*playwright*" -type d -cmin +30 -exec rm -rf {} + 2>/dev/null || true

touch /workspace/.claude/.data/logs/confd.log
confd \
  -backend env \
  -confdir /etc/confd \
  -onetime &> /workspace/.claude/.data/logs/confd.log

# defaults
echo "tree_view=1" > ${HOME}/.config/htop/htoprc
touch /workspace/.claude/.env

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
        pwsh -NonInteractive -NoProfile -NoLogo -File /docker-entrypoint.ps1 ${@}
esac
