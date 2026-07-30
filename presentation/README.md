# Présentation

Ce dossier contient les supports de présentation du dépôt.

## Fichiers

- `sdd-repo-talk.md` : version Markdown compatible avec Marp ;
- `reveal/index.html` : point d’entrée Reveal.js ;
- `reveal/slides.md` : contenu des diapositives Reveal.js ;
- `reveal/theme.css` : petites adaptations visuelles.

## Workflow recommandé

1. Modifier `reveal/slides.md` pour une présentation Reveal.js.
2. Ouvrir `reveal/index.html` depuis un serveur web local.
3. Utiliser `sdd-repo-talk.md` uniquement pour un export Marp vers PDF ou
   PowerPoint.

## Exécuter Reveal.js en local

Depuis la racine du dépôt :

```bash
python3 -m http.server 8000
```

Ouvrir ensuite
`http://localhost:8000/presentation/reveal/index.html`.

Utiliser les flèches du clavier pour naviguer.

## Durée conseillée

- 20 à 25 minutes au total ;
- 8 à 10 minutes de démonstration ;
- 3 à 5 minutes de questions.

## Sources utilisées

- `docs/methodology.md`
- `docs/harness-principles.md`
- `docs/artifact-contract.md`
- `docs/spec-format.md`
- `README.md`
