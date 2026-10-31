# Correctif onboarding premier lancement — v1.5.2 (à intégrer avant publication)

## Objectif
L'application distribuée ne doit embarquer **aucune donnée personnelle de démonstration**. Sur une nouvelle installation sans profils préexistants, afficher un écran de bienvenue neutre :
- « Créer mon profil » : prénom facultatif/nom, taille, poids initial, objectif, date de départ; enregistrer seulement après validation.
- « Restaurer une sauvegarde » : ouvrir le sélecteur Android de documents (ACTION_OPEN_DOCUMENT), accepter le JSON de sauvegarde multi-profils, vérifier le format et afficher un aperçu avant import.
- Aucun nom, poids, objectif, repas ou photo provenant d'un ancien appareil ne doit être codé en dur ni créé automatiquement.

## Détection sécurisée
1. Charger le stockage local **avant** toute initialisation de profil ou rendu du tableau de bord.
2. Si au moins un profil réel et valide existe : afficher le profil sélectionné précédemment, sinon le sélecteur de profils. Ne pas réinitialiser les données lors d'une mise à jour.
3. Si aucun profil réel n'existe : montrer l'écran d'accueil initial, sans création implicite d'un profil.
4. Si une ancienne version possède une base locale, conserver la compatibilité et effectuer une migration non destructive.
5. Si le chargement échoue (JSON malformé, permissions Drive manquantes, conflit ou fichier vide), **ne pas écraser les données** et proposer une nouvelle tentative.
6. Une restauration doit préserver les ID de profil, l'historique des pesées, repas et photos ainsi que les références Drive lorsque leur permission est toujours valide; protéger contre les doublons d'ID et demander avant de remplacer un profil existant.

## Confidentialité
Le JSON d'une sauvegarde est privé. Ne jamais publier de profil personnel dans les ressources APK, le dépôt public, les tests ou les journaux.

## Critères de validation indispensables
- Nouvelle installation Samsung A : aucun « Bonjour Mario », aucun poids / objectif prérempli; les deux options apparaissent.
- « Créer mon profil » puis redémarrer : le profil créé s'affiche, le formulaire initial ne réapparaît plus.
- Nouvelle installation Samsung B : restauration de plusieurs profils depuis Drive, tous les historiques correspondent.
- Mise à jour 1.5.1 → 1.5.2 : profils, repas, photos et pesées préservés sans retour sur l'écran initial.
- Sauvegarde vide / JSON invalide / permission Drive révoquée : aucune destruction de données.
- Profil partagé : accès lecture seule, séparé des profils locaux éditables.

## Publication
Ce document est le cahier des charges, **pas une preuve d'implémentation**. Modifier les sources dans `android/releases/Mon_Evolution_IMC_v1.5.2_correctif_sources.zip`, compiler et tester avant de déclarer la 1.5.2 publiée. Ne pas déclencher le workflow de publication avant cette validation et la configuration des secrets de signature.