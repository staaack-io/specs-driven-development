# Contrat du synthesizer de vague SDD

Le synthesizer observe les gates ; il ne demande aucune review et n'effectue
aucune fusion. Une PR techniquement prête peut seulement placer sa carte en
`awaiting_go`. Le go est une donnée humaine explicite. La carte devient `done`
uniquement après observation indépendante de la fusion déjà réalisée.

## Fan-in transactionnel

Toutes les cartes de la vague doivent être `done` et chaque journal task-local
doit passer `verify_job_journal`. L'acteur unique `synthesizer` transmet ensuite
exactement `04-tasks.md`, `.tdd-state.json` et `05-implementation-log.md` à
`transactional_fan_in` avec leurs tokens CAS.

Le runtime garantit qu'une interruption avant le marqueur restaure l'ancien
ensemble complet et qu'une interruption après le marqueur restaure le nouvel
ensemble complet. Aucun worker n'obtient une référence d'écriture vers ces
artefacts.

## PR et barrière de vague

Une unique PR brouillon de fan-in est créée par clé idempotente. Le synthesizer
n'expose aucun appel de fusion. La vague suivante reste inadmissible jusqu'à
observation de la fusion humaine de cette PR.
