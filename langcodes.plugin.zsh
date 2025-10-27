# Provides `langcode` function for converting between language tags and English names.

# Resolve plugin directory even when sourced via symbolic links.
_langcodes_plugin_dir=${0:A:h}
_langcodes_script="$_langcodes_plugin_dir/inspect_langcodes.py"

# Ensure helper script exists before defining the function.
if [[ ! -r $_langcodes_script ]]; then
  print -u2 "langcodes plugin: missing helper script at $_langcodes_script"
  return 1
fi

langcode() {
  if ! command -v uv >/dev/null 2>&1; then
    print -u2 "langcode: uv command not found"
    return 127
  fi

  "$_langcodes_script" "$@"
}

# Optional shorter alias.
alias lc=langcode
