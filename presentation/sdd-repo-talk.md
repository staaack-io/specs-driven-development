---
marp: true
title: Le développement piloté par les spécifications en pratique
paginate: true
size: 16:9
---

# Le développement piloté par les spécifications en pratique

Du code assisté par IA à une livraison logicielle vérifiable.

- Dépôt : specs-driven-development
- Public : équipes d’ingénierie et responsables techniques

---

# Pourquoi ce framework existe

L’IA produit rapidement du code, mais les équipes rencontrent encore :

- des résultats incohérents ;
- des suppositions qui dérivent ;
- une traçabilité faible ;
- des contrôles de qualité inégaux.

Ce dépôt répond à ces écarts avec un workflow structuré en phases.

---

# Idée centrale

Un modèle de livraison déterministe :

- responsabilité explicite par phase ;
- artefacts stables à chaque étape ;
- TDD imposé pendant l’implémentation ;
- validation et revue avant le commit.

Résultat : itérer plus vite sans sacrifier la fiabilité.

---

# Vue d’ensemble du workflow

1. Spécifier
2. Relire la spécification
3. Planifier la conception et les tâches
4. Implémenter en TDD
5. Élargir les tests
6. Valider
7. Relire le code

Référence : `docs/methodology.md`

---

# Contrat des artefacts

Chaque phase produit un artefact concret sous `.specs/<feature-id>/`.

Exemples :

- `01-spec.md`
- `03-design.md`
- `04-tasks.md`
- `07-validation-report.md`
- `08-code-review.md`

Référence : `docs/artifact-contract.md`

---

# Rôles des agents

Des rôles spécialisés améliorent la concentration et la responsabilité :

- auteur de spécification ;
- architecte ;
- ingénieur de test ;
- agent d’implémentation ;
- agent de validation ;
- agent de revue.

Chaque rôle possède ses contraintes et règles de transmission.

---

# Garde-fous importants

Règles non négociables :

- aucune valeur par défaut silencieuse ;
- discipline rouge → vert → refactorisation ;
- aucune option contournant les contrôles ;
- aucune modification du code pendant validation ou revue ;
- décision humaine pour les actions à risque.

---

# Hooks et harness

Les hooks protègent chaque action : état TDD, périmètre, questions ouvertes et
commandes interdites.

Le harness valide ensuite l’ensemble :

- format et lint ;
- compilation et analyse statique ;
- architecture ;
- tests unitaires et d’intégration ;
- couverture et mutations ;
- contrats d’API ;
- sécurité.

Référence : `docs/harness-principles.md`

---

# Traçabilité

Le dépôt relie :

- critères d’acceptation ;
- tâches ;
- tests ;
- modifications du code ;
- résultats de validation.

Résultat : moins d’ambiguïté, des audits plus faciles et des livraisons plus
sûres.

---

# Démonstration en 8 à 10 minutes

1. Partir d’une demande de fonctionnalité.
2. Produire `01-spec.md` avec ses questions ouvertes.
3. Montrer le découpage dans `04-tasks.md`.
4. Parcourir rouge puis vert sur une tâche.
5. Montrer les artefacts de validation et de revue.
6. Terminer sur la décision humaine explicite.

---

# Plan d’adoption

Commencer petit :

1. Choisir une fonctionnalité moyenne.
2. Exécuter tout le workflow.
3. Mesurer le temps de cycle et les défauts.
4. Faire une rétrospective et ajuster les conventions.

---

# Risques et réponses

Préoccupations fréquentes :

- « Cela semble plus lent. »
- « Il y a trop de processus. »
- « C’est difficile en brownfield. »

Réponses :

- expérimenter sur une fonctionnalité ;
- établir une référence puis relever progressivement les seuils ;
- garder les artefacts concis et utiles.

---

# Appel à l’action

Mener une expérimentation sur un sprint :

- une fonctionnalité ;
- un responsable ;
- toutes les phases ;
- une revue fondée sur des preuves.

Si l’expérimentation réduit le travail repris et renforce la confiance,
généraliser l’approche.
