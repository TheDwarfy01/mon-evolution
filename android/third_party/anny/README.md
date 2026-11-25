# Anny 0.6.2 — source locale
Archive source officielle publiée le 26 octobre 2026.
Origine : https://pypi.org/project/anny/0.6.2/
Amont : https://github.com/naver/anny
SHA-256 : 270ef9ce790a940199f79b66556a11f9b90793e4bbe7ce8242f31442cde4c9ea
Le code et les ressources distribuées restent dans ce dépôt. Les avis de licence
restent dans l'archive originale. Ne pas remplacer automatiquement la version.
Extraire dans un dossier de travail, sans récupérer Anny depuis Internet :
`tar -xzf android/third_party/anny/anny-0.6.2.tar.gz -C /tmp`.
Utiliser exclusivement la topologie native Anny; ne pas télécharger les modèles
SMPL/SMPL-X soumis à des conditions distinctes.
Les dépendances Python/PyTorch et le port Android ne sont pas inclus dans cette
étape. L'APK de production devra intégrer les ressources exportées et les calculs
locaux nécessaires, avec vérification hors réseau.
