# Mon Évolution IMC — Android

## État du chantier v1.5

La branche `develop/mon-evolution-imc-v1.5` prépare l'intégration Android. **Elle ne contient pas encore une APK v1.5** et n'est pas publiée en production.

La dernière APK distribuée dans la conversation était la version **1.4**. L'archive de code source conservée séparément dans la bibliothèque ChatGPT est plus ancienne (**1.2**) : elle ne doit **pas** remplacer la 1.4 sans récupération des fonctions manquantes. L'APK 1.4 inclut notamment des écrans de partage Drive via le sélecteur Android.

## Principes à respecter

- Identifiant Android existant : `fr.monevolution.app`.
- Conserver le certificat de signature original pour installer une mise à jour sans désinstallation.
- Ne jamais publier la clé `.keystore`, un mot de passe, un jeton OAuth ou des données de pesée.
- Garder l'hébergement GitHub Pages à la racine du dépôt.
- Placer le futur code Android dans `android/`.
- Générer une APK nommée `Mon_Evolution_IMC_v1.5.apk` et afficher « Mon Évolution IMC » dans l'app et sa page À propos.
- Tester les migrations, sauvegardes et partages sur deux téléphones avant diffusion.

Voir [le cahier d'intégration](../docs/v1.5-integration.md).
