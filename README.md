# ML-for-Climate-Risk
## Generation de l'environnement virtuel sous conda
Exécuter le code  **conda create -n _envclr python=3.11**
Si les PATHs ne sont pas directement remplacer automatiquement, penser à l'ajouter manuellement (Au niveau des variables de l'environnement).
Exécuter **conda activate _envclr** pour activé l'envrionnement
Exécute **pip install -r requirements.txt** pour installer toutes les dependances
Si tu fais d'autres installation  et tu veux les ajouter dans le requirements il suffit d'exécuter **conda list --export > requirements.txt**

Pour verfier qu'il y a pas de soucis de cohérence dans ton environnement exécute: **pip check**  et sortie doit être *No broken requirements found*