# Mon Évolution IMC

[![Dernière version](https://img.shields.io/github/v/release/TheDwarfy01/mon-evolution?label=Version%20Android&color=72dfcb)](https://github.com/TheDwarfy01/mon-evolution/releases/latest)
[![Télécharger l'APK](https://img.shields.io/badge/T%C3%A9l%C3%A9charger-APK%20Android-72dfcb)](https://github.com/TheDwarfy01/mon-evolution/releases/latest)

**Mon Évolution IMC** est une application Android indépendante pour suivre son poids et son alimentation, avec plusieurs profils, sauvegardes et partage sécurisé.

🌐 **[Site officiel](https://thedwarfy01.github.io/mon-evolution/)** · 📦 **[Dernière version et téléchargement](https://github.com/TheDwarfy01/mon-evolution/releases/latest)** · 🔐 **[Confidentialité](https://thedwarfy01.github.io/mon-evolution/confidentialite.html)**

## Fonctionnalités

- **Poids et IMC :** historique, objectifs, indicateurs de progression et graphiques avancés.
- **Repas :** calendrier alimentaire, descriptions, photos et bilans PDF mensuels.
- **Profils :** plusieurs profils personnels, avec portrait et préférences.
- **Partage :** invitations par lien, consultation en lecture seule, chiffrement AES-256-GCM et contrôle des accès via Google Drive.
- **Synchronisation :** actualisation automatique des profils des proches au lancement, avec états et heures des synchronisations.
- **Google Drive :** sauvegarde et restauration dans un fichier choisi par l'utilisateur.
- **Rappels :** repas, photos, pesée et injections si prescrites, configurables par profil.
- **Mises à jour :** recherche automatique d'une nouvelle version à l'ouverture.

## Installer ou mettre à jour

1. Ouvrez **[la dernière release](https://github.com/TheDwarfy01/mon-evolution/releases/latest)**.
2. Téléchargez le fichier `Mon_Evolution_IMC_v*.apk` dans la section **Assets**.
3. Installez-le sur Android. Pour une mise à jour, **ne désinstallez pas la version précédente**.

Si un navigateur bloque le téléchargement sur Samsung, essayez Firefox ou DuckDuckGo. Android peut demander d'autoriser l'installation depuis le navigateur utilisé.

## Code source Android complet

📂 **[Sources Android v1.6.31 — dossier de référence](android/source-1.6.31/)**

Le dossier `android/source-1.6.31/` contient le projet Gradle Android complet (activité principale, rappels, ressources et interface WebView) **sans fichiers compilés ni clés privées**. Il peut être ouvert directement depuis Android Studio ou utilisé comme base commune par les différentes conversations et contributeurs.

Les correctifs historiques sont conservés dans `android/patches/`, mais **il n'est pas nécessaire de les rejouer** pour travailler sur la v1.6.31. Les nouvelles évolutions peuvent partir de ce dossier versionné.

## Publication et versions

Les APK signés sont publiés dans **[GitHub Releases](https://github.com/TheDwarfy01/mon-evolution/releases)**. Le site officiel consulte automatiquement l'API GitHub Releases pour présenter la dernière version disponible et son APK officiel. Le bouton « Dernière version » de ce README utilise aussi une URL permanente : aucune référence à un ancien numéro de version.

Les workflows Android se trouvent dans `.github/workflows/` et les correctifs successifs dans `android/patches/`. Les notes détaillées de chaque version figurent dans sa release.

## Confidentialité

Les données personnelles sont stockées sur l'appareil et, si vous choisissez cette option, dans un fichier Google Drive. Le partage des profils utilise un fichier chiffré et une invitation distincte du code de déchiffrement. Un destinataire peut consulter un profil partagé mais ne peut pas modifier le profil source.

**Attention :** Mon Évolution IMC est un outil personnel de suivi, pas un dispositif médical. Il ne fournit pas de diagnostic ni de consigne thérapeutique.

---
© 2026 Mon Évolution IMC
