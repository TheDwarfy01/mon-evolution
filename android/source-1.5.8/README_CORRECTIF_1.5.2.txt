Mon Évolution IMC — Sources correctif 1.5.2

Objectif : éviter le recouvrement de l’en-tête par la barre de notification Android 15+.

Modifications :
- La WebView est maintenant contenue dans une FrameLayout native.
- Les marges de status bar / navigation bar / encoche sont appliquées à la FrameLayout plutôt qu’au WebView.
- VersionCode 8 / VersionName 1.5.2 ; même applicationId fr.monevolution.app.
- La page HTML conservée de la v1.5.1, système « Rechercher une mise à jour » conservé.
- Permission Internet ajoutée pour vérifier le fichier de version sur GitHub Pages.

IMPORTANT : Ceci est le code source, PAS une APK signée.
Pour mettre à jour la v1.5.1 sans désinstallation ni perte de données, il faut
construire cette version avec Android SDK et signer avec la MÊME clé de
signature privée que la 1.5.1. Ne publiez PAS le keystore ni son mot de passe
sur GitHub. Une installation sur un appareil réel reste nécessaire pour valider
l’affichage.
