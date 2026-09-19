# Roadmap de Linediff

> Diagnostic initial du dépôt local au 19 septembre 2026; les constats ci-dessous conservent l'état de départ. Les cases et les notes de progression plus bas décrivent les travaux et vérifications effectués depuis cet audit. Les tags locaux `v0.1.2` et `v0.1.3` existaient déjà au départ; les preuves distantes sont consignées séparément.

## Diagnostic et cap produit

Linediff est aujourd'hui une CLI Python qui compare deux fichiers texte en trois présentations (`unified`, `side-by-side`, `inline`) et propose `--check-only`, une entrée stdin à séparateur maison et une interface à sept arguments prévue pour `git diff --ext-diff`. Le dépôt contient des exemples, sept modules de tests, une CI Linux, de la documentation et un script de publication. Le cas d'usage prometteur est une **revue de changements de code locale, lisible dans le terminal et utilisable avec Git**. Sa différenciation annoncée, le diff syntaxique, doit encore être démontrée par le produit.

### Constats vérifiés dans le dépôt

| Priorité | Constat et preuve locale | Conséquence |
| --- | --- | --- |
| P0 | `src/linediff/diff.py` relie le départ aux sommets droits et les sommets gauches à la fin, sans chemin des sommets droits vers la fin. Sur un arbre minimal, `dijkstra_shortest_path` renvoie `[]`; `compute_diff` utilise alors `difflib.unified_diff`. | La promesse de diff structurel de `README.md` et `docs/` n'est pas réalisée par ce moteur. |
| P0 | `compute_diff('a', 'a\n')` renvoie `[]`; la CLI et `--check-only` traitent aussi ces fichiers comme identiques. | Perte d'une différence réelle, grave pour un outil de comparaison et un contrôle CI. |
| P0 | `--language` ne passe pas au parseur : il est transmis seulement aux fonctions de formatage qui ne l'utilisent pas. Le parseur charge les huit grammaires dans un unique `try`, puis tente `parser.set_language(...)`; ses dépendances sont ouvertes à toute version `>=0.20`. | L'override et l'installation partielle des grammaires ne sont pas fiables; la compatibilité Tree-sitter n'est pas établie. |
| P0 | `README.md` et `docs/usage.md` proposent `git diff \| linediff`; une entrée de vrai diff Git échoue car la CLI attend une ligne seule `---`. | Parcours d'adoption Git cassé; l'entrée maison peut aussi perdre les sauts de ligne. |
| P0 | `--check-only` renvoie `1` pour « différent », mais aussi pour un fichier absent ou non UTF-8. `read_file_content` ne gère que deux erreurs de lecture. | Une automatisation ne peut pas distinguer un écart d'une erreur; certaines entrées peuvent produire une traceback. |
| P1 | Les tests vérifient surtout qu'une chaîne apparaît ou qu'une commande ne plante pas; `tests/test_languages.py` accepte 29 noms sans tester de parseur. La CI installe `.[dev]` sans extra Tree-sitter, n'exécute ni mypy ni Black, rend une passe flake8 non bloquante et ne teste que Linux 3.8–3.11. | Les promesses de structure, de portabilité et de qualité ne sont pas protégées par les gates. |
| P1 | `README.md`, `docs/index.md` et `docs/faq.md` revendiquent vitesse, mémoire, cache et avantages syntaxiques sans mesure fournie; `docs/api.md` indique encore 0.1.0, `docs/index.md` pointe vers un `docs/changelog.md` absent. Aucune capture ou vidéo n'est suivie dans le dépôt. | La présentation est abondante mais moins crédible et moins rapide à évaluer qu'une preuve courte et reproductible. |
| P1 | `scripts/release-kit.sh` modifie version et changelog avant son contrôle Git, modifie ces fichiers même avec `--dry-run`, peut poursuivre avec des changements locaux, publie sur PyPI avant le commit/tag/push et autorise `--skip-tests`/`--skip-check`. Les tags locaux ne prouvent pas la disponibilité d'artefacts. | La publication est fragile et difficile à reproduire ou à auditer. |
| P2 | `requirements.txt` contient des dépendances Markdown sans rapport clair avec la CLI; `pyproject.toml` annonce `py.typed`, absent de `src/linediff/`. La documentation a plusieurs URL d'hébergement, mais aucune configuration de génération de site n'est présente. | Installation, typage et documentation publiée restent ambigus. |

Vérifications faites pour cet audit : exécution locale de la CLI sur `data/`, inspection du graphe minimal, comparaison de fichiers différant seulement par le saut de ligne final, essai de l'entrée `git diff` et lecture des fichiers suivis par Git. L'environnement courant dispose de Python 3.14.6, sans `pytest`, `tree_sitter`, `build` ni `twine` : **la suite de tests, l'installation avec grammaires et le build n'ont pas été validés**. Les statuts distants, le packaging publié, les téléchargements, les étoiles et les performances comparées ne sont pas déduits des badges ou des liens.

### Positionnement à trancher avant d'élargir le périmètre

Le dépôt se compare lui-même à `git diff`, mais n'apporte actuellement aucune preuve reproductible d'un meilleur résultat. Viser d'abord une promesse étroite : **rendre les changements dans des fonctions Python plus faciles à comprendre que le diff ligne seul, tout en conservant un diff exact et exploitable**. Garder les autres langages en mode texte jusqu'à validation réelle de chaque grammaire. Une matrice concurrentielle future devra comparer, sur les mêmes fichiers et versions archivés, `git diff`, un outil de diff syntaxique et une visionneuse de diff; ne publier que des différences observées, leurs compromis et les limites de Linediff. Les étoiles sont un résultat possible de l'utilité et de la confiance, pas un critère de livraison.

## Règles de progression

