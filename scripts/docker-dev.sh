#!/bin/bash
# scripts/docker-dev.sh

echo "🐳 Démarrage de l'environnement de développement Docker..."

# Vérifier que Docker est en cours d'exécution
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker n'est pas en cours d'exécution. Veuillez démarrer Docker."
    exit 1
fi

# Construire les images
echo "🔨 Construction des images Docker..."
docker-compose build

# Démarrer les services
echo "🚀 Démarrage des services..."
docker-compose up -d

# Attendre que la base de données soit prête
echo "⏳ Attente de la base de données..."
sleep 15

# Vérifier la santé des services
echo "🏥 Vérification de la santé des services..."
docker-compose ps

echo ""
echo "✅ Environnement prêt!"
echo "📖 Documentation API: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/health"
echo "🗄️  Base de données: localhost:5432"
echo ""
echo "📋 Commandes utiles:"
echo "  docker-compose logs -f talentbridge-api  # Logs API"
echo "  docker-compose logs -f talentbridge-db   # Logs DB"
echo "  docker-compose down                      # Arrêter"