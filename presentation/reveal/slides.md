# Le développement piloté par les spécifications en pratique

Du code assisté par IA à une livraison logicielle vérifiable.

<div class="hero-meta">
  <span class="pill">Dépôt : specs-driven-development</span>
  <span class="pill">Public : équipes d’ingénierie et responsables techniques</span>
</div>

Note:
Cette présentation ne parle pas de remplacer la discipline d’ingénierie par
l’IA. Elle montre comment des spécifications structurées, des portes explicites
et une validation déterministe permettent d’avancer plus vite sans perdre le
contrôle.

---

<div class="section-label">Contenu</div>

## Programme interactif

Vue d’ensemble cliquable de la présentation.

<div class="agenda-grid">
  <a class="agenda-card" href="#/2">
    <div class="agenda-num">01</div>
    <h3>Qu’est-ce que SDD ?</h3>
    <p>L’idée centrale et son intérêt.</p>
  </a>
  <a class="agenda-card" href="#/4">
    <div class="agenda-num">02</div>
    <h3>Workflow</h3>
    <p>Les sept phases et leurs transmissions.</p>
  </a>
  <a class="agenda-card" href="#/6">
    <div class="agenda-num">03</div>
    <h3>Architecture<br />du contexte</h3>
    <p>Comment règles, skills, agents et artefacts coopèrent.</p>
  </a>
  <a class="agenda-card" href="#/8">
    <div class="agenda-num">04</div>
    <h3>Ingénierie<br />du harness</h3>
    <p>Pourquoi le harness constitue la couche de confiance.</p>
  </a>
  <a class="agenda-card" href="#/11">
    <div class="agenda-num">05</div>
    <h3>Quand<br />l’utiliser</h3>
    <p>Les contextes où ce parcours apporte le plus.</p>
  </a>
  <a class="agenda-card" href="#/13">
    <div class="agenda-num">06</div>
    <h3>Quand ne pas<br />l’utiliser</h3>
    <p>Les cas où un processus plus léger convient mieux.</p>
  </a>
  <a class="agenda-card" href="#/15">
    <div class="agenda-num">07</div>
    <h3>Démonstration</h3>
    <p>Ce qu’il faut montrer en direct.</p>
  </a>
  <a class="agenda-card" href="#/16">
    <div class="agenda-num">08</div>
    <h3>Adoption</h3>
    <p>Comment expérimenter sur une fonctionnalité.</p>
  </a>
</div>

---

<div class="section-label">01 / Fondamentaux</div>

## Qu’est-ce que SDD ?

Le développement piloté par les spécifications guide le travail assisté par IA
avec :

- des exigences approuvées avant l’implémentation ;
- un artefact explicite pour chaque phase ;
- des agents spécialisés aux responsabilités étroites ;
- des portes déterministes avant toute progression du code.

<div class="callout">
  SDD n’est pas une technique pour « mieux prompter ». C’est un système
  d’exploitation léger pour livrer du logiciel avec des preuves.
</div>

Note:
Insister sur le fait que le dépôt traite les spécifications, la conception, les
tâches, la validation et la revue comme des actifs d’ingénierie.

---

## Pourquoi ce framework existe

Les équipes qui utilisent des outils d’IA rencontrent souvent les mêmes échecs :

- l’agent invente les exigences manquantes ;
- le contexte dérive entre les sessions ;
- les tests et validations deviennent inégaux ;
- la revue arrive trop tard ou reste trop superficielle.

<div class="two-col">
  <div>
    <h3>Sans SDD</h3>
    <ul>
      <li>Production rapide</li>
      <li>Faible prévisibilité</li>
      <li>Traçabilité limitée</li>
    </ul>
  </div>
  <div>
    <h3>Avec SDD</h3>
    <ul>
      <li>Production suffisamment rapide</li>
      <li>Confiance renforcée</li>
      <li>Preuves vérifiables</li>
    </ul>
  </div>
</div>

---