- **P0 bloque la publication** : exactitude, vérité de la promesse, comportement CLI/Git et gate de tests. P1 rend le projet attractif et facile à adopter. P2 améliore la maintenance et le partage une fois le cœur prouvé.
- Chaque phase se termine avec les critères de ses tâches **observés sur le code et des artefacts réels**; noter `passé`, `non vérifié` et `bloqué` séparément. Un tag, un badge ou un build local ne prouve ni mise en ligne ni fonctionnement chez l'utilisateur.
- Conserver le diff ligne comme référence d'exactitude. Toute sortie annoncée comme patch unifié doit conserver les octets pertinents et réussir une application de patch; les annotations structurelles qui ne sont pas compatibles avec un patch doivent être clairement séparées.
- Ne publier aucune performance, compatibilité, URL de documentation, release ou comparaison externe avant contrôle correspondant. Ne lancer **la phase vidéo qu'après validation de toutes les autres phases**.

## Phase 0 — Contrat et base de preuve (P0)

### 0.1 Définir les modes et les garanties du produit

- [x] **Terminé localement (19 septembre 2026).** Contrat cible et limites actuelles dans `docs/PRODUCT.md`, plan de tests dans `tests/TEST_PLAN.md`. Les trois scénarios ont été comparés au moteur actuel et à `difflib` : la baseline est bien un diff ligne. Le comportement cible reste à implémenter dans les phases suivantes.

- **Objectif :** choisir une proposition de valeur réalisable et un contrat que tests, CLI et documentation partagent.
- **Changements :** écrire des spécifications courtes pour la comparaison de fichiers, le mode syntaxique Python, le fallback texte, le format unifié, `--check-only`, l'entrée stdin et le cas Git; établir explicitement ce qui est *différenciation*, *préservation exacte* et *simple affichage*; décider si l'entrée de diff unifié depuis stdin sera réellement supportée ou retirée des exemples.
- **Fichiers :** nouveau `docs/PRODUCT.md`, `docs/usage.md`, `README.md`, plan de tests dans `tests/`.
- **Acceptation :** tableau des modes et des codes de sortie non ambigu; trois scénarios avant/après où l'information structurelle souhaitée est indiquée; limites par langage annoncées; une phrase de valeur utilisable telle quelle dans le README.
- **Validation :** revue des scénarios contre la CLI actuelle et contre un diff ligne de référence; aucun résultat hypothétique présenté comme livré.
- **Dépendances / risques :** point de départ de toutes les phases; réduire la liste de langages annoncés peut paraître régressif, mais évite une promesse trompeuse.

### 0.2 Constituer le corpus de référence et une mesure initiale

- [x] **Terminé localement (19 septembre 2026).** Quinze paires et leurs tailles/règles/sorties baseline figurent dans `tests/fixtures/`; `scripts/benchmark.py` imprime des mesures reproductibles sans modifier le dépôt; résultats et limites dans `docs/BASELINE.md`. Les erreurs de saut de ligne final et CRLF sont conservées comme preuves de départ.

- **Objectif :** disposer d'exemples vérifiables avant de changer l'algorithme.
- **Changements :** figer des paires de fichiers et des résultats attendus pour ajout, suppression, modification, déplacement de fonction, changement de paramètre, reformatage, répétitions, Unicode, absence de saut de ligne final, fichier vide, fichier binaire et gros fichier; séparer exemples d'acceptation et benchmarks.
- **Fichiers :** `data/`, nouveaux `tests/fixtures/` et `benchmarks/` ou `scripts/benchmark.py`, `docs/PRODUCT.md`.
- **Acceptation :** chaque cas a entrée, sortie attendue, règle vérifiée et taille documentées; mesures baseline reproductibles avec versions d'outils, machine et commande.
- **Validation :** exécuter les fixtures sur le code actuel, conserver les échecs attendus comme preuve de départ; vérifier que les benchmarks ne modifient pas le dépôt.
- **Dépendances / risques :** suit 0.1; éviter d'optimiser seulement pour les exemples choisis.

## Phase 1 — Exactitude du diff et du contrat CLI (P0)

### 1.1 Réparer la comparaison fidèle des textes

- [x] **Terminé et vérifié (19 septembre 2026).** Les fixtures texte distinguent fins de ligne et saut final; `git apply` reconstruit exactement les fichiers de sortie. La matrice GitHub Actions des runs `35442699106` et `35442835093` a réussi sur Linux, macOS et Windows avec Python 3.8–3.14.

- **Objectif :** ne jamais déclarer identiques deux fichiers dont le contenu diffère.
- **Changements :** remplacer l'usage de `splitlines()` qui efface l'information de fin de ligne, représenter correctement `\n`, `\r\n` et l'absence de saut final; définir le comportement des fichiers vides, lignes répétées et contenus Unicode; produire des hunks et en-têtes de diff unifié corrects sans les dupliquer.
- **Fichiers :** `src/linediff/diff.py`, `src/linediff/__main__.py`, `tests/test_unit_diff.py`, nouvelles fixtures de phase 0.
- **Acceptation :** `a` et `a\n` sont différents, `--check-only` renvoie « différent »; une sortie unifiée est interprétable et applicable aux cas texte du corpus; mêmes octets en entrée donnent « identique ».
- **Validation :** tests de propriétés sur paires de fichiers, comparaison avec une référence ligne et application de patch en dossier temporaire, tests de fins de ligne sous Linux/macOS/Windows.
- **Dépendances / risques :** dépend du contrat 0.1; une sortie plus fidèle peut modifier les instantanés et exemples existants.

### 1.2 Rendre les entrées et les codes de sortie fiables

- [x] **Terminé localement (19 septembre 2026).** Codes `0/1/2` testés sur identique/différent/erreur, stdin à séparateur préservant les fins de ligne, erreurs de fichiers/binaires/UTF-8 sans traceback, noms commençant par `-`, pipe fermé, exemples `git diff | linediff` retirés. La suite locale et un script `set -e` sur les trois issues passent.

