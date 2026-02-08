# PROJET HNS : Multilevel_Geovisualisaiton_Airbnb_JO
**Les Jeux olympiques de Paris 2024 et les hôtes Airbnb :**
**une analyse spatialisée de la participation au marché et des stratégies de communication**

## Introduction
Ce projet étudie l'impact des **Jeux Olympiques et Paralympiques de Paris 2024** sur le marché Airbnb à Paris.  
L'objectif est d'analyser les **comportements stratégique des hôtes**, que ce soit la participation au marché ou l'ajustement des stratégies de communication, ainsi que la manière dont un événement majeur influence **l'offre et la demande** dans le contexte urbain parisien.


## Jeux de données 
### Données principaux - data_geo\Q1Q2Q3
- **Source** : Données disponible sur le site Inside Airbnb  
- **Période** : Mars, Juin, Septembre 2024 à Paris (Avant, pendant et après la préparation des Jeux Olympiques)
- **Variables** : Coordonnées géographiques (latitude, longtitude), prix, disponibilité dans les 90 jours suivant, description personnelle, description sur l'annonce, description sur le voisinage, etc.

### Données complémentaires
- Carte de quartiers Paris : data_map\paris_ar.gpkg
- Carte de sites olympiques principaux : data_geo\main_venues_JO.gpkg
 

## Methodologie
- **Variable clé**: Hôtes en changement (is_changed):

- Au niveau de participation :
Nouveaux hôtes (depuis 2024) , hôtes qui reviennent en juin (n’existe pas dans les données de mars), hôtes qui réouvrent leur disponibilité pour JO (disponibilité_90=0 en mars);

- Au niveau de présentation de soi : Hôtes qui modifient sa description ou /et la photo personnelle(s).


## Problématique et hypothèses :
- **Problématique** : Comment l’approche des Jeux Olympiques de Paris 2024 a-t-elle influencé la participation et les stratégies communicatives des hôtes sur Airbnb ?

- **Hypothèses** : 


**H1** : L’approche des Jeux olympiques de Paris 2024 conduit à une augmentation temporaire du nombre d’hôtes actifs, des prix des annonces et de leur disponibilité sur le marché.

**H2** : Les comportements des hôtes, notamment l’entrée sur le marché et les changements observés, varient selon les territoires parisiens et selon la proximité aux sites olympiques.

**H3** : Les hôtes utilisent plus les Jeux olympiques comme argument marketing, en particulier pour les logements situés à proximité des sites olympiques, afin d’attirer les voyageurs.


## Résultats et analyses :

-**Tendances globales**:

1.Densité des hôtes : Augmentation forte en juin, surtout 11e, 15e, 17e, 18e arrondissements, proches aux sites olympiques, réduction en septembre.

2.Prix moyenne : la hausse n'est pas généralisé, elle dépasse 100 euros dans les dans 7e et 16e arronds.

3.Disponibilité 90:  augmente de 10 jours environ pendant JO, elle 
se maintient et progresse après JO

- **Hôtes en changement**:

4.Changements: jusqu'à 50% environ dans tous les arronds, surtout aux arrondissements extérieurs de Paris, du 11e au 20e arrondissements.

5.Entrants récents vs adaptation de stratégies communicatives :

Les nouveaux entrants se trouvent plutôt dans les arrondissements extérieurs de Paris, alors que les hôtes ont modifié leur présentation de soi sont plus présent au centre.

6.15e, 16e arrondissements sont des zones mixtes : beaucoup de nouveaux entrants et nouvelles images de soi.


- **JO marketing**:

7.Les JO comme un argument de marketing devient plus fréquent en juin, surtout dans les arrondissements proches aux sites olympiques, mais la proportion globale reste relativement faible (10%).


- **Visualisation** : output_map1


## Conclusion et perspective :
- L’approche des Jeux olympiques de Paris 2024 s’accompagne de 
changements visibles : l’entrée temporaire, la fluctuation du prix et de 
la disponibilité, l’adaptation des stratégies communicatives.
- La dynamique n’est pas homogène dans l’espace et présente parfois 
des distributions différentes selon les arrondissements ou des 
concentrations autour des sites olympiques.
- L’analyse spatialisée permet de mettre en évidence des réactions 
différenciées des hôtes face à un événement exceptionnel et 
temporaire

