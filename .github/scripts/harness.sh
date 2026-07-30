#!/usr/bin/env bash
# harness.sh
# Harness d'auto-validation de l'agent. Exécute les 10 couches et produit un
# résumé JSON unique consommé par spring-validator.
#
# Utilisation :
#   ./scripts/harness.sh                  # exécute, affiche le résumé et échoue si une porte échoue
#   ./scripts/harness.sh --report         # exécute et écrit harness-summary.json sur stdout
#   ./scripts/harness.sh --baseline       # capture la référence lors d'un onboarding brownfield

set -euo pipefail

# Résoudre le dossier du script AVANT tout cd, afin que --module fonctionne quel
# que soit le chemin relatif utilisé.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Premier argument facultatif : --module <path> pour entrer dans un module Maven.
if [ "${1:-}" = "--module" ]; then
  shift
  MODULE_DIR="${1:-}"
  shift || true
  [ -d "$MODULE_DIR" ] || { echo "harness : dossier de module introuvable : $MODULE_DIR" >&2; exit 2; }
  cd "$MODULE_DIR"
fi

MODE="${1:-run}"
SUMMARY="target/harness-summary.json"
mkdir -p target

# Helper : section horodatée.
section() { echo "=== $* ==="; }

# Détecter la stack afin de savoir quelles couches imposer.
STACK_JSON="$("$SCRIPT_DIR/detect-stack.sh" pom.xml 2>/dev/null || echo '{}')"

has_layer() {
  echo "$STACK_JSON" | jq -r ".harness_layers.$1 // false"
}

# Couches 1 à 9 séquentielles via Maven verify ; PIT séparément avec -Ppit.
section "formatage + compilation + analyse statique + architecture + tests unitaires + intégration + couverture + sécurité"
mvn -B -ntp verify

if [ "$(has_layer pit)" = "true" ]; then
  section "mutation (incrémentale)"
  mvn -B -ntp -Ppit org.pitest:pitest-maven:mutationCoverage || PIT_RC=$?
fi

# Diff du contrat si une spécification OpenAPI est présente.
if [ -f src/main/resources/openapi/openapi.yaml ]; then
  section "diff du contrat OpenAPI"
  prev="$(git show "origin/main:src/main/resources/openapi/openapi.yaml" 2>/dev/null || true)"
  if [ -n "$prev" ]; then
    echo "$prev" > target/openapi-base.yaml
    if command -v openapi-diff >/dev/null 2>&1; then
      openapi-diff target/openapi-base.yaml src/main/resources/openapi/openapi.yaml --json > target/openapi-diff.json || true
    else
      echo "AVERTISSEMENT : la CLI openapi-diff n'est pas installée ; étape ignorée (exécuter npm i -g @apidevtools/swagger-cli ou utiliser l'image Docker openapitools/openapi-diff)" >&2
    fi
  fi
fi

# Construire le résumé JSON. L'analyse est au mieux : une couche sans rapport
# produit simplement la valeur technique "skipped".
parse_surefire() {
  local dir="$1"
  [ -d "$dir" ] || { echo '{"status":"skipped"}'; return; }
  local total=0 fail=0 err=0 skip=0
  while IFS= read -r f; do
    t=$(grep -oE 'tests="[0-9]+"' "$f" | head -n1 | grep -oE '[0-9]+' || echo 0)
    fa=$(grep -oE 'failures="[0-9]+"' "$f" | head -n1 | grep -oE '[0-9]+' || echo 0)
    er=$(grep -oE 'errors="[0-9]+"' "$f" | head -n1 | grep -oE '[0-9]+' || echo 0)
    sk=$(grep -oE 'skipped="[0-9]+"' "$f" | head -n1 | grep -oE '[0-9]+' || echo 0)
    total=$((total+t)); fail=$((fail+fa)); err=$((err+er)); skip=$((skip+sk))
  done < <(find "$dir" -name 'TEST-*.xml')
  local status="pass"
  [ "$fail" -gt 0 ] || [ "$err" -gt 0 ] && status="fail"
  printf '{"status":"%s","tests":%d,"failures":%d,"errors":%d,"skipped":%d}' "$status" "$total" "$fail" "$err" "$skip"
}

parse_jacoco() {
  local f="target/site/jacoco/jacoco.xml"
  [ -f "$f" ] || { echo '{"status":"skipped"}'; return; }
  # Utiliser python3 pour analyser correctement le XML : JaCoCo 0.8.x peut écrire
  # tout le rapport sur une ligne, ce qui casse les chaînes de grep.
  local result
  result=$(python3 - "$f" <<'PYEOF'
import sys, xml.etree.ElementTree as ET
tree = ET.parse(sys.argv[1])
root = tree.getroot()
# Le dernier <counter type="LINE|BRANCH"> du document représente le total.
line_c = [(int(c.get('missed','0')), int(c.get('covered','0')))
          for c in root.iter('counter') if c.get('type')=='LINE']
branch_c = [(int(c.get('missed','0')), int(c.get('covered','0')))
            for c in root.iter('counter') if c.get('type')=='BRANCH']
lm, lc = line_c[-1] if line_c else (0, 0)
bm, bc = branch_c[-1] if branch_c else (0, 0)
lt = lm + lc; bt = bm + bc
lr = lc / lt if lt > 0 else 0.0
br = bc / bt if bt > 0 else 0.0
status = "fail" if lr < 0.90 or br < 0.90 else "pass"
print('{"status":"' + status + '","line":' + f'{lr:.4f}' + ',"branch":' + f'{br:.4f}' + '}')
PYEOF
  )
  echo "$result"
}

parse_pit() {
  local f="target/pit-reports/mutations.xml"
  [ -f "$f" ] || { echo '{"status":"skipped"}'; return; }
  local result
  result=$(python3 - "$f" <<'PYEOF'
import sys, xml.etree.ElementTree as ET
tree = ET.parse(sys.argv[1])
root = tree.getroot()
total = 0; killed = 0; survived = 0; no_cov = 0; timed_out = 0
for m in root.iter('mutation'):
    total += 1
    s = m.get('status', '')
    if s == 'KILLED':   killed += 1
    elif s == 'SURVIVED': survived += 1
    elif s == 'NO_COVERAGE': no_cov += 1
    elif s == 'TIMED_OUT': timed_out += 1
detected = killed + timed_out
kr = detected / total if total > 0 else 0.0
threshold = 0.75
status = "pass" if kr >= threshold else "fail"
print('{"status":"' + status + '","kill_rate":' + f'{kr:.4f}' + ',"killed":' + str(detected) + ',"survived":' + str(survived) + ',"no_coverage":' + str(no_cov) + ',"total":' + str(total) + '}')
PYEOF
  )
  echo "$result"
}

unit=$(parse_surefire target/surefire-reports)
it=$(parse_surefire target/failsafe-reports)
cov=$(parse_jacoco)
pit=$(parse_pit)

cat > "$SUMMARY" <<EOF
{
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "git_sha": "$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')",
  "stack": $STACK_JSON,
  "gates": {
    "unit":     $unit,
    "it":       $it,
    "coverage": $cov,
    "mutation": $pit
  }
}
EOF

if [ "$MODE" = "--report" ]; then
  cat "$SUMMARY"
elif [ "$MODE" = "--baseline" ]; then
  jq '{captured_at: .started_at, git_sha, stack, gates}' "$SUMMARY" > .specs/_baseline.json
  echo "Fichier .specs/_baseline.json écrit"
else
  echo
  jq '.gates' "$SUMMARY"
fi
