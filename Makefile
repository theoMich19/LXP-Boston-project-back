# TalentBridge - Commandes Docker et Backend

.PHONY: help start stop restart logs clean db-reset dev-setup dev-start dev-format dev-lint dev-test dev-install

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === COMMANDES DOCKER ===

start: ## Démarre tous les services
	docker-compose up -d
	@echo "✅ TalentBridge démarré!"
	@echo "🗄️  PostgreSQL: localhost:5432"

stop: ## Arrête tous les services
	docker-compose down
	@echo "🛑 TalentBridge arrêté!"

restart: ## Redémarre tous les services
	docker-compose restart
	@echo "🔄 TalentBridge redémarré!"

logs: ## Affiche les logs
	docker-compose logs -f

logs-db: ## Affiche les logs de PostgreSQL
	docker-compose logs -f talentbridge-db

status: ## Affiche le statut des services
	docker-compose ps

clean: ## Supprime les containers et volumes
	docker-compose down -v
	docker system prune -f
	@echo "🧹 Nettoyage terminé!"

db-reset: ## Recrée la base de données
	@echo "🗄️  Réinitialisation de la base de données..."
	docker-compose down -v
	docker volume prune -f
	docker-compose up -d talentbridge-db
	@echo "⏳ Attente de l'initialisation..."
	@sleep 10
	@echo "✅ Base de données réinitialisée!"

backup: ## Sauvegarde la base de données
	@mkdir -p backups
	docker-compose exec talentbridge-db pg_dump -U talentbridge_user talentbridge > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "💾 Sauvegarde créée dans backups/"

psql: ## Se connecte à PostgreSQL
	docker-compose exec talentbridge-db psql -U talentbridge_user -d talentbridge

# === COMMANDES BACKEND PYTHON ===

dev-setup: ## Configure l'environnement de développement Python
	@echo "🐍 Configuration de l'environnement Python..."
	python -m venv venv
	@echo "📦 Installation des dépendances..."
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install "fastapi[all]" uvicorn[standard] sqlalchemy psycopg2-binary alembic python-dotenv pydantic-settings black flake8 isort pytest pytest-asyncio
	./venv/bin/pip freeze > requirements.txt
	@echo "✅ Environnement Python configuré!"
	@echo "💡 N'oublie pas d'activer l'environnement: source venv/bin/activate"

dev-install: ## Installe les dépendances Python (avec venv activé)
	@if [ ! -d "venv" ]; then echo "❌ Environnement virtuel non trouvé. Lance 'make dev-setup' d'abord."; exit 1; fi
	@echo "📦 Installation des dépendances..."
	pip install -r requirements.txt
	@echo "✅ Dépendances installées!"

dev-start: ## Démarre le serveur de développement FastAPI
	@if [ ! -d "venv" ]; then echo "❌ Environnement virtuel non trouvé. Lance 'make dev-setup' d'abord."; exit 1; fi
	@echo "🚀 Démarrage du serveur FastAPI..."
	@echo "📖 Documentation disponible sur: http://localhost:8000/docs"
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-format: ## Formate le code Python avec Black et isort
	@if [ ! -d "venv" ]; then echo "❌ Environnement virtuel non trouvé. Lance 'make dev-setup' d'abord."; exit 1; fi
	@echo "🔧 Formatage du code..."
	black app/ && isort app/
	@echo "✅ Code formaté!"

dev-lint: ## Vérifie le code avec flake8
	@if [ ! -d "venv" ]; then echo "❌ Environnement virtuel non trouvé. Lance 'make dev-setup' d'abord."; exit 1; fi
	@echo "🔍 Vérification du code..."
	flake8 app/
	@echo "✅ Vérification terminée!"

dev-test: ## Lance les tests Python
	@if [ ! -d "venv" ]; then echo "❌ Environnement virtuel non trouvé. Lance 'make dev-setup' d'abord."; exit 1; fi
	@echo "🧪 Lancement des tests..."
	pytest tests/ -v
	@echo "✅ Tests terminés!"

dev-check: ## Lance format + lint + test en une commande
	@echo "🔄 Vérification complète du code..."
	make dev-format
	make dev-lint
	make dev-test
	@echo "✅ Vérification complète terminée!"

dev-clean: ## Supprime l'environnement virtuel Python
	@echo "🧹 Suppression de l'environnement virtuel..."
	rm -rf venv
	rm -f requirements.txt
	@echo "✅ Environnement virtuel supprimé!"

# === COMMANDES COMBINÉES ===

dev: ## Démarre la DB et le serveur de développement
	@echo "🚀 Démarrage de l'environnement de développement complet..."
	make start
	@echo "⏳ Attente de la base de données..."
	@sleep 5
	make dev-start

dev-full-setup: ## Setup complet pour un nouveau développeur
	@echo "🎯 Configuration complète de l'environnement de développement..."
	make dev-setup
	make start
	@echo "⏳ Attente de la base de données..."
	@sleep 10
	@echo "✅ Environnement de développement prêt!"
	@echo ""
	@echo "🎉 Pour commencer le développement:"
	@echo "   1. Active l'environnement: source venv/bin/activate"
	@echo "   2. Lance le serveur: make dev-start"
	@echo "   3. Visite: http://localhost:8000/docs"