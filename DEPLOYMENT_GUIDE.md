# Guide de Déploiement du Backend E-Learning

Ce document explique comment déployer le backend de la plateforme e-learning sur Render pour obtenir un endpoint en ligne et fonctionnel.

## Solution de Déploiement Recommandée

**Render** est la meilleure solution gratuite pour ce projet pour les raisons suivantes :
*   **Niveau Gratuit Généreux :** Offre gratuite adaptée aux projets de développement et personnels.
*   **Déploiement Continu (CI/CD) :** S'intègre parfaitement avec GitHub pour un déploiement automatique à chaque push.
*   **Facilité d'Utilisation :** Interface intuitive et configuration simplifiée.

## Prérequis

1.  Un compte GitHub avec le code du backend.
2.  Un compte Render ([render.com](https://render.com)).
3.  Les informations de connexion de votre base de données Supabase (URL et clé API).

## Étapes de Déploiement

### Étape 1 : Préparation du Code Local

Avant de déployer, assurez-vous que votre projet local est prêt pour la production.

1.  **Ajoutez Gunicorn aux dépendances :**
    Ouvrez votre fichier [`requirements.txt`](requirements.txt:1) et ajoutez la ligne suivante :
    ```
    gunicorn
    ```

2.  **Créez un fichier `Procfile` :**
    À la racine de votre projet, créez un fichier nommé `Procfile` (sans extension) avec le contenu suivant :
    ```
    web: gunicorn app:app
    ```
    Ce fichier indique à Render comment démarrer votre application Flask.

### Étape 2 : Configuration sur Render

1.  **Connectez votre Dépôt GitHub :**
    *   Connectez-vous à votre compte Render.
    *   Allez dans le tableau de bord et cliquez sur **"New +"** puis **"Web Service"**.
    *   Sélectionnez votre dépôt GitHub contenant le code du backend.

2.  **Configurez les Paramètres du Service :**
    *   **Name** : Donnez un nom à votre service (ex: `elearning-api-backend`).
    *   **Region** : Choisissez une région (ex: `Frankfurt`).
    *   **Branch** : Assurez-vous que votre branche principale est sélectionnée (ex: `main`).
    *   **Runtime** : Render devrait détecter **Python 3**.
    *   **Build Command** : `pip install -r requirements.txt`
    *   **Start Command** : `gunicorn app:app`
    *   **Instance Type** : Laissez l'option **Free** sélectionnée.

3.  **Ajoutez les Variables d'Environnement :**
    C'est l'étape la plus critique. Dans la section **"Environment"**, ajoutez les variables suivantes avec les valeurs correspondantes de votre projet Supabase (trouvées dans votre fichier [`.env`](.env:1) local) :

    | Nom de la Variable | Valeur | Description |
    |---|---|---|
    | `SUPABASE_URL` | `votre_url_supabase` | L'URL de votre projet Supabase. |
    | `SUPABASE_KEY` | `votre_cle_supabase` | La clé anon (ou service) de votre projet Supabase. |
    | `JWT_SECRET_KEY` | `une_cle_secrete_robuste` | Une clé secrète pour signer les tokens JWT. Générez-en une nouvelle sur [random.org/strings](https://www.random.org/strings/). |

4.  **Lancez le Déploiement :**
    Cliquez sur **"Create Web Service"**. Render va maintenant construire et déployer votre application. Attendez que le statut passe à **Live**.

### Étape 3 : Utilisation de l'API Déployée

Une fois le déploiement réussi, Render vous fournira une URL publique pour votre service, au format : `https://votre-service.onrender.com`.

**Endpoints Disponibles :**

*   **Documentation Swagger :** `https://votre-service.onrender.com/api/docs`
*   **Login Admin :** `POST https://votre-service.onrender.com/api/v1/auth/login`
*   **Dashboard Admin (protégé) :** `GET https://votre-service.onrender.com/api/v1/admin/dashboard-data`

**Exemple d'utilisation avec cURL :**

1.  **Se connecter pour obtenir un token :**
    ```bash
    curl -X POST "https://votre-service.onrender.com/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "votre-admin@email.com", "password": "votre-mot-de-passe"}'
    ```
    Réponse attendue :
    ```json
    {
      "access_token": "votre_token_jwt",
      "token_type": "bearer"
    }
    ```

2.  **Accéder à un endpoint protégé :**
    ```bash
    curl -X GET "https://votre-service.onrender.com/api/v1/admin/dashboard-data" \
    -H "Authorization: Bearer votre_token_jwt"
    ```

## Déploiement Continu

Chaque fois que vous pousserez (`git push`) des changements sur la branche configurée (ex: `main`) de votre dépôt GitHub, Render déclenchera automatiquement un nouveau déploiement. Vous pouvez suivre la progression des logs directement dans l'interface Render.

## Bonnes Pratiques

*   **Gardez vos secrets en sécurité :** Ne jamais commettre de fichiers contenant des secrets (comme `.env`) dans votre dépôt Git.
*   **Testez localement avant de pousser :** Assurez-vous que votre application fonctionne correctement en local avant de déployer.
*   **Surveillez les logs :** En cas d'erreur, les logs sur Render sont votre meilleure source de débogage.

## Support

Si vous rencontrez des problèmes :
1.  Consultez les logs de déploiement dans l'interface Render.
2.  Vérifiez que toutes les variables d'environnement sont correctement configurées.
3.  Assurez-vous que votre code local est à jour et qu'il n'y a pas d'erreurs de syntaxe.