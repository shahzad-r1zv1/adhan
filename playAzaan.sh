#!/usr/bin/env bash
if [ $# -lt 1 ]; then
  echo "USAGE: $0 <azaan-audio-path> [<volume>]"
  exit 1
fi

audio_path="$1"
vol=${2:-0}
root_dir=$(dirname "$0")

run_hooks() {
  local hooks_dir="$1"
  local label="$2"
  for hook in "$hooks_dir"/*; do
    [ -e "$hook" ] || continue
    if [ -x "$hook" ]; then
      echo "Running $label hook: $hook"
      "$hook"
    else
      echo "Skipping $label hook (not executable): $hook"
    fi
  done
}

# Run before hooks
run_hooks "$root_dir/before-hooks.d" "before"

# Play Azaan audio, trying players in order of preference. omxplayer is no
# longer available on current Raspberry Pi OS releases (Bullseye+), so fall
# back to other common audio players if it is not installed.
# mpg123/mpv use a 0-100 volume percentage, so convert millibels to a rough
# percentage: 0 mB is full volume.
vol_pct=$(( (vol + 30000) * 100 / 30000 ))
if [ "$vol_pct" -gt 100 ]; then vol_pct=100; fi
if [ "$vol_pct" -lt 0 ]; then vol_pct=0; fi
if command -v omxplayer >/dev/null 2>&1; then
  omxplayer --vol "$vol" -o local "$audio_path"
elif command -v mpg123 >/dev/null 2>&1; then
  mpg123 -q --gain "$vol_pct" "$audio_path"
elif command -v mpv >/dev/null 2>&1; then
  mpv --no-video --volume="$vol_pct" "$audio_path"
elif command -v ffplay >/dev/null 2>&1; then
  ffplay -nodisp -autoexit -loglevel quiet "$audio_path"
elif command -v vlc >/dev/null 2>&1; then
  vlc --intf dummy --play-and-exit "$audio_path"
else
  echo "No supported audio player found (tried omxplayer, mpg123, mpv, ffplay, vlc)." >&2
  echo "Install one of these players, e.g.: sudo apt-get install mpg123" >&2
  exit 1
fi

# Run after hooks
run_hooks "$root_dir/after-hooks.d" "after"
