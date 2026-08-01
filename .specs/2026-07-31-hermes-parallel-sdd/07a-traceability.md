# Matrice de traçabilité : S-001 — profil 0.4.8

> Responsable : `spring-validator` · Phase 6 · Périmètre primaire : les 36 AC
> affectés à S-001 dans `03a-epic-roadmap.md`.

## Matrix

| AC-ID | Tâche | Preuve principale | État | Portes restantes |
|---|---|---|---|---|
| AC-009, AC-010 | T-001 | contrat onboard, découverte directe 42/42 | local green | CI profil |
| AC-081 à AC-086 | T-002 | workflows présents, tests directs, diff local | partiel | CI, distribution globale, Markdownlint |
| AC-087 à AC-094 | T-003 | historique de la PR source #47 | externe pending | preuve review/fils/go dans l'état SDD |
| AC-095 | T-003 | issue profil #45, future PR distincte | issue créée | créer la PR profil |
| AC-096 | T-001 | copie exacte et parité | green | CI profil |
| AC-097 | T-002 | T-002-T1 + manifeste 0.4.8 | green ciblé | validateur global |
| AC-098, AC-099 | T-001 | disposition 1/1, garde 15/15, contrat 5/5, parité 41 | green | runner/CI global |
| AC-100 | T-003 | blocage de mise à jour VPS | pending | review, autorisation et fusion |
| AC-195 | T-002 | mêmes tests copiés et directs | partiel | exécution dans les deux CI |
| AC-237 | T-002 | deux workflows aux noms stables | inspection | checks GitHub réels |
| AC-250 | T-002 | `git diff --check` | local green | check GitHub |
| AC-251 | T-002 | entrée `0.4.8` du changelog | green ciblé | PR profil |
| AC-272 à AC-275 | T-003 | historique PR #47 | externe pending | preuves consolidées dans T-003 |
| AC-281, AC-282 | T-002 | tests locaux verts | partiel | CI obligatoire verte |
| AC-283, AC-284 | T-003 | review et fils de la future PR profil | pending | `approve`, zéro fil actionnable |
| AC-285 | T-003 | lecture de la review #47 | externe pending | preuve consolidée |
| AC-286 | T-002 | contrat ciblé uniquement | partiel | validateur global et CI |

La réunion des lignes représente exactement : `AC-009`, `AC-010`,
`AC-081` à `AC-100`, `AC-195`, `AC-237`, `AC-250`, `AC-251`, `AC-272` à
`AC-275` et `AC-281` à `AC-286`, soit **36 AC uniques**.

## Coverage check

- AC absent de `04-tasks.md` : **0**.
- AC avec preuve locale ou gate désignée : **36**.
- AC avec toutes les preuves de publication réussies : **incomplet**.
- Tests ajoutés sans T-ID/AC : **0** dans le diff S-001.
- Fichiers source modifiés sans test associé : **0**.

## Test to AC links

- T-001-T1 : AC-098, AC-099 — portabilité de la disposition profil.
- T-001-T2 à T-001-T5 : AC-009, AC-010, AC-095, AC-096, AC-098,
  AC-099 — contrats, garde, parité et non-régression.
- T-002-T1 : AC-097, AC-251 — métadonnées de release.
- T-002-T2 à T-002-T5 : AC-081 à AC-086, AC-195, AC-237, AC-250,
  AC-281, AC-282, AC-286 — distribution et CI.
- T-003-T1 à T-003-T6 : AC-087 à AC-095, AC-100, AC-272 à AC-275,
  AC-283 à AC-285 — gate GitHub et humaine.

## Orphans and gaps

- Aucun code ou test local orphelin détecté.
- **GAP-001 :** l'issue profil
  [#45](https://github.com/staaack-io/hermes-agent-profile-staaack/issues/45)
  existe ; T-003 et ses preuves de PR, CI, review, fils et go restent absents.
- **GAP-002 :** runner global, distribution complète et Markdownlint n'ont pas
  de résultat réussi.

## Verdict

**❌ Traçabilité structurelle complète, traçabilité de preuves incomplète.**

La matrice n'autorise ni la revue formelle phase 7, ni la fusion, ni la mise à
jour du VPS tant que GAP-001 et GAP-002 restent ouverts.
