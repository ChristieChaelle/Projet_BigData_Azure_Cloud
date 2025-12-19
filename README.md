# Projet de scoring bancaire
## Présentation du projet

Ce projet a été réalisé dans le cadre du Master 2 Big Data et Intelligence Artificielle.  
L’objectif principal est de concevoir une application de scoring bancaire capable d’estimer le risque de défaut d’un client à partir de données historiques, tout en proposant une interface claire permettant d’analyser et de comprendre les résultats.

Le projet couvre l’ensemble de la chaîne de valeur, depuis le calcul des scores sur un environnement Big Data jusqu’à leur restitution via une interface utilisateur.

## Objectifs

L’application vise à :
- prédire le risque de défaut d’un client à l’aide d’un modèle de machine learning,
- analyser les principaux facteurs influençant ce risque,
- exposer ces traitements via une API,
- proposer une interface simple permettant de consulter les prédictions et les analyses.

## Architecture générale

L’architecture repose sur une séparation claire des responsabilités.

L’interface utilisateur est développée avec Streamlit. Elle permet à l’utilisateur de saisir un identifiant client, de consulter le score de risque et d’explorer différentes analyses globales.

Le backend est assuré par une API Flask. Cette API centralise la logique applicative, gère les appels vers Databricks et renvoie les résultats sous un format exploitable par l’IHM.

Les calculs, le prétraitement des données et l’exécution du modèle de machine learning sont réalisés sur Databricks, en s’appuyant sur Spark et Spark MLlib.

## Organisation du projet

Le projet est structuré de manière à isoler clairement chaque composant :
- backend : qui contient app.py et requirements.txt. API Flask servant de middleware entre l’IHM et Databricks 
- frontend : qui contient le dossier pages et le fichier accueil.py 
- accueil.py : point d’entrée de l’interface Streamlit et gestion de la navigation  
- pages/1_client_prediction.py : page Streamlit dédiée à la prédiction individuelle d’un client  
- pages/2_data_analysis.py : page Streamlit dédiée à l’analyse globale et aux visualisations  
- .env : variables d’environnement (non versionné)  

Cette organisation facilite la maintenance, l’évolution du projet et le déploiement.

## Variables d’environnement

Les paramètres sensibles (URL de l’API, identifiants Databricks, tokens) sont stockés dans un fichier .env  
Ce fichier est chargé au démarrage de l’application et permet de séparer la configuration du code source.

Le fichier .env n’est volontairement pas inclus dans le dépôt GitHub.

## API Flask

L’API Flask joue le rôle de couche intermédiaire.  
Elle expose notamment :
- un endpoint de prédiction du risque de défaut pour un client donné,
- un endpoint de génération d’analyses et de visualisations,
- un endpoint de supervision permettant de vérifier l’état du service.

L’API communique avec Databricks via l’API REST et gère également la mise en cache et les logs applicatifs.

## Interface Streamlit

L’interface utilisateur est construite avec Streamlit.  
Elle se compose de deux pages principales :
- une page de prédiction client permettant d’obtenir un score et une recommandation,
- une page d’analyse globale proposant des visualisations interactives.

La navigation est centralisée dans un fichier unique afin d’éviter toute duplication de logique entre les pages.

## Modèle de machine learning

Le modèle utilisé est une régression logistique entraînée sur des données historiques de clients.  
Le modèle est déployé sur Databricks et utilisé uniquement en phase d’inférence dans l’application.

Les résultats fournis incluent :
- un score de risque,
- une classe de décision,
- des recommandations métier associées.

## Lancement du projet

Pour exécuter le projet en local :

1. Lancer l’API Flask :
```bash
python app.py
```

2. Lancer l’interface Streamlit :
```bash
python -m streamlit run streamlit_app.py
```

L’application est alors accessible via le navigateur.


## Conclusion

Ce projet illustre la mise en œuvre concrète d’une application de scoring bancaire en environnement Big Data et Cloud.  
Il met l’accent sur la structuration, la séparation des responsabilités et l’intégration de plusieurs technologies (Streamlit, Flask, Databricks, Spark).

Il constitue une base solide pouvant être enrichie par des modèles plus avancés, des mécanismes d’explicabilité ou une industrialisation plus poussée.
