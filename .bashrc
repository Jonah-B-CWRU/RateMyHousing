export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] $$ export Path="$PYENV_ROOT/bin:$PATH"
eval ("$pyenv init -)"
