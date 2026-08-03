---
name: sdd-build
description: Exécuter une tâche SDD prouvée selon le cycle TDD séquentiel.
---

# /sdd-build

Invocation exacte : `/sdd-build <feature-id> <T-NNN>`.

Le garde déterministe `scripts/build_guard.py` valide les deux arguments et le
contrat de tâche avant toute délégation. Il choisit les rôles depuis les preuves
de stack, puis exécute une seule tâche dans l'ordre contractuel.

La façade `run_runtime_task` charge et valide l'état cible, acquiert le lease
exact de la tâche et protège l'empreinte hors scope. Elle journalise chaque
transition avec le runtime v2, applique la porte RED avant GREEN, contrôle les
changements rapportés et libère toujours le lease.

Contrats publiés :

- [délégation](references/delegation-contract.md) ;
- [cycle TDD](references/tdd-cycle-contract.md) ;
- [role-spring-test-engineer.md](references/role-spring-test-engineer.md) ;
- [role-spring-implementer.md](references/role-spring-implementer.md) ;
- [role-react-nextjs-test-engineer.md](references/role-react-nextjs-test-engineer.md) ;
- [role-react-nextjs-implementer.md](references/role-react-nextjs-implementer.md).