<div class="section-label">02 / Workflow</div>

## Le parcours en sept phases

1. Spécifier
2. Relire la spécification
3. Planifier la conception et les tâches
4. Implémenter en TDD
5. Élargir et renforcer les tests
6. Valider avec le harness
7. Effectuer une revue structurée du code

<div class="callout compact">
  Idée clé : chaque phase possède un responsable, un artefact, un contrat
  d’entrée, un contrat de sortie et une porte.
</div>

<div class="slide-ref">Référence : <code>docs/methodology.md</code></div>

---

## Les artefacts forment la colonne vertébrale

Les artefacts sous `.specs/<feature-id>/` relient le workflow de bout en bout.

<div class="artifact-grid">
  <div class="artifact-card"><code>01-spec.md</code><span>Intention et critères</span></div>
  <div class="artifact-card"><code>02-spec-review.md</code><span>Verdict de revue</span></div>
  <div class="artifact-card"><code>03-design.md</code><span>Conception technique</span></div>
  <div class="artifact-card"><code>04-tasks.md</code><span>Tâches adaptées au TDD</span></div>
  <div class="artifact-card"><code>07-validation-report.md</code><span>Résultats des portes</span></div>
  <div class="artifact-card"><code>08-code-review.md</code><span>Verdict avant commit</span></div>
</div>

<div class="slide-ref">Référence : <code>docs/artifact-contract.md</code></div>

---

<div class="section-label">03 / Architecture du contexte</div>

## Architecture du contexte

Ce dépôt ne traite pas tout le contexte comme un prompt géant. Il le sépare :

- règles globales et instructions permanentes ;
- instructions ciblées par fichier ;
- skills spécialisés pour des tâches étroites ;
- agents propres à chaque phase ;
- artefacts produits pendant le workflow.

<div class="callout">
  Objectif : ne charger que le contexte nécessaire, au moment où il est utile.
</div>

---

## Pourquoi cette architecture compte

Une architecture de contexte structurée améliore :

- la précision, avec moins de bruit et de valeurs inventées ;
- la portabilité entre l’application Codex, le CLI et l’extension IDE ;
- la maintenabilité, car le comportement vit dans des fichiers ;
- la gouvernance, avec des actions à risque contraintes par des règles.

<div class="two-col">
  <div>
    <h3>Le dépôt comme source de vérité</h3>
    <p>Méthode, garde-fous et rôles vivent dans le dépôt.</p>
  </div>
  <div>
    <h3>Les artefacts comme mémoire</h3>
    <p>Les specs et rapports conservent l’intention entre les sessions.</p>
  </div>
</div>

---

<div class="section-label">04 / Ingénierie du harness</div>

## Hooks et harness

Les hooks distinguent une narration confiante d’une action autorisée. Ils
répondent immédiatement :

- un test rouge autorise-t-il cette édition ?
- le fichier est-il dans le périmètre ?
- reste-t-il une question ouverte ?
- la commande contourne-t-elle une porte ?

Le harness distingue ensuite une narration confiante d’une preuve globale :

- le code compile-t-il ?
- le comportement a-t-il régressé ?
- l’architecture a-t-elle dérivé ?
- le changement est-il relié aux exigences ?

<div class="callout compact">
  Les hooks protègent chaque geste ; le harness valide l’état final.
</div>

<div class="slide-ref">Référence : <code>docs/harness-principles.md</code></div>

---

## Les dix couches de validation

1. Format et lint
2. Compilation
3. Analyse statique
4. Règles d’architecture
5. Tests unitaires et de tranche
6. Tests d’intégration
7. Couverture
8. Tests de mutation
9. Validation des contrats
10. Analyse de sécurité

<div class="callout">
  Le workflow est fiable non parce que l’agent paraît intelligent, mais parce
  que le dépôt exige des preuves.
</div>

---

## La traçabilité appartient au harness

Le workflow relie :

