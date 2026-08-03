---
name: sdd-build
description: Exécuter une tâche SDD prouvée ou admettre une vague parallèle via Hermes.
---

# /sdd-build

Invocations exactes :

- `/sdd-build <feature-id> <T-NNN>` ;
- `/sdd-build <feature-id> --parallel [--max-workers 1|2]`.

Le garde déterministe `scripts/build_guard.py` valide les deux arguments et le
contrat de tâche avant toute délégation. Il choisit les rôles depuis les preuves
de stack, puis exécute une seule tâche dans l'ordre contractuel.

La façade `run_runtime_task` charge et valide l'état cible, acquiert le lease
exact de la tâche et protège l'empreinte hors scope. Elle journalise chaque
transition avec le runtime v2, applique la porte RED avant GREEN, contrôle les
changements rapportés et libère toujours le lease.

Le chemin parallèle appelle `sdd_build_orchestrator.py` pour une unique passe
d'admission. La valeur VPS par défaut et le plafond sont deux writers. Le
runtime valide le DAG et les dépendances fusionnées, sérialise les scopes en
conflit, crée toutes les cartes compatibles avec un budget de 45 minutes et
deux retries, puis acquiert au plus deux leases. Seul l'adaptateur Kanban Hermes
reçoit les demandes de dispatch ; le garde ne contient aucun second scheduler.

Un échec de dispatch libère uniquement le lease concerné, conserve les autres
jobs actifs et laisse la carte fautive en échec pour diagnostic et retry.

Contrats publiés :

- [délégation](references/delegation-contract.md) ;
- [cycle TDD](references/tdd-cycle-contract.md) ;
- [admission parallèle](../../runtime/build-orchestrator-contract.md) ;
- [role-spring-test-engineer.md](references/role-spring-test-engineer.md) ;
- [role-spring-implementer.md](references/role-spring-implementer.md) ;
- [role-react-nextjs-test-engineer.md](references/role-react-nextjs-test-engineer.md) ;
- [role-react-nextjs-implementer.md](references/role-react-nextjs-implementer.md).
