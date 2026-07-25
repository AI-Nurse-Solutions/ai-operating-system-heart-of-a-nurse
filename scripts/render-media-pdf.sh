#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  printf 'usage: %s INPUT_HTML OUTPUT_PDF\n' "$0" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
IMAGE="mcr.microsoft.com/playwright@sha256:5b8f294aff9041b7191c34a4bab3ac270157a28774d4b0660e9743297b697e48"

translate_path() {
  local path="$1"
  case "$path" in
    "$ROOT"/*) printf '/work/%s' "${path#"$ROOT"/}" ;;
    *) printf 'renderer path must be inside %s: %s\n' "$ROOT" "$path" >&2; return 2 ;;
  esac
}

input="$(translate_path "$1")"
output="$(translate_path "$2")"

exec docker run --rm \
  --network=none \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  --security-opt no-new-privileges \
  --cap-drop=ALL \
  --volume "$ROOT:/work:rw" \
  --workdir /work \
  --entrypoint node \
  "$IMAGE" \
  /work/scripts/render-media-pdf.mjs "$input" "$output"
