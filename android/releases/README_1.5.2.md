# Correctif Android 1.5.2 — état : sources uniquement

L'archive `android/releases/Mon_Evolution_IMC_v1.5.2_correctif_sources.zip` contient les sources Android du correctif d'affichage sous la barre de notifications (Android 15), avec versionCode 8 et versionName 1.5.2.

**La version 1.5.2 n'est pas encore publiée ni signée.** Le fichier public `version.js` doit rester `published: false` tant que la compilation signée n'a pas réussi. Ne jamais distribuer l'archive ZIP comme si c'était une APK.

## Publication sécurisée
Un workflow manuel est disponible dans **Actions → Construire et publier APK 1.5.2**. Il compile les sources avec Gradle/SDK, signe l'APK avec la même clé privée que la 1.5.1, vérifie sa signature puis publie l'APK sur GitHub et active la notification de mise à jour.

Il faut créer **avant de lancer** ces secrets dans **Settings → Secrets and variables → Actions** :

- `ANDROID_KEYSTORE_BASE64` : contenu base64 du fichier keystore Android (sans sauts de ligne).
- `ANDROID_KEYSTORE_PASSWORD` : mot de passe du keystore.
- `ANDROID_KEY_ALIAS` : alias de la clé.
- `ANDROID_KEY_PASSWORD` : mot de passe de la clé (peut être identique au précédent).

Ces valeurs sont privées, ne doivent jamais être ajoutées aux fichiers GitHub, aux journaux de compilation ou à la conversation. Le fichier keystore ne doit pas être commité.

Après le succès du workflow, tester dans la version 1.5.1 : **À propos → Rechercher une mise à jour**. La mise à jour doit être installée par-dessus la version existante, sans désinstallation. En cas de refus du gestionnaire de paquets Samsung, utiliser ADB pour relever l'erreur précise ; ne pas supprimer les données.

La mise à jour est un téléchargement proposé à l'utilisateur, **pas une installation automatique**. Un test sur téléphone est nécessaire pour confirmer le correctif d'affichage.


## Nouveau prérequis (31 octobre 2026) : premier lancement neutre

Avant de signer et publier la 1.5.2, intégrer et valider l'écran de premier lancement décrit dans [`PREMIER_LANCEMENT_1.5.2.md`](./PREMIER_LANCEMENT_1.5.2.md). Une nouvelle installation doit demander de créer un profil ou de restaurer une sauvegarde, sans afficher le nom, le poids ou les objectifs d'un ancien utilisateur. La mise à jour 1.5.1 → 1.5.2 doit préserver les profils réels.

**Attention : ceci n'est pas encore intégré dans l'archive ZIP des sources. Le workflow de publication ne doit pas être lancé avant la modification et les tests.**