- **Objectif :** permettre un usage sûr en shell et en CI.
- **Changements :** distinguer code `0` identique, `1` différent et `2` erreur en mode de contrôle; spécifier le code du mode d'affichage; attraper permissions, répertoires, I/O, Unicode et pipe fermé sans traceback; router diagnostics vers stderr; corriger ou supprimer `git diff | linediff` et le séparateur maison; prendre en charge les noms contenant espaces et tirets.
- **Fichiers :** `src/linediff/__main__.py`, `tests/test_cli.py`, `tests/test_error_handling.py`, `README.md`, `docs/usage.md`.
- **Acceptation :** aucun exemple documenté ne plante; les trois issues de `--check-only` sont distinctes et stables; erreurs lisibles, sans sortie diff partielle sur stdout.
- **Validation :** tests subprocess sur fichiers valides/absents/non UTF-8/répertoire, stdin réel, pipe, noms spéciaux et codes de retour; scripts shell CI avec `set -e`.
- **Dépendances / risques :** dépend de 1.1; changement de code de sortie à documenter comme compatibilité CLI.

### 1.3 Prouver l'intégration Git avant de la recommander

- [x] **Terminé et vérifié (19 septembre 2026).** Un vrai dépôt temporaire couvre modification, création, suppression, renommage à neuf arguments, binaire, fichier avec espaces et retour à `git diff --no-ext-diff`. La commande du README a été exécutée avec le binaire installé dans un environnement isolé. Les mêmes tests passent dans les runs GitHub Actions `35442699106` et `35442835093` sur Linux, macOS et Windows; un filtre Git de fins de ligne peut encore modifier les octets des opérandes pour un changement ordinaire, limite documentée.

- **Objectif :** fournir un parcours Git fiable, limité et réversible.
- **Changements :** tester réellement les protocoles à sept et neuf arguments de `git diff --ext-diff`; traiter création, suppression, renommage, fichiers temporaires et binaires; choisir une commande d'activation locale au dépôt et de désactivation; retirer la recommandation de configuration globale tant que tous les cas ne passent pas.
- **Fichiers :** `src/linediff/__main__.py`, nouveaux `tests/test_git_integration.py`, `README.md`, `docs/usage.md`.
- **Acceptation :** un dépôt temporaire Git produit un diff correct sur les cas annoncés; l'exemple copié depuis le README fonctionne et la désactivation restaure le comportement initial.
- **Validation :** tests d'intégration avec vrai `git diff --ext-diff` sur Linux, macOS et Windows ou déclarer les plateformes non vérifiées; comparaison avec `git diff --no-ext-diff`.
- **Dépendances / risques :** dépend de 1.1–1.2; les conventions de Git pour fichiers absents et binaires demandent un traitement explicite.

## Phase 2 — Diff syntaxique réel et architecture (P0)

### 2.1 Remplacer ou corriger le moteur structurel, avec preuve de valeur

- [x] **Terminé localement sur macOS arm64 (19 septembre 2026).** La nouvelle vue `--display structural` utilise l'AST Python pour identifier déplacement de fonction, changement de signature/corps et modification de méthode; elle annexe le diff texte exact en le marquant non patchable. Les tests d'oracle couvrent les trois scénarios, la provenance des lignes, un reformatage sans faux changement et l'indépendance de l'analyse structurelle vis-à-vis de `difflib`. Le graphe expérimental reste à retirer lors de 2.3; Tree-sitter et les autres langues relèvent de 2.2.

- **Objectif :** produire au moins un bénéfice syntaxique observable sur de vrais changements Python.
- **Changements :** supprimer le chemin de graphe mort ou le rendre complet avec un algorithme documenté; choisir des unités AST stables (fonction, classe, bloc) avec positions source; aligner les changements sans perdre les lignes; identifier un déplacement de fonction et un changement local dans son contexte; séparer le signal structurel des hunks patchables.
- **Fichiers :** `src/linediff/diff.py`, éventuellement nouveaux modules `model.py`/`structural.py`, `tests/test_diff_engine.py`, fixtures Python.
- **Acceptation :** au moins les trois cas définis en 0.1 montrent une information vérifiable absente du simple diff ligne; aucun changement n'est supprimé; mode texte exact en fallback; le moteur n'emprunte plus systématiquement `difflib` sur les cas pris en charge.
- **Validation :** tests d'oracle pour additions/suppressions/déplacements/répétitions, invariants de conservation du contenu et revue manuelle du résultat face au diff ligne.
- **Dépendances / risques :** dépend de la phase 1; l'alignement de mouvements peut être ambigu, donc expliciter les heuristiques et leurs faux positifs.

### 2.2 Fiabiliser Tree-sitter et les langues annoncées

- [x] **Terminé localement sur macOS arm64/Python 3.14.6; autres plateformes et versions non vérifiées.** Chargement indépendant des huit grammaires avec versions figées, extra Python seul, offsets UTF-8 corrigés et fallback explicite. Trois installations isolées (base, Python seul, extra complet), les tests de capacités et la suite complète avec extra complet passent; `--language python` sélectionne la vue Python sur un `.txt`. `docs/PARSER_SUPPORT.md` distingue grammaire disponible et diff structurel réellement livré.

- **Objectif :** faire correspondre l'installation, la détection et le support effectif.
- **Changements :** isoler l'import de chaque grammaire, choisir et tester une plage de versions Tree-sitter compatible avec l'API utilisée, corriger les offsets en octets UTF-8 et la gestion des arbres avec erreurs; passer `--language` au parseur; n'activer dans l'interface que les langues dont le rendu syntaxique a un oracle réel; conserver explicitement le fallback texte pour les autres.
- **Fichiers :** `src/linediff/parser.py`, `src/linediff/__main__.py`, `pyproject.toml`, `tests/test_parser.py`, `tests/test_languages.py`.
- **Acceptation :** installation sans grammaire, avec Python seul et avec l'extra complet toutes testées; langue forcée modifie effectivement le parseur; Unicode n'altère pas les plages source; table de support basée sur des tests par langue.
- **Validation :** matrice d'installation isolée avec versions épinglées et testées, fixtures non ASCII et syntaxe invalide, assertion du parseur réellement choisi plutôt qu'une simple sortie non vide.
- **Dépendances / risques :** dépend de 2.1; les roues natives des grammaires varient selon Python/OS/architecture; préférer réduire le périmètre plutôt que simuler le support.

