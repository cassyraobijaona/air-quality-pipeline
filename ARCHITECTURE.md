
# Architecture du projet

## Le principe

On récupère la qualité de l'air pour 5 villes via l'API OpenWeatherMap, toutes les heures. Les données brutes sont sauvegardées telles quelles, puis nettoyées et fusionnées dans un fichier CSV unique, puis chargées dans une base de données organisée pour l'analyse, data warehouse. Tout ça tourne automatiquement, sans qu'on ait besoin d'intervenir.

## Les villes

On a choisi Antananarivo, Delhi, Paris, Los Angeles et Beijing. L'idée était d'avoir des villes sur des continents différents avec des niveaux de pollution très différents, pour que les données récoltées aient un vrai intérêt à analyser plutôt que d'être toutes similaires.

## Pourquoi ces outils

**OpenWeatherMap** pour la donnée : c'est l'API qu'on utilisait déjà avant pour un autre projet, elle est gratuite, et elle a un avantage pratique important, elle propose à la fois les données en temps réel et un historique, utile pour le backfill des 3 derniers mois.

**Le stockage brut et propre directement dans le repo Git** (dossiers `data/raw/` et `data/clean/`) : pas besoin d'un système compliqué, les fichiers bruts ne sont jamais touchés une fois écrits, et le fichier propre est reconstruit à chaque exécution à partir des fichiers bruts.

**Supabase pour le data warehouse** : c'est une base PostgreSQL gratuite, hébergée, avec une interface web pour vérifier les tables sans avoir à taper des requêtes SQL à chaque fois. Pas besoin de carte bancaire pour l'utiliser.

**GitHub Actions comme orchestrateur** : c'est le choix qui a le plus changé en cours de route. Au départ on voulait utiliser Airflow (vu en cours) déployé sur un serveur cloud (Oracle Cloud), mais toutes les offres cloud gratuites sérieuses demandent une carte bancaire pour la vérification d'identité, et on n'y avait pas accès. On a donc gardé Airflow comme preuve de compétence, testé en local, puis dockerisé avec docker-compose, tout est encore dans le repo, mais pour la vraie mise en production on utilise GitHub Actions : un fichier de configuration dans le repo dit à GitHub de lancer notre pipeline toutes les heures, sur ses propres serveurs, gratuitement. On voit l'historique de toutes les exécutions directement dans l'onglet Actions du repo.

**Les secrets** comme clé API, accès à la base sont stockés dans GitHub Secrets, jamais écrits en clair dans le code.

## Le schéma du data warehouse

On a fait un schéma en étoile avec une table de faits et deux dimensions :

- `dim_ville` : id, nom, pays, latitude, longitude
- `dim_temps` : id, date, heure, jour, mois, année, jour de la semaine, weekend ou non
- `fait_qualite_air` : les clés vers les deux dimensions, l'AQI, et les concentrations de chaque polluant (CO, NO, NO2, O3, SO2, PM2.5, PM10, NH3)

Comme vu en cours, la table de faits ne contient que des mesures et des clés étrangères, jamais d'infos descriptives comme le nom de la ville ou la date en clair.

## Comment le pipeline s'enchaîne :

1. Extraction : un appel API par ville, sauvegardé en JSON brut. Si une ville échoue, le pipeline continue quand même avec les autres.
2. Nettoyage : tous les fichiers bruts sont relus, fusionnés, dédoublonnés, triés dans un seul CSV.
3. Chargement : ce CSV est chargé dans les 3 tables du warehouse sur Supabase.
4. Le tout est lancé automatiquement toutes les heures par GitHub Actions, qui commit aussi les nouvelles données dans le repo à chaque exécution.
