# 🚀 Package de Déploiement Telegram Bot 3D - deploy234

## 📋 Contenu du Package
- `render_main.py` - Point d'entrée principal avec serveur web
- `predictor.py` - Moteur de prédiction avec règle stricte A/K/J/Q
- `scheduler.py` - Système de planification automatique
- `models.py` - Modèles de base de données
- `requirements.txt` - Dépendances Python
- `render.yaml` - Configuration Render.com

## ⚙️ Variables d'Environnement Requises
```
API_ID=29177661
API_HASH=a8639172fa8d35dbfd8ea46286d349ab
BOT_TOKEN=8442253971:AAEisYucgZ49Ej2b-mK9_6DhNrqh9WOc_XU
ADMIN_ID=1190237801
PORT=10000
```

## 🔧 Instructions Render.com
1. **Service Type**: Web Service
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `python render_main.py`
4. **Port**: 10000

## ✨ Format de Message
🔵{numéro}— 3D🔵 statut :⏳

## 🎯 Règle de Prédiction STRICTE
- **Premier groupe**: EXACTEMENT 2 cartes avec UNE SEULE carte de valeur (A,K,J,Q) + 1 chiffre
- **Deuxième groupe**: EXACTEMENT 2 cartes UNIQUEMENT avec des chiffres (0-15), AUCUNE carte de valeur
- Prédiction automatique pour le numéro suivant