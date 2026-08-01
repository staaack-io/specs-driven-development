# Revue de spécification : 2026-07-31-hermes-parallel-sdd

> Responsable : `spec-author` · Phase 2 · Checklist : `.codex/checklists/spec-review.md`

## Inputs

- Révision de `01-spec.md` : SHA-256 `71fd818b8d9e30931ac5203bd3099ec5ecceb6475461b4d494e72674f640a7b6`, relue le 2026-07-31.
- Source relue : `/Users/cor/.codex/attachments/ba6c1e9c-7bf7-424b-948f-7c887b271ee4/pasted-text.txt`.
- Revue précédente relue : `02-spec-review.md`, verdict `request-changes`, 42 AC en échec et 4 questions nouvelles.
- Sign-off de phase 1 : donné par l'utilisateur le 2026-07-31.
- Go opérationnel pour la future fusion de la pull request #47 : donné par l'utilisateur le 2026-07-31 ; il ne lève aucune autre garde.

## Review Summary

- `verdict`: `approve`
- `acs_total`: `286`
- `acs_failed`: `0`
- `open_questions`: `0`
- `previous_failures_total`: `42`
- `previous_failures_resolved`: `42`
- `new_acs_total`: `44`
- `new_acs_failed`: `0`
- `next_command`: `$epic-plan 2026-07-31-hermes-parallel-sdd`

## Checklist

| Élément | Résultat | Justification |
|---|---|---|
| La source est consignée avec outil, identifiant, URL ou statut ad-hoc et date. | pass | La source ad-hoc, son identifiant, son chemin et sa date de capture figurent aux lignes 7 à 27. |
| L'objectif tient en un paragraphe et décrit un résultat visible. | pass | Le but complet est exprimé en un paragraphe aux lignes 29 à 31. |
| Les non-objectifs sont présents et explicites. | pass | La section couvre les exclusions d'ordonnanceur, d'interface, d'écriture, de fusion, de déploiement et d'exploitation aux lignes 404 à 416. |
| Le glossaire couvre chaque terme métier utilisé dans les AC. | pass | Les termes déterminants ajoutés ou précisés — données sensibles, glob, parité source/profil, gate de validation, pilote réussi et clone propre — sont définis aux lignes 418 à 446. |
| `## Domain Entities and Relationships` est présent. | pass | La section est présente aux lignes 351 à 402. |
| Les entités restent conceptuelles, sans fuite de classes, tables ou bibliothèques. | pass | Les entités décrivent le domaine d'orchestration ; les noms d'outils et d'artefacts cités sont imposés par la source. |
| Les relations précisent leur cardinalité et leur sens métier. | pass | La vague contient `1..*` jobs, le plafond concurrent est séparé en `0..2` jobs écrivains actifs, et les deux extrémités d'une dépendance sont explicitées aux lignes 381 à 402. |
| Chaque AC possède un identifiant stable, complété et croissant. | pass | Les 286 identifiants sont uniques et continus de `AC-001` à `AC-286`, sans trou ni renumérotation des 242 identifiants antérieurs. |
| Chaque AC suit une forme EARS-lite. | pass | Les 286 critères emploient une forme universelle, événementielle, pilotée par l'état ou indésirable. |
| Chaque AC est atomique : une condition et un résultat. | pass | Les 16 critères précédemment composites conservent leur identifiant pour un résultat ; leurs 29 résultats supplémentaires sont séparés dans `AC-243` à `AC-271`. |
| Chaque AC est testable indépendamment. | pass | Les 25 oracles précédemment insuffisants sont mesurables par version, comparaison sans différence, catégories d'expurgation, chemins littéraux, gates nommées ou critères de succès référencés. |
| Aucun AC ne contient de choix d'implémentation inventé. | pass | Les commandes, chemins, outils et paramètres techniques normatifs sont présents dans la source ou dans les réponses utilisateur consignées. |
| Les exigences non fonctionnelles vagues sont mesurables ou deviennent des `Q-NNN`. | pass | Les notions de validation, de réussite du pilote, de redaction, de parité et de propreté possèdent désormais un oracle explicite. |
| Les hypothèses proviennent uniquement de l'utilisateur ou de la source. | pass | Les hypothèses des lignes 448 à 457 sont traçables à la source et aux entrées hors bande. |
| Aucun choix par défaut silencieux n'est introduit. | pass | Ordonnanceur, suivi, capacités, topologie, redaction, chemins admissibles, validation et stratégie de migration sont explicitement sourcés ou résolus. |
| Toutes les `Q-NNN` sont résolues ou différées avec justification. | pass | `Open Questions` indique « aucune » et `Q-001` à `Q-010` sont toutes résolues avec réponse et date. |
| Tous les besoins de la source sont repris ou exclus. | pass | Les interfaces, phases, contraintes VPS, scénarios de test, interdictions, critères de publication et pilote sont représentés. |
| Les informations hors ticket sont consignées sous `Out-of-Band Inputs`. | pass | Le sign-off, le go de la PR #47 et les réponses à `Q-007` à `Q-010` sont consignés aux lignes 459 à 466. |
| Toute bascule visible possède un flag et un retour arrière, ou une dérogation approuvée. | pass | La réponse explicite de l'utilisateur à `Q-007` retient une stratégie de compatibilité à la place d'un flag : double lecture v1/v2, écriture v2, retour au profil précédent et conservation de la lisibilité v1, matérialisés par `AC-276` à `AC-279`. |
| Revue effectuée par l'utilisateur. | pass | L'approbation de phase 1 est consignée à la ligne 510 et la présente passe distincte applique la checklist complète. |
| Le verdict utilise `approve` ou `request-changes`. | pass | Le verdict exact est `approve`. |

