# Package Déploiement 2026 - Support YAML Intégré

## ✨ Nouvelles Fonctionnalités 2026:
• Configuration YAML persistante (prediction.yaml inclus)
• Commande /intervalle (1-60 minutes) - Actuel: 1min
• Gestion automatique des erreurs de dépendances
• Support psycopg2 pour base de données PostgreSQL
• Health check endpoint intégré

## 🔧 Variables Render.com (Obligatoires):
```env
API_ID=29177661
API_HASH=votre_hash
BOT_TOKEN=votre_token
ADMIN_ID=1190237801
PORT=10000
PREDICTION_INTERVAL=1
USE_YAML_CONFIG=true
```

## 📋 Configuration Render.com:
- Build Command: pip install -r requirements.txt
- Start Command: python render_main.py
- Health Check: /health
- Port: 10000 (automatique)

## 🎯 Commandes Disponibles:
/intervalle [minutes] - Configurer délai prédiction
/status - État complet avec configuration YAML
/deploy - Générer ce package normé 2026

## 🚀 Déploiement:
1. Extraire deploy2026.zip
2. Upload sur votre repo Git
3. Connecter à Render.com
4. Configurer les variables d'environnement
5. Déployer!

✅ Package testé et optimisé pour Render.com
🔄 Support YAML intégré pour la persistance des données
📊 Système de prédictions avec planification automatique

Développé par Sossou Kouamé Appolinaire - Version 2026