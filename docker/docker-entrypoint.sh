#!/bin/bash

# update ca trust
update-ca-trust --fresh &>/dev/null

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
    /workspace${CLAUDE_PROJECT_SLUG}/.claude \
    /workspace${CLAUDE_PROJECT_SLUG}/.claude/.data/logs \
    /workspace${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/screencaps \
    /workspace${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/videos \
    /workspace${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/data \
    /workspace${CLAUDE_PROJECT_SLUG}/.claude/.data/logs/playwright

# Clean stale Playwright browser locks (older than 30 minutes)
find /usr/local/share/playwright -name "mcp-*" -type d -mmin +30 -exec rm -rf {} + 2>/dev/null || true
find /tmp -name "*playwright*" -type d -cmin +30 -exec rm -rf {} + 2>/dev/null || true

# run gomplate
touch /workspace${CLAUDE_PROJECT_SLUG}/.claude/.data/logs/gomplate.log
gomplate --config /workspace${CLAUDE_PROJECT_SLUG}/.claude/config/gomplate.yaml --verbose \
  &> /workspace${CLAUDE_PROJECT_SLUG}/.claude/.data/logs/gomplate.log

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
        pwsh -NonInteractive -NoProfile -NoLogo -File /docker-entrypoint.ps1 ${@}
esac
