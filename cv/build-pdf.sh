#!/usr/bin/env bash
# Regenerate cv/Aida_Farahani.pdf from Aida_Farahani.md (styled, with photo).
set -euo pipefail
cd "$(dirname "$0")"
npx --yes md-to-pdf Aida_Farahani.md
echo "Wrote Aida_Farahani.pdf"