### 2.3 Clarifier l'API et les limites de l'algorithme

- [x] **Terminé localement sur macOS arm64 (19 septembre 2026).** Graphe/Dijkstra inatteignables retirés; LCS conservé pour l'alignement des définitions; positions des atomes uniformisées en offsets UTF-8; API documentée. Lecture, détection, calcul, analyse et rendu sont séparés. `--diagnostics` montre la route effective et le motif du fallback sur stderr, sans modifier le diff sur stdout. Suite complète verte; validation multiplateforme encore couverte par 4.2.

- **Objectif :** rendre le cœur testable, maintenable et documentable.
- **Changements :** séparer lecture, détection, parse, calcul et rendu; retirer le LCS et les structures non utilisés ou les intégrer avec tests; définir un modèle de changement avec provenance et plages; formaliser les conditions du fallback et ses raisons sans imprimer de warning sur stdout.
- **Fichiers :** `src/linediff/`, `docs/api.md`, tests unitaires dédiés.
- **Acceptation :** chaque fonction publique a un contrat de sortie clair; le chemin choisi peut être observé en diagnostic sans polluer le diff; les données structurelles ne sont pas confondues avec des lignes préfixées `+`/`-`.
- **Validation :** tests de contrat API et revue de couverture des branches de parsing, fallback et rendu.
- **Dépendances / risques :** suit 2.1–2.2; refonte interne à garder compatible avec la CLI documentée.

## Phase 3 — Robustesse et expérience terminal (P1, avec risques P0)

### 3.1 Maîtriser performance et entrées adverses

- [x] **Terminé pour le corpus borné (19 septembre 2026).** Limites de 4 MiB/20 000 lignes/200 000 caractères, seuil d'alignement de 8 millions de paires avec patch complet applicable, repli structurel à 1 MiB/500 définitions; tests d'entrées volumineuses et `git apply` verts. Le benchmark CI `35444327149` a mesuré les cinq cas sur trois OS; résultats dans `docs/LIMITS.md`. La barrière à 500 ms de médiane CLI et 64 MiB de RSS maximal du processus de calcul, avec timeout de 15 secondes, a réussi dans le run CI `35445031559`. Un seuil volontairement trop bas a échoué localement pour chaque cas. Ces budgets ne promettent rien sur toute entrée acceptée.

- **Objectif :** éviter une explosion de mémoire ou une sortie inutilisable sur des fichiers réels.
- **Changements :** borner taille/complexité avant la construction de graphes quadratiques, traiter gros fichiers, longues lignes, profondeur AST, fichiers binaires et répertoires; définir budgets de temps/mémoire et chemin de repli; limiter les allocations et la récursion non bornée.
- **Fichiers :** `src/linediff/diff.py`, `src/linediff/parser.py`, `src/linediff/__main__.py`, benchmarks et `tests/test_edge_cases.py`.
- **Acceptation :** corpus de tailles défini en phase 0 terminé sous budgets documentés, sans OOM ni traceback; cas refusés ou dégradés signalés clairement; aucune affirmation chiffrée sans résultats reproductibles.
- **Validation :** benchmarks répétés avec médiane et RSS, timeouts en CI, tests de gros fichiers/répétitions/Unicode/binaire et contrôle des sorties.
- **Dépendances / risques :** dépend de la phase 2; les budgets doivent être ajustés par OS et type de fichier, sans sacrifier l'exactitude.

### 3.2 Donner une vraie UX de lecture des changements

- [x] **Terminé et vérifié localement et en CI (19 septembre 2026).** Couleur `auto/always/never`, respect de `NO_COLOR` en mode auto, largeur terminal/`--width`, colonnes avec numéros de lignes, troncature visible et sommaire sont implémentés. Tests 80/120 colonnes, Unicode large, redirection et caractères de contrôle passent. Les trois modes ont été capturés par un vrai PTY sur les fixtures `data/move_*.py`, rendus en SVG clair/sombre et inspectés visuellement dans Chrome; la vue principale a aussi été inspectée à 390 px. Les fixtures de capture restent LF sur Windows et `tests/test_capture.py` passe sur les trois OS dans le run `35445031559`. Le texte mobile reste petit mais vectoriel et zoomable.

- **Objectif :** rendre le résultat scannable dans un terminal ordinaire et dans un README.
- **Changements :** couleur `auto/always/never` selon TTY et `NO_COLOR`, entêtes et statuts cohérents, largeur terminal mesurée, troncature ou retour à la ligne contrôlé, colonnes alignées pour ajouts/suppressions, positions de lignes, signal de déplacement et sommaire; éviter les codes ANSI dans fichiers redirigés.
- **Fichiers :** fonctions `format_*` de `src/linediff/__main__.py` ou nouveau `render.py`, tests CLI, exemples `data/`.
- **Acceptation :** sorties lisibles à 80 et 120 colonnes, sur fond clair et sombre; aucun débordement silencieux ou séquence ANSI sur sortie non TTY; code couleur jamais seul porteur du sens.
- **Validation :** captures de vrais terminaux, tests de largeur et d'absence d'ANSI, revue manuelle des trois modes sur plusieurs fixtures.
- **Dépendances / risques :** suit 1.1 et 2.3; le style doit rester sobre et compatible avec accessibilité et lecteurs de logs.

### 3.3 Offrir un démarrage démontrable en une minute

- [x] **Terminé localement sur macOS arm64 (19 septembre 2026).** `docs/QUICKSTART.md` utilise les fixtures réelles et une installation locale dans un venv neuf; `--help`, vue structurelle et colonnes ont été exécutés depuis ce venv. `tests/test_quickstart.py` compare l'exemple documenté à la sortie réelle. Le parcours Windows reste soumis à la matrice de 4.2.