## Historical Failure Closure

| Groupe de la revue précédente | Total | Résolus | Preuve |
|---|---:|---:|---|
| AC composites | 16 | 16 | `AC-024`, `AC-084`, `AC-097`, `AC-103`, `AC-112`, `AC-113`, `AC-115`, `AC-126`, `AC-129`, `AC-152`, `AC-168`, `AC-186`, `AC-190`, `AC-194`, `AC-223` et `AC-224` portent chacun un résultat ; `AC-243` à `AC-271` portent les 29 résultats scindés. |
| AC sans oracle objectif | 25 | 25 | `AC-010` à `AC-018`, `AC-035`, `AC-064`, `AC-098`, `AC-109`, `AC-123`, `AC-138`, `AC-139`, `AC-147`, `AC-154`, `AC-158`, `AC-159`, `AC-160`, `AC-167`, `AC-178`, `AC-187` et `AC-232` sont précisés par versions, catégories exhaustives, interdiction de tout glob, comparaison sans différence, gates et critères référencés. |
| Garde de fusion de la PR #47 incomplète | 1 | 1 | `AC-094`, `AC-272` à `AC-275` et `AC-285` exigent respectivement le go, les checks verts, la review reçue, l'absence de fil actionnable, la nouvelle review après correction et la lecture de la review reçue. |
| **Total** | **42** | **42** | Aucun échec historique ne reste ouvert. |

Les quatre questions découvertes lors de la passe précédente sont également fermées :

- `Q-007` : double lecture v1/v2, écriture v2 et rollback compatible v1 dans `AC-276` à `AC-279` ;
- `Q-008` : expurgation exhaustive des cinq catégories dans `AC-035` et le glossaire ;
- `Q-009` : refus de tout glob dans `AC-064`, chemins littéraux relatifs dans `AC-280` et définition du glossaire ;
- `Q-010` : gate de publication décomposée dans `AC-281` à `AC-284` et `AC-286`, et pilote réussi défini par `AC-226` à `AC-230`.

## AC Audit

- AC audités : `286`.
- AC conformes sur la forme EARS-lite : `286`.
- AC atomiques : `286`.
- AC testables indépendamment : `286`.
- AC en échec : `0`.
- Nouveaux AC audités : `44` (`AC-243` à `AC-286`).
- Nouveaux AC conformes : `44`.
- Nouveaux AC en échec : `0`.

Répartition des 44 nouveaux critères :

- `29` résultats issus de la scission des AC composites (`AC-243` à `AC-271`) ;
- `5` gardes complétant le cycle de review de la PR #47 (`AC-272` à `AC-275`, `AC-285`) ;
- `4` critères de bascule et de rollback v1/v2 (`AC-276` à `AC-279`) ;
- `1` critère imposant exclusivement des chemins littéraux relatifs (`AC-280`) ;
- `5` critères définissant la gate de validation de publication (`AC-281` à `AC-284`, `AC-286`).

## Findings

- (aucun)

## New Questions Raised

- (aucune)

## Verdict

- `approve`
- [x] `approve` — passer à `$epic-plan 2026-07-31-hermes-parallel-sdd`
- [ ] `request-changes` — revenir à `$spec 2026-07-31-hermes-parallel-sdd`

Relecteur : `spec-author` (deuxième passe de revue distincte)
Date : 2026-07-31
