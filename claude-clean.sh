#!/usr/bin/env zsh
cd "$(dirname "$0")"
unset_args=()
for var in ${(f)"$(env | grep -iE '^[A-Za-z_]*(TOKEN|SECRET|PASSW)[A-Za-z_]*=' | cut -d= -f1)"}; do
  unset_args+=(-u "$var")
done
exec env "${unset_args[@]}" claude --setting-sources project --model claude-fable-5 "$@"
