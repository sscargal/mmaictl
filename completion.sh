# Add this script to your shell configuration to enable tab completion.
_mmaictl_completions()
{
    COMPREPLY=( $(compgen -W "$(mmaictl --help | grep '  [a-z]' | awk '{print $1}')" -- ${COMP_WORDS[COMP_CWORD]}) )
}
complete -F _mmaictl_completions mmaictl
