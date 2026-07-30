#!/usr/bin/env bash
# forbid-skip-flags.sh
# Hook Codex PreToolUse pour Bash.
# Bloque toute commande qui désactive le build ou contourne les vérifications.

set -euo pipefail

input="$(cat)"
cmd="$(echo "$input" | jq -r '.tool_input.command // empty')"
[ -z "$cmd" ] && exit 0

# Motif → raison
declare -a patterns=(
  '-DskipTests'           'Exécution refusée avec -DskipTests : les tests sont obligatoires.'
  '-DskipITs'             "Exécution refusée avec -DskipITs : les tests d'intégration sont obligatoires lorsqu'ils existent."
  '-Dpit\.skip'           'Impossible de désactiver les tests de mutation.'
  '-Dcheckstyle\.skip'    'Impossible de désactiver Checkstyle.'
  '-Dspotbugs\.skip'      'Impossible de désactiver SpotBugs.'
  '-Dspotless\.check\.skip' 'Impossible de désactiver Spotless.'
  '-Djacoco\.skip'        'Impossible de désactiver JaCoCo.'
  '--no-verify'           'Impossible de contourner les vérifications Git ou Maven.'
  '-Dmaven\.test\.skip'   'Impossible de sauter entièrement la phase de test.'
  'maven\.test\.failure\.ignore=true' "Impossible d'ignorer les échecs de tests."
)

i=0
while [ $i -lt ${#patterns[@]} ]; do
  pat="${patterns[$i]}"
  reason="${patterns[$((i+1))]}"
  if printf '%s\n' "$cmd" | grep -Eq -- "$pat"; then
    echo "BLOQUÉ : $reason (motif détecté : $pat)" >&2
    echo "Commande : $cmd" >&2
    exit 2
  fi
  i=$((i+2))
done

# Bloquer aussi les opérations Git destructrices sans demande explicite de l'utilisateur.
if printf '%s\n' "$cmd" | grep -Eq -- \
  '(^|[[:space:]])git[[:space:]]+(commit|push|reset[[:space:]]+--hard|clean[[:space:]]+-fd)([[:space:]]|$)'; then
  echo "BLOQUÉ : cet outil ne commit, ne pousse et ne nettoie jamais automatiquement de façon destructive. Demandez à l'utilisateur d'exécuter lui-même la commande." >&2
  exit 2
fi

exit 0
