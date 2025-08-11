# Documentation de l'API de la Plateforme E-Learning

Ce document fournit les informations nécessaires aux développeurs frontend pour interagir avec l'API de la plateforme e-learning.

## 1. Introduction

L'architecture du backend est maintenant une **API-first**, ce qui signifie qu'elle expose des points de terminaison (endpoints) JSON et ne gère plus le rendu de l'interface utilisateur. Deux applications frontend distinctes (une pour les **étudiants** et une pour les **administrateurs**) peuvent être construites en utilisant cette API.

La documentation technique complète et interactive de chaque point de terminaison est disponible via **Swagger UI** lorsque l'application est en cours d'exécution.

- **URL de la documentation Swagger :** `http://127.0.0.1:5000/api/docs`

## 2. Flux d'Authentification (pour les deux applications)

L'API utilise une authentification par token **JWT (JSON Web Token)**. C'est un processus en deux étapes :

### Étape A : Connexion de l'utilisateur

- **Endpoint :** `POST /api/v1/auth/login`
- **Description :** Authentifie un utilisateur (étudiant ou admin) avec son email et son mot de passe.
- **Corps de la requête :**
  ```json
  {
    "email": "votre.email@example.com",
    "password": "votre_mot_de_passe"
  }
  ```
- **Réponse en cas de succès (200 OK) :**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```
- **Action Frontend :** Stockez l'`access_token` et le `refresh_token` de manière sécurisée (par exemple, dans `localStorage` ou un cookie `HttpOnly`).

### Étape B : Envoyer des requêtes authentifiées

- Pour tous les appels aux points de terminaison protégés, vous devez inclure l'`access_token` dans l'en-tête `Authorization`.
- **Format de l'en-tête :** `Authorization: Bearer <votre_access_token>`

### Étape C : Rafraîchir le token d'accès

- L'`access_token` a une durée de vie courte (30 minutes). Lorsqu'il expire, l'API renverra une erreur `401 Unauthorized`.
- **Endpoint :** `POST /api/v1/auth/refresh`
- **Description :** Obtenez un nouvel `access_token` en utilisant le `refresh_token`.
- **Corps de la requête :**
  ```json
  {
    "refresh_token": "votre_refresh_token_stocké"
  }
  ```
- **Action Frontend :** Si un appel API échoue avec un statut 401, utilisez cette route pour obtenir un nouveau token d'accès, mettez à jour le token stocké, puis réessayez la requête initiale.

---

## 3. Points de Terminaison pour l'Application Étudiant

- **Préfixe de base :** `/api/v1/student`

| Méthode | Route                               | Description                                     | Authentification |
|---------|-------------------------------------|-------------------------------------------------|------------------|
| `GET`   | `/profile`                          | Récupère le profil de l'étudiant connecté.      | Requise          |
| `PUT`   | `/profile`                          | Met à jour le profil de l'étudiant connecté.    | Requise          |
| `GET`   | `/courses`                          | Liste les cours auxquels l'étudiant est inscrit.| Requise          |
| `POST`  | `/courses/<course_id>/enroll`       | Inscrit l'étudiant à un cours spécifique.       | Requise          |
| `GET`   | `/assignments/<course_id>`          | Récupère les devoirs pour un cours spécifique.  | Requise          |
| `POST`  | `/assignments/submit`               | Soumet un devoir.                               | Requise          |
| `GET`   | `/progress/<course_id>`             | Récupère la progression de l'étudiant.          | Requise          |

---

## 4. Points de Terminaison pour l'Application Administrateur

- **Préfixe de base :** `/api/v1/admin`

| Méthode | Route                               | Description                                     | Authentification |
|---------|-------------------------------------|-------------------------------------------------|------------------|
| `GET`   | `/dashboard-data`                   | Récupère les statistiques du tableau de bord.   | Admin Requis     |
| `GET`   | `/students`                         | Liste tous les étudiants.                       | Admin Requis     |
| `POST`  | `/students`                         | Crée un nouvel étudiant.                        | Admin Requis     |
| `PUT`   | `/students/<student_id>`            | Met à jour un étudiant spécifique.              | Admin Requis     |
| `DELETE`| `/students/<student_id>`            | Supprime un étudiant spécifique.                | Admin Requis     |
| `GET`   | `/courses`                          | Liste tous les cours.                           | Admin Requis     |
| `POST`  | `/courses`                          | Crée un nouveau cours.                          | Admin Requis     |
| `PUT`   | `/courses/<course_id>`              | Met à jour un cours spécifique.                 | Admin Requis     |
| `DELETE`| `/courses/<course_id>`              | Supprime un cours spécifique.                   | Admin Requis     |
| `GET`   | `/instructors`                      | Liste tous les instructeurs.                    | Admin Requis     |
| `POST`  | `/instructors`                      | Crée un nouvel instructeur.                     | Admin Requis     |
| `DELETE`| `/instructors/<email>`              | Supprime un instructeur spécifique.             | Admin Requis     |

---

## 5. Points de Terminaison Publics

| Méthode | Route                   | Description                             | Authentification |
|---------|-------------------------|-----------------------------------------|------------------|
| `GET`   | `/api/v1/courses/`      | Liste tous les cours disponibles.       | Aucune           |
| `GET`   | `/api/v1/courses/<id>`  | Récupère les détails d'un cours.        | Aucune           |