- **Objectif :** permettre de constater la valeur sans configuration globale de Git.
- **Changements :** ajouter une commande ou un jeu d'exemples reproductibles inclus dans le dépôt, une sortie attendue maintenue par tests et un parcours « installer → comparer → comprendre le résultat → intégrer localement à Git »; ne pas fabriquer d'écrans ni de résultats.
- **Fichiers :** `README.md`, `data/`, `docs/examples.md`, éventuellement `scripts/demo.sh`, tests de smoke.
- **Acceptation :** un nouvel utilisateur peut suivre le parcours depuis un environnement propre, comparer deux fichiers fournis et reproduire l'exemple structurel annoncé en moins de cinq minutes.
- **Validation :** exécution du parcours exact en environnement vierge et revue de chaque sortie/capture issue de cette exécution.
- **Dépendances / risques :** attend 2.1 et 3.2; ne pas figer une démo d'une fonctionnalité non livrée.

## Phase 4 — Vérification et sécurité de livraison (P0/P1)

### 4.1 Transformer la suite en garde-fou d'exactitude (P0)

- [x] **Terminé pour les branches critiques ciblées (19 septembre 2026).** Assertions permissives remplacées par oracles ciblés; les tests normaux utilisent le paquet installé sans `PYTHONPATH` manuel. Quatre mutations isolées (saut final, code de sortie, langue forcée, route structurelle) sont toutes détectées. Une mesure locale `coverage.py 7.16.1` qui agrège les sous-processus donne 87 % global, 94 % pour `diff.py` et `inputs.py`, 77 % pour `__main__.py`; méthode et limites dans `docs/QUALITY.md`. La suite complète locale et le nouveau gate de mutations CI Linux ont réussi dans le run `35445154639`, avec les profils de grammaires sur les trois OS. Cette mesure n'est pas une garantie d'absence de défaut.

- **Objectif :** empêcher qu'une CI verte masque la perte de données ou l'absence de diff syntaxique.
- **Changements :** remplacer les assertions permissives (`code in [0,1]`, sortie simplement non vide) par des oracles précis; séparer tests unitaires, CLI, Git réel, parseurs optionnels et packaging; mesurer la couverture des branches critiques plutôt que viser un pourcentage global seul.
- **Fichiers :** `tests/`, `pyproject.toml`, fixtures de la phase 0.
- **Acceptation :** un défaut injecté sur saut de ligne final, code de sortie, détection de langue ou chemin syntaxique fait échouer une assertion dédiée; les tests ne dépendent pas de `PYTHONPATH` manuel pour le paquet installé.
- **Validation :** suite complète avec et sans extra Tree-sitter, vérification de mutation ciblée sur les quatre défauts, rapport de couverture des chemins critiques.
- **Dépendances / risques :** commence avec phase 1 et se termine après phase 2; tests plus stricts révéleront probablement des défauts historiques.

### 4.2 Faire de la CI une barrière de qualité (P0)

- [ ] **En cours (19 septembre 2026).** Workflow refait avec permissions `contents: read`, contrôle Ruff bloquant, matrice base 3 OS × Python 3.8–3.14, profils de grammaires Python/complet sur 3 OS, puis build wheel/sdist, `twine check` et smoke hors checkout. Les 29 jobs des runs `35442699106` et `35442835093` ont réussi sur GitHub après correction des défauts Windows observés dans les runs précédents. Une PR de test et le nouveau contrôle des liens ajouté ensuite restent à vérifier; ne pas attribuer la réussite des runs antérieurs à ce contrôle inédit.

- **Objectif :** prouver que le produit s'installe, fonctionne et se construit sur les plateformes annoncées.
- **Changements :** matrice Python réellement supportée sur Linux/macOS/Windows, jobs avec/sans grammaires, lint strict, format, typage si l'API le revendique, tests Git, build wheel/sdist, installation puis smoke test des artefacts; fixer permissions minimales et versions d'actions; supprimer `--exit-zero` des contrôles attendus bloquants.
- **Fichiers :** `.github/workflows/ci.yml`, `pyproject.toml`, `tests/`, éventuellement scripts de smoke.
- **Acceptation :** une PR échoue si tests, format, lint, build ou installation d'artefact échouent; chaque OS/Python annoncé a un résultat CI consultable; publication exclue de la CI de PR.
- **Validation :** exécution d'une PR de test, lecture des logs par matrice, installation des wheel/sdist dans un environnement propre, vérification des permissions du workflow.
- **Dépendances / risques :** dépend de 4.1; Python 3.8 et les grammaires peuvent imposer un choix de versions supportées plus restreint.

### 4.3 Sécuriser les entrées et la chaîne de dépendances (P1)

- [ ] **En cours (19 septembre 2026).** La CLI refuse les contrôles de terminal et caractères bidi dans le texte et les labels; le mode Git réduit le contenu dangereux à un statut sans l'afficher. Les opérandes doivent être des fichiers réguliers, avec contrôle supplémentaire après ouverture non bloquante; un symlink vers un fichier régulier passe, une FIFO est rejetée. Des tests couvrent fichiers, stdin, labels Git, binaire NUL et FIFO. Politique de signalement ajoutée dans `SECURITY.md`. Scan local Gitleaks de l'historique sans résultat; audit local des dépendances complètes sans vulnérabilité connue après mise à jour du `pip` de test. Le job CI de sécurité a réussi dans le run `35444327149`. L'ancien modèle `.env.example` demandant un jeton PyPI a été retiré; aucun secret de publication n'est configuré. Le processus de publication approuvé reste à traiter.

- **Objectif :** réduire les surprises pour un outil qui lit des fichiers arbitraires et un script qui publie des artefacts.
- **Changements :** auditer exceptions de fichiers, symlinks, décodage, profondeur AST, sorties de terminal et contenu Git non fiable; ne pas exécuter le contenu comparé; auditer dépendances et grammaires, figer une stratégie de mise à jour, documenter signalement de vulnérabilité; ne jamais charger des secrets dans les jobs de PR.
- **Fichiers :** `src/linediff/`, `pyproject.toml`, `.github/workflows/`, nouveau `SECURITY.md`, `scripts/release-kit.sh`.
- **Acceptation :** aucune exécution de contenu issu des fichiers comparés; entrées malformées bornées et testées; politique de signalement claire; publication limitée aux événements autorisés avec secrets minimaux.
- **Validation :** audit de code, scan des dépendances et secrets en CI, tests d'entrées hostiles sans fuite de chemin/token dans les logs publics.
- **Dépendances / risques :** suit 3.1 et 4.2; éviter un faux sentiment de sécurité fondé sur un scan seul.

