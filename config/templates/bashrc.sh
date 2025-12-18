# ~/.bashrc: executed by bash(1) for non-login shells.

# if not running interactively, don't do anything
[ -z "$PS1" ] && return

# Source .claude/.env if it exists (environment variables for Claude tools)
if [ -f "${CLAUDE_PATH}/.env" ]; then
    set -a  # automatically export all variables
    source "${CLAUDE_PATH}/.env"
    set +a
fi

export CONTAINER_ID=`cat /proc/self/cgroup | grep -o -E '[0-9a-f]{64}' | head -n 1`

alias less='less -R'
alias diff='colordiff'
alias glog='git log --oneline --graph --color --all --decorate'
alias ll='ls -hal'
alias lt='tree --dirsfirst -h -C'

eval "$(oh-my-posh init bash --config ${POSH_THEMES_PATH}/${POSH_THEME}.omp.json)"
