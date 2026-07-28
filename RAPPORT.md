# Rapport de projet — Pipeline qualité de l'air

## Répartition des tâches

Le groupe discutait régulièrement du projet en présentiel, à HEI, pour décider ensemble des orientations (choix des villes, de l'architecture, des outils), y compris pour les aspects techniques, où on échangeait nos avis avant de valider une direction.

## Méthode de travail

Le projet a été mené de façon incrémentale, étape par étape, en testant et validant chaque brique avant de passer à la suivante plutôt que de tout écrire d'un coup. L'idée était de toujours avoir quelque chose qui marche vraiment, testé avec des vraies données, pas juste "ça a l'air bon", avant d'avancer.

Ordre suivi : mise en place du repo Git, script de backfill historique 3 mois, script de nettoyage/fusion des données, chargement dans le data warehouse, test du pipeline horaire en local avec Airflow, dockerisation d'Airflow, puis déploiement réel en continu.

## Difficultés rencontrées et comment on les a résolues

Airflow en local (WSL) qui perdait le fil. Plusieurs fois, le "dag-processor", le processus qui scanne les fichiers de DAG, s'arrêtait sans prévenir, et plus rien n'apparaissait dans l'interface. La solution a été de comprendre qu'Airflow 3.x tourne avec 3 processus séparés (api-server, scheduler, dag-processor) qui doivent tous tourner en même temps, et de les relancer quand ça bloquait.

Connexion à la base Supabase refusée. Le mot de passe généré par Supabase contenait des caractères spéciaux qui cassaient le format de l'URL de connexion. Réglé en régénérant un mot de passe composé seulement de lettres et de chiffres.

Un bug dans le script de chargement du warehouse. Une ligne du script essayait d'utiliser une colonne (id_ville) qui n'existait pas encore à ce moment du programme, puisqu'elle n'est générée qu'après l'insertion des villes en base. Corrigé en réorganisant l'ordre des étapes du script.

Le vrai gros blocage : le déploiement cloud. Le plan de départ était de déployer Airflow (dockerisé) sur un serveur Oracle Cloud, dans leur offre "toujours gratuite". Le souci : même les offres cloud gratuites demandent une carte bancaire pour vérifier l'identité, à laquelle on n'avait pas accès. Plutôt que de rester bloquées, on a changé d'orchestrateur pour GitHub Actions, qui permet d'exécuter du code sur un planning directement sur les serveurs de GitHub, gratuitement et sans carte bancaire. Le travail Airflow/Docker n'a pas été perdu : il reste dans le repo, testé et fonctionnel en local, et sert de preuve de compétence même s'il n'est plus la version utilisée en production.

## Choix techniques et pourquoi

L'API OpenWeatherMap a été gardée parce qu'elle était déjà utilisée pour un exercice de cours et qu'elle propose à la fois les données en temps réel et un historique, ce qui évitait de jongler entre deux fournisseurs différents.

Les 5 villes (Antananarivo, Delhi, Paris, Los Angeles, Beijing) ont été choisies pour avoir des niveaux de pollution très différents d'une ville à l'autre, plutôt que des villes qui se ressembleraient toutes — l'idée étant de rendre les données plus intéressantes à analyser derrière.

Supabase a été choisi pour le data warehouse parce que c'est du PostgreSQL classique, gratuit, sans carte bancaire, avec une interface web pratique pour vérifier les données sans taper de requête.

Le détail complet des choix techniques et leurs justifications est dans ARCHITECTURE.md.