## Phase 5 — Installation, documentation et vitrine du dépôt (P1)

### 5.1 Rendre l'installation et les extras cohérents

- [x] **Terminé pour les parcours annoncés (19 septembre 2026).** `pyproject.toml` est la source des dépendances; l'ancien `requirements.txt` Markdown, l'extra de documentation sans build et la déclaration `py.typed` absente ont été retirés. Le guide pip/venv reflète le produit; wheel/sdist et leur licence ont été inspectés, `twine check` et smoke hors checkout ont réussi localement. La matrice CI `35445373893` a réussi sur Python 3.8–3.14 et trois OS avec installation éditable et profils de grammaires. Le run `35445659112` a construit les archives sur Linux, puis installé et testé **les mêmes archives** hors checkout sur Linux, macOS et Windows, avec Python 3.8 et 3.14. `pipx` et `uv tool` ne sont pas annoncés. La table de licence héritée garde les builds Python 3.8 au prix d'un avertissement setuptools dont la fin annoncée est février 2027; ce choix de maintenance est documenté.

- **Objectif :** faire marcher les commandes copiées depuis le README et expliquer précisément ce qui s'installe.
- **Changements :** aligner `pyproject.toml`, `requirements.txt` et guide d'installation; tester `pip`, `pipx` ou `uv tool` selon les parcours retenus; résoudre la compatibilité des versions Python/grammaires; retirer `py.typed` annoncé tant que le fichier et la vérification de typage ne sont pas prêts, ou le fournir réellement.
- **Fichiers :** `pyproject.toml`, `requirements.txt`, `MANIFEST.in`, `src/linediff/py.typed` si justifié, `docs/installation.md`, `README.md`.
- **Acceptation :** installation du paquet de base et des extras annoncés dans des environnements propres; commande `linediff --help` et scénario réel fonctionnels; aucune dépendance étrangère au produit sans raison documentée.
- **Validation :** smoke tests wheel/sdist sur OS/Python supportés, inspection du contenu des archives et de la métadonnée de paquet.
- **Dépendances / risques :** dépend de 2.2 et 4.2; les grammaires natives peuvent limiter la liste de plateformes.

### 5.2 Réécrire la documentation sur les capacités observées

- [x] **Terminé pour la documentation du code de développement (19 septembre 2026).** README et guides `PRODUCT`, index, FAQ, usage et exemples réécrits autour de la CLI actuelle; promesses multilangues, performances, téléchargements et site non vérifiés retirés. `scripts/check_docs.py` vérifie les liens locaux de 18 fichiers, l'exemple du quickstart est lié à un test, `twine check` passe et le README rendu sur GitHub a été inspecté visuellement. Le run CI `35443085289` incluant le contrôle des liens est vert. Les futurs liens de release restent soumis à 6.3.

- **Objectif :** restaurer la confiance et réduire le temps jusqu'à la première preuve.
- **Changements :** resserrer README autour du problème, de la démo réelle, de l'installation, des commandes exactes et des limites; corriger version et liens obsolètes dans `docs/`; retirer chiffres de performance non mesurés et promesses de cache, langages ou hébergement non validés; choisir une seule source de documentation en ligne ou rester sur GitHub tant que le site n'est pas publié.
- **Fichiers :** `README.md`, `docs/index.md`, `docs/api.md`, `docs/faq.md`, `docs/usage.md`, `docs/examples.md`, `CHANGELOG.md`, `pyproject.toml`.
- **Acceptation :** chaque commande et sortie montrées est issue de la version livrée; table « fonctionne / fallback / non pris en charge » explicite; aucun lien local cassé ni version contradictoire; URL en ligne vérifiée avant affichage.
- **Validation :** test automatisé des liens internes et des exemples copiables, revue humaine des affirmations, contrôle visuel du rendu Markdown sur GitHub.
- **Dépendances / risques :** dépend des phases 1–3; une prose plus courte exige de choisir les preuves les plus convaincantes.

### 5.3 Créer des preuves visuelles et un dépôt accueillant

- [ ] **En cours (19 septembre 2026).** Guide de contribution unifié, modèles d'issue/PR, `SECURITY.md`, `SUPPORT.md` et projet de métadonnées dans `docs/GITHUB_PRESENTATION.md` créés. Le guide a été essayé dans un clone propre avec une installation `.[dev]`, tests, Ruff et liens locaux verts. Captures fidèles des trois modes et d'un vrai `git diff --ext-diff`, variantes claire/sombre et provenance contrôlée ajoutées au dépôt; la principale a été revue à largeur mobile et dans le README rendu sur GitHub. La capture Git a été comparée par test à une nouvelle exécution réelle et inspectée sur les deux fonds dans Chrome. La description About distante conserve une promesse ancienne. Sa mise à jour autorisée reste à faire.

