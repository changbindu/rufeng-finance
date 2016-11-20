# rufeng_finance(8) completion                                   -*- shell-script -*-
# place this file to /usr/share/bash-completion/completions/rufeng_finance

_rufeng_finance()
{
    local cur prev words cword
    _init_completion || return

    if (( $cword == 1)); then
        COMPREPLY=( $( compgen -W 'download check list drop plot analyze monitor' -- "$cur" ) )
        return 
    fi

    local options="--config= -h"
    case $prev in
    "download")
        options="-t --threads= -f --force_update $options"
        ;;
    "check")
        options="$options"
        ;;
    "list")
        options="-o $options"
        ;;
    "drop")
        options="$options"
        ;;
    "plot")
        options="-o --qfq -i --index-overlay $options"
        ;;
    "analyze")
        options="-t --threads= -o --plot-all $options"
        ;;
    "monitor")
        options="$options"
        ;;
    esac
    COMPREPLY=( $( compgen -W '$options' -- "$cur" ) )
} &&
complete -F _rufeng_finance rufeng_finance

alias rufeng_finance="python3 rufeng_finance.py"
# ex: ts=4 sw=4 et filetype=sh
