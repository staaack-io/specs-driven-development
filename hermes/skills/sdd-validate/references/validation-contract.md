# Contrat de validation et de preuves

## Résultats

- Le verdict technique est fermé à `PASS` ou `FAIL`.
- La décision de workflow est fermée à `approve` ou `request-changes`.
- `PASS` et `approve` exigent toutes les gates vertes, une couverture d'au
  moins 95 % et une traçabilité non vide pour chaque validateur.
- Tout résultat absent, inconnu ou non structuré produit `FAIL` et
  `request-changes`.

## Catalogue exécutable S-005

| AC | Preuve exécutable |
|---|---|
| AC-210 | `test_sdd_github_bridge.py::test_admitted_job_creates_and_records_issue_and_draft_pull_request` |
| AC-211 | `test_sdd_github_bridge.py::test_correction_stays_on_branch_replies_to_exact_thread_and_rewaits` |
| AC-212 | `test_sdd_github_bridge.py::test_correction_stays_on_branch_replies_to_exact_thread_and_rewaits` |
| AC-213 | `test_sdd_wave_synthesizer.py::test_t012_t3_only_explicitly_approved_observed_merge_becomes_done` |
| AC-214 | `test_sdd_runtime_guard.py::test_worker_can_only_touch_scope_and_its_task_local_journal` |
| AC-215 | `test_sdd_wave_synthesizer.py::test_t012_t5_only_synthesizer_writes_three_shared_artifacts` |
| AC-216 | `test_sdd_runtime_guard.py::test_crash_before_marker_rolls_back_complete_old_set` |
| AC-217 | `test_sdd_wave_synthesizer.py::test_t012_t8_runtime_recovery_returns_only_complete_old_or_new_set` |

Le test du garde vérifie que chaque fichier et chaque méthode référencés existent.
