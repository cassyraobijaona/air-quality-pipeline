
# Pipeline de qualité de l'air — DONNEES2

Ce repo contient un pipeline qui va chercher la qualité de l'air de 5 villes toutes les heures, et qui range tout ça dans une base de données propre pour qu'on puisse l'analyser derrière. Pour comprendre pourquoi on a fait tel ou tel choix technique, voir ARCHITECTURE.md.

## Les 5 villes

On suit Antananarivo (Madagascar), Delhi (Inde), Paris (France), Los Angeles (États-Unis) et Beijing (Chine).

Antananarivo : lat -18.8792, lon 47.5079
Delhi : lat 28.7041, lon 77.1025
Paris : lat 48.8566, lon 2.3522
Los Angeles : lat 34.0522, lon -118.2437
Beijing : lat 39.9042, lon 116.4074

## Ce qu'il y a dans le fichier clean

Le fichier data/clean/qualite_air_clean.csv contient une ligne par ville et par heure, trié dans l'ordre chronologique, sans doublons. Voici ce que veut dire chaque colonne :

- ville, pays : le nom de la ville et son code pays
- latitude, longitude : les coordonnées de la ville
- timestamp_unix et timestamp : l'heure de la mesure, en unix puis en format lisible (UTC)
- aqi : l'indice de qualité de l'air d'OpenWeatherMap, ça va de 1: bon à 5: très mauvais
- co, no, no2, o3, so2, pm2_5, pm10, nh3 : les concentrations de chaque polluant, en microgrammes par mètre cube (μg/m³)

## Sur quelle période on a des données

On a commencé par récupérer 3 mois d'historique en arrière (depuis fin avril 2026) pour les 5 villes d'un coup. Depuis que le pipeline est déployé, il ajoute une nouvelle mesure par ville chaque heure, en continu.

Si jamais il manque une mesure à un moment donné pour une ville, c'est probablement que l'API a eu un souci ponctuel (timeout, erreur réseau) — le script est fait pour ne pas planter dans ce cas-là, il passe juste à la ville suivante et continue. Ce genre de trou reste rare et isolé, ce n'est pas un problème structurel du pipeline.

## Le data warehouse

On a mis les données dans une base PostgreSQL sur Supabase, organisée en schéma en étoile, comme vu en cours :

- dim_ville contient le nom, le pays et les coordonnées de chaque ville
- dim_temps contient la date découpée (heure, jour, mois, année, jour de la semaine, weekend ou pas)
- fait_qualite_air contient les mesures (AQI et tous les polluants) reliées aux deux dimensions par leurs clés

À chaque exécution du pipeline, les 3 tables sont recréées et rechargées entièrement à partir du fichier clean.

## Comment se connecter à la base

La chaîne de connexion n'est écrite nulle part dans le code, ni sur Git. Le pipeline automatique la récupère depuis un secret GitHub, et en local elle vit dans un fichier .env qu'on ne commit jamais. Si quelqu'un a besoin d'un accès en lecture, un membre du groupe, il faut demander à être ajouté comme collaborateur sur le projet Supabase, ou demander la chaîne de connexion directement, en dehors de Git.

## Faire tourner le pipeline en local

pip install -r requirements.txt
python scripts/backfill.py --months 3
python scripts/clean.py
python scripts/load_warehouse.py

Il faut un fichier .env avec OPENWEATHER_API_KEY et DATABASE_URL dedans pour que ça marche.