- critères d’acceptation ;
- tâches ;
- tests ;
- symboles de code ;
- résultats des portes.

Un relecteur peut donc demander :

- à quelle exigence répond ce changement ?
- quels tests le prouvent ?
- quelle porte l’a vérifié ?

---

<div class="section-label">05 / Adéquation</div>

## Quand utiliser ce parcours

Utiliser le workflow lorsque vitesse et fiabilité sont nécessaires :

- fonctionnalités produit de risque moyen à élevé ;
- changements d’API avec contraintes de compatibilité ;
- travaux en plusieurs étapes dont les décisions doivent être vérifiables ;
- équipes adoptant le code assisté par IA avec une gouvernance forte ;
- systèmes brownfield où les régressions coûtent cher.

<div class="callout compact">
  Plus un changement comporte d’ambiguïté, de coordination ou de risque, plus
  SDD est utile.
</div>

---

## Cas d’usage forts

<div class="two-col">
  <div>
    <h3>Très adapté</h3>
    <ul>
      <li>Fonctionnalités backend avec règles métier</li>
      <li>Évolution de schéma ou d’API</li>
      <li>Fonctionnalités auditables</li>
      <li>Collaboration entre équipes</li>
    </ul>
  </div>
  <div>
    <h3>Pourquoi</h3>
    <ul>
      <li>Les questions apparaissent tôt</li>
      <li>Les tâches deviennent petites et testables</li>
      <li>La validation détecte la dérive avant le commit</li>
      <li>La revue s’appuie sur des preuves</li>
    </ul>
  </div>
</div>

---

<div class="section-label">06 / Limites</div>

## Quand ne pas utiliser tout le parcours

Ne pas imposer le workflow complet à chaque minuscule changement :

- correction d’une faute sur une ligne ;
- petite modification documentaire ;
- prototype jetable sans avenir en production ;
- exploration locale ;
- urgence où le confinement immédiat passe d’abord.

<div class="callout warning">
  SDD est un système de livraison, pas une religion. Adapter le processus au
  risque.
</div>

---

## Préférer un parcours plus léger

Pour un changement minuscule et peu risqué :

- édition directe ;
- test ou validation ciblée ;
- revue courte ;
- aucun artefact lourd.

Règle pratique :

- petit changement, faible risque → parcours léger ;
- changement ambigu, durable et partagé → parcours SDD.

---

<div class="section-label">07 / Démonstration</div>

## Parcours de démonstration

Une bonne démonstration montre le contrôle, pas un spectacle de vitesse.

1. Partir d’une demande.
2. Produire `01-spec.md` et exposer les questions ouvertes.
3. Montrer `04-tasks.md` et les fichiers autorisés.
4. Parcourir une tâche du rouge au vert.
5. Montrer les artefacts de validation et de revue.
6. S’arrêter à la limite d’approbation humaine.

Note:
La fin compte. Ne pas brouiller la frontière entre autonomie de l’agent et
approbation humaine : elle fait partie du propos.

---

<div class="section-label">08 / Adoption</div>

## Comment expérimenter

Commencer avec une vraie fonctionnalité, pas un exercice de présentation.

1. Choisir un ticket de complexité moyenne.
2. Exécuter tout le parcours.
3. Mesurer le temps de cycle, la qualité de revue et les défauts échappés.
4. Faire une rétrospective.
5. Garder ce qui améliore le signal et retirer les frictions inutiles.

<div class="callout">
  Objectif : démontrer que la structure augmente la confiance sans tuer l’élan.
</div>

---

## Recommandation finale

Commencer avec :

- une fonctionnalité ;
- un porteur ;
- toute la chaîne d’artefacts ;
- une exécution complète du harness ;
- un verdict de revue explicite.

Si l’expérimentation réduit le travail repris et augmente la confiance,
étendre la méthode.

<div class="hero-meta">
  <span class="pill">La prévisibilité plutôt que les impressions</span>
  <span class="pill">Des preuves avant le commit</span>
</div>
