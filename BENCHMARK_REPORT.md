# BENCHMARK_REPORT — RepoInspector

Date de vérification : 2026-11-14.

## Résultat

RepoInspector est livré sur la branche `feature/initial-implementation` du dépôt public `Thierno-Balde/repoinspector_benchmark`. Le code, les tests, l’exemple et les rapports sont présents. La PR #1 reste volontairement en brouillon : aucune fusion dans `main` n’a été autorisée.

## Fonctionnalités terminées

- Exploration récursive des fichiers source.
- Détection Python (`.py`) et JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`).
- Comptage des lignes totales, code, vides et commentaires en début de ligne.
- Détection des fonctions de plus de 30 lignes en Python et JavaScript.
- Détection heuristique d’imports inutilisés, avec niveau de confiance explicite.
- Détection Python des `except` vides et trop larges.
- Détection de signaux de sécurité simples : `eval`, `exec`, `pickle.loads`, `shell=True`, `innerHTML`, `document.write`, `new Function`.
- Score indicatif sur 100 documenté dans les rapports.
- Export JSON et Markdown.
- CLI `python -m repoinspector --help`, `--path` et `--output`.
- Aucun paquet tiers : bibliothèque standard Python uniquement.

## Commandes exécutées et preuves

| Vérification | Résultat |
|---|---|
| CI initiale sur dépôt privé, run `43579149926` | Refus avant démarrage : problème Actions au niveau du compte |
| Diagnostic après passage public | Les jobs ont démarré ; preuve : run `43581979361` |
| Première exécution avec implémentation | `12 tests`, `1 failure`, `6 errors` ; bug identifié dans le tuple de détection `shell=True` |
| Correction du bug | Commit `f0c4ba2d7c3f44a9c5c46690d4f7f5ee19eef0fc` |
| Suite après correction | Run `43583369612` : `12 tests`, `OK` |
| Audit des faux positifs | Réexport `__all__` et chaîne contenant `eval` corrigés ; test de non-régression ajouté |
| Suite finale | Run `43583671945` : `13 tests`, `OK` |
| Génération des rapports | Run `43583671945` : rapports JSON/Markdown générés puis relus et ajoutés au dépôt |
| CLI | Couvert par les tests : `--help`, sortie JSON/Markdown, chemin inexistant |
| Cas limites | Couvert : dossier vide, chemin inexistant, encodage invalide, dossiers imbriqués et répertoire exclu |

## Tests finaux

- **13 réussis**
- **0 échoué** sur la suite finale.
- Les échecs historiques ont été corrigés ; ils ne sont pas masqués.

## Livrables

- `repoinspector/core.py`
- `repoinspector/__init__.py`
- `repoinspector/__main__.py`
- `tests/test_analyzer.py`
- `tests/test_cli.py`
- `examples/sample_project/`
- `reports/sample_report.json`
- `reports/sample_report.md`
- `reports/self_report.json`
- `reports/self_report.md`
- `README.md`
- `.github/workflows/ci.yml`
- `BENCHMARK_REPORT.md`

## Rapport de l’exemple

Le projet d’exemple contient 4 fichiers : 2 Python et 2 JavaScript. Le rapport réel généré par le runner indique :

- 95 lignes au total ;
- 85 lignes de code ;
- 10 lignes vides ;
- 10 findings ;
- score indicatif : **50/100**.

Les findings incluent imports inutilisés, fonction longue, `eval`, `except` trop permissif et affectation `innerHTML`.

## Auto-audit et corrections

1. Le premier détecteur de sécurité Python parcourait le texte brut et signalait `eval` dans les chaînes de test. Correction : analyse des appels via l’AST, puis test de non-régression.
2. Les réexports de `__init__.py` étaient signalés comme imports inutilisés. Correction : prise en compte de `__all__` et des imports `__future__`.
3. Le workflow initial lançait deux événements et trois versions Python. Correction : un seul événement `pull_request` et un seul job Python 3.12.
4. Le code contient encore trois fonctions internes longues, volontairement signalées par son propre rapport. Elles restent lisibles pour ce benchmark, mais seraient à découper dans un chantier de production.

## Fonctionnalités incomplètes ou limites

- JavaScript analysé par expressions régulières prudentes, sans parser ECMAScript complet.
- Imports inutilisés : heuristique ; réexportations complexes, imports dynamiques et métaprogrammation peuvent produire des faux positifs ou faux négatifs.
- Sécurité : détection de signaux simples uniquement ; ce n’est pas un audit de sécurité.
- Comptage des commentaires : les lignes de commentaire complet sont comptées ; les commentaires inline ne sont pas séparés du code.
- Pas d’analyse des dépendances, de typage, de flux interprocédural ou de qualité d’architecture.
- Le score est indicatif et ne doit pas être comparé entre projets sans garder la même méthode et les mêmes règles.

## Sources techniques consultées

- Python `ast` — documentation officielle : https://docs.python.org/3.11/library/ast.html
- Python `tokenize` — documentation officielle : https://docs.python.org/3.11/library/tokenize.html
- ESLint `no-unused-vars` — documentation officielle : https://eslint.org/docs/latest/rules/no-unused-vars

Ces sources ont confirmé l’usage d’un AST pour la structure Python, l’intérêt du tokenizer pour les commentaires et le caractère non trivial de la détection d’éléments inutilisés en JavaScript. RepoInspector reste volontairement plus petit et plus prudent qu’un linter complet.

## Statut de livraison

Livraison technique vérifiée sur la branche dédiée et par CI GitHub Actions. `main` n’a pas été modifiée et la PR #1 n’a pas été fusionnée.