- **Objectif :** rendre la valeur compréhensible en quelques secondes et faciliter une première contribution.
- **Changements :** capturer de vrais terminaux pour le cas Python et la comparaison Git, fournir image/GIF seulement si lisible et légère, texte alternatif et transcription; simplifier `CONTRIBUTING.md` et `docs/contributing.md`, ajouter templates d'issue/PR, catégories « good first issue », politique de support et métadonnées GitHub pertinentes; éviter badges de téléchargements/performance sans vérification.
- **Fichiers :** `README.md`, nouveau `assets/` ou `docs/assets/`, `CONTRIBUTING.md`, `docs/contributing.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `SECURITY.md`.
- **Acceptation :** capture issue d'une commande reproductible, lisible sur mobile et desktop; une contribution de documentation suit un parcours testé; description, sujets et lien du dépôt contrôlés sur GitHub avant de les déclarer publiés.
- **Validation :** revue visuelle du README rendu, contrôle du poids et de l'accessibilité des médias, essai du guide de contribution dans un clone propre.
- **Dépendances / risques :** suit 3.2–3.3 et 5.2; paramètres GitHub distants exigent une vérification séparée.

## Phase 6 — Packaging, release et distribution (P1, publication bloquée par P0)

### 6.1 Mettre le processus de release sous garde

- [ ] **En cours (19 septembre 2026).** L'ancien script de publication anticipée est remplacé par une validation/compilation locale sans identifiants, tag, push ni upload; un workflow manuel ne produit que des artefacts Actions temporaires avec accès GitHub en lecture seule. Le guide `docs/RELEASING.md` décrit les contrôles et la vérification après publication. La version candidate `0.2.0a1` et ses notes sont préparées. Sur le commit propre `0adeeae`, le mode à blanc n'a créé aucun diff; tests, Ruff, liens, build, `twine check` et smoke isolé des deux archives ont passé. La CI du même commit est verte dans le run `35446450376` (42 jobs). Les SHA-256 des archives locales sont consignées dans `docs/RELEASE_NOTES_0.2.0a1.md`. Le workflow candidat manuel et une méthode de publication approuvée restent à valider.

- **Objectif :** produire une version traçable dont les artefacts correspondent au code validé.
- **Changements :** refondre `scripts/release-kit.sh` pour valider l'arbre propre et tous les gates avant mutation; rendre `--dry-run` réellement sans effet; ne jamais taguer ni téléverser avec tests ou `twine check` contournés; remplacer les identifiants locaux par publication à identité fédérée si la cible le permet; séparer préparation, approbation, build et publication; générer notes de release factuelles.
- **Fichiers :** `scripts/release-kit.sh`, `.github/workflows/` (workflow de release à créer), `CHANGELOG.md`, nouveau `docs/RELEASING.md`.
- **Acceptation :** test à blanc sans diff Git, version cohérente entre paquet/tag/changelog, échec avant upload si gate rouge; aucune release distale créée par la préparation seule; pas de publication accidentelle depuis PR.
- **Validation :** exécution locale en environnement temporaire, workflow sur tag de préversion ou dépôt de test, audit des artefacts et des permissions avant vraie publication.
- **Dépendances / risques :** attend 4.2, 5.1–5.2; PyPI et GitHub sont des états externes à vérifier après publication.

### 6.2 Livrer d'abord un paquet Python installable, puis des exécutables autonomes

- [ ] **En cours (19 septembre 2026).** Un script PyInstaller 6.22.3 prépare une archive autonome du CLI de base, un checksum SHA-256 et des smoke tests avant/après extraction (`--help`, exactitude, `--check-only`, structure Python, fallback, protocole Git). L'archive locale macOS arm64 du commit `0adeeae` a passé ces smoke tests avant et après extraction. Les jobs `standalone` du run CI `35446450376` ont réussi sur Linux, macOS et Windows; les six jobs d'installation des wheel/sdist sur trois OS ont également réussi. Le workflow candidat versionné n'a pas encore été exécuté et aucune archive n'est publiée. Les grammaires optionnelles ne sont pas embarquées.

- **Objectif :** offrir des téléchargements utiles aux développeurs avec ou sans environnement Python.
- **Changements :** publier wheel et sdist vérifiés; définir une recette de binaire autonome (par exemple PyInstaller) pour les OS/architectures réellement testés, inclure les grammaires nécessaires ou documenter explicitement le mode texte; créer archives, SHA-256 et instructions de désinstallation; comparer taille, démarrage et comportement au paquet Python.
- **Fichiers :** `pyproject.toml`, nouveaux scripts de packaging, `.github/workflows/release.yml`, `docs/installation.md`, `README.md`.
- **Acceptation :** wheel/sdist et chaque exécutable annoncé s'installent dans un environnement propre et exécutent `--help`, comparaison Python, fallback et Git; checksum vérifié après téléchargement; plateformes non testées non revendiquées.
- **Validation :** smoke tests sur machines CI par OS/architecture, inspection des archives, provenance des checksums, test de lecture complète des binaires, contrôle manuel de la page Release.
- **Dépendances / risques :** dépend de 6.1 et 2.2; taille et disponibilité des grammaires natives peuvent rendre certains binaires irréalistes : publier alors seulement les cibles validées.

### 6.3 Vérifier la publication de bout en bout

- [ ] **Préparé localement (19 septembre 2026).** Le brouillon de notes `docs/RELEASE_NOTES_0.2.0a1.md` distingue capacités, compatibilité, changement de code de sortie, limites et preuves requises. La construction candidate locale des wheel/sdist et de l'archive autonome macOS arm64 sur le commit `0adeeae` a réussi; la CI du même commit est verte dans le run `35446450376`. Aucune GitHub Release, fiche PyPI ou installation depuis une distribution publique n'a été vérifiée; la publication attend l'autorisation du mainteneur.

- **Objectif :** distinguer build réussi, publication et installation par un tiers.
- **Changements :** préparer notes, version cible et liste d'artefacts; après autorisation de publication, vérifier la GitHub Release et, si utilisée, la fiche PyPI; télécharger les artefacts publiés et les réinstaller hors du checkout; mettre à jour les liens et badges uniquement sur preuves.
- **Fichiers :** `CHANGELOG.md`, `README.md`, `docs/RELEASING.md`, workflow de release.
- **Acceptation :** tag et artefacts publics cohérents, sommes locales/distantes identiques, installation et démo depuis la distribution publiée, liens valides; preuve consignée avec date et version.
- **Validation :** téléchargement réel, `sha256sum`/`shasum`, smoke tests hors dépôt, contrôle des pages publiques et de leurs versions.
- **Dépendances / risques :** suit 6.2; publication dépend des comptes et autorisations externes et ne doit pas être présumée acquise.

## Phase 7 — Positionnement, adoption et contributions (P1/P2)

### 7.1 Établir une comparaison concurrentielle honnête

- [ ] **Préparé localement (19 septembre 2026).** `docs/COMPARISON.md`, `scripts/compare_tools.py` et les sorties brutes datées fixent Git, Difftastic 0.71.0 et delta 0.19.2 sur quatre fixtures du dépôt. Les deux archives concurrentes ont été contrôlées contre les SHA-256 de leurs releases. La comparaison décrit aussi les faiblesses de Linediff et l'ambiguïté d'un déplacement; les temps mesurés sont limités à une machine. Elle doit être rafraîchie sur une distribution Linediff réellement publiée après 6.3 avant de cocher cette phase.

- **Objectif :** montrer où Linediff aide réellement et où un autre outil convient mieux.
- **Changements :** sélectionner au moment de la phase un outil ligne (`git diff`), un outil syntaxique et une visionneuse; figer versions/commandes/corpus; comparer précision, lisibilité, vitesse et limites sur les mêmes cas; publier les sorties brutes et expliquer les écarts sans revendiquer une supériorité générale.
- **Fichiers :** nouveaux `docs/COMPARISON.md`, `benchmarks/`, `README.md`.
- **Acceptation :** chaque comparaison est reproductible et datée; cas où Linediff perd ou tombe en fallback visibles; proposition de valeur étroite cohérente avec les résultats.
- **Validation :** reproduction par un mainteneur dans un environnement propre, revue des mesures et captures, lien vers méthodes et versions.
- **Dépendances / risques :** attend les phases 2–6; outils externes changent, donc réactualiser avant tout usage public.

### 7.2 Créer une boucle d'adoption et de maintenance

- [ ] **Préparé localement (19 septembre 2026).** Le protocole neutre `docs/FEEDBACK_TRIAL.md` fixe les tâches, le consentement, les preuves minimales et la méthode de tri des retours. Aucun essai utilisateur réel ni recrutement n'a été effectué. Les cinq retours observés restent dépendants d'une distribution publiée et de participants consentants.

- **Objectif :** convertir l'intérêt initial en usage répété et contributions utiles.
- **Changements :** recueillir des retours consentis sur de vrais workflows de revue, suivre questions/régressions, documenter les limites et prioriser les issues; proposer des tâches de contribution bornées; publier des exemples courts et un changelog lisible lors des releases; éviter toute métrique de croissance non vérifiée.
- **Fichiers :** `CONTRIBUTING.md`, `README.md`, `docs/`, `.github/`, `CHANGELOG.md`.
- **Acceptation :** au moins cinq essais observés ou retours détaillés sur la version distribuée, problèmes classés avec décision et reproducteur, chemin de contribution testé; retours anonymisés ou publiés avec consentement.
- **Validation :** notes de sessions et issues liées, réexécution des reproducteurs, revue des changements réellement motivés par ces retours.
- **Dépendances / risques :** attend 6.3 pour tester la distribution; recrutement et consentement externes peuvent retarder la phase, sans être inventés.

## Phase 8 — Vidéo de démonstration du produit fini (dernière phase, P1)

**Gate absolu :** ne commencer cette phase qu'après implémentation et validation des phases 0 à 7, y compris installation depuis un artefact réellement publié, comportement Git vérifié, captures fidèles et limites documentées. Si un gate précédent est bloqué, la vidéo reste à faire; ne pas remplacer la preuve par une maquette.

### 8.1 Capturer un usage réel et écrire le conducteur

- **Objectif :** montrer un problème concret résolu par la version distribuée.
- **Changements :** utiliser obligatoirement la skill **`ffmpeg-video-editor`**; écrire un conducteur « problème du diff ligne → installation ou démarrage depuis l'artefact final → comparaison Python → information syntaxique utile → affichages/Git → limite/fallback »; capturer le terminal et les fichiers réels, sans écrans fictifs, données privées ni commandes simulées.
- **Fichiers :** nouveau `media/demo/` (sources et conducteur selon politique de taille), `README.md` après validation.
- **Acceptation :** chaque scène correspond à une commande reproductible de la version finale; version affichée, sortie et narration concordent; aucune fonction non démontrée n'est affirmée.
- **Validation :** relancer les commandes du conducteur et comparer les captures, revoir les prises brutes et retirer secrets/chemins personnels.
- **Dépendances / risques :** dépend de **toutes** les phases 0–7; changement tardif du produit exige une nouvelle capture.

### 8.2 Monter, exporter et vérifier intégralement

- **Objectif :** publier une vidéo courte, professionnelle et utilisable sur GitHub.
- **Changements :** avec `ffmpeg-video-editor`, sonder les sources avec `ffprobe`, monter avec rythme, titres sobres, zooms/recadrages seulement pour la lisibilité, transitions discrètes et audio propre si voix nécessaire; exporter une version 16:9 adaptée au README/GitHub et, si le contenu le justifie, une courte version verticale ou carrée; fournir sous-titres/transcription et une image d'aperçu issue du produit réel.
- **Fichiers :** `media/demo/`, `README.md`, éventuellement `docs/` pour la transcription; hébergement de la vidéo à choisir et vérifier.
- **Acceptation :** fichier final lu entièrement sans image noire ni son coupé; durée, résolution, codecs vidéo/audio, fréquence d'images et poids mesurés; H.264 avec pixel format compatible et `faststart` pour la version Web si approprié; liens et miniature fonctionnels depuis le README rendu.
- **Validation :** `ffprobe` sur chaque export, décodage complet avec `ffmpeg -f null -`, visionnage humain du début à la fin, vérification du rendu mobile/desktop et du téléchargement GitHub.
- **Dépendances / risques :** suit 8.1; les limites de taille/lecture de l'hébergement doivent être vérifiées avant de choisir les encodages, sans sacrifier la lisibilité du terminal.

## Résultat attendu

Après ces gates, Linediff doit pouvoir être présenté comme un outil terminal de comparaison **exact** avec un avantage syntaxique Python démontré, une intégration Git reproductible, une installation simple, une CI bloquante, des artefacts vérifiés, une documentation honnête et une vraie démonstration filmée sur la version distribuée. Cette combinaison peut favoriser l'adoption et le partage; elle ne garantit aucun nombre de stars.
