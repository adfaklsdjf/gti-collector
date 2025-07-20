#!/usr/bin/env bash
set -euo pipefail

# Number of lines to retain in the primary log
KEEP_LINES=100

# Define log files and their corresponding backups
declare -A LOGS=(
  ["app.log"]="backups/app.log"
  ["migrations.log"]="backups/migrations.log"
)

for LOG in "${!LOGS[@]}"; do
  BACKUP="${LOGS[$LOG]}"

  # Skip if log doesn't exist or is empty
  [[ -s "$LOG" ]] || continue

  # Create backup dir if needed
  mkdir -p "$(dirname "$BACKUP")"

  # Count total lines
  TOTAL_LINES=$(wc -l < "$LOG")

  if (( TOTAL_LINES <= KEEP_LINES )); then
    # Nothing to rotate
    continue
  fi

  # Number of lines to extract for backup
  EXTRACT_LINES=$(( TOTAL_LINES - KEEP_LINES ))

  # Extract older lines and append to backup
  head -n "$EXTRACT_LINES" "$LOG" >> "$BACKUP"

  # Retain only the last KEEP_LINES lines
  tail -n "$KEEP_LINES" "$LOG" > "${LOG}.tmp"
  mv "${LOG}.tmp" "$LOG"
done
