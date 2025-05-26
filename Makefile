# TalentBridge - Commandes Docker et Backend

.PHONY: help start stop restart logs clean db-reset dev-setup dev-start dev-format dev-lint dev-test dev-install db-init db-status

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === COMMANDES DOCKER ===

start: ## Démarre tous les services avec init DB automatique
	@echo "🚀 Démarrage de TalentBridge..."
	docker-compose up -d
	@echo "⏳ Attente de l'initialisation de la base de données..."
	@make db-wait
	@echo "✅ TalentBridge démarré!"
	@echo "🗄️  PostgreSQL: localhost:${DB_PORT:-5432}"
	@echo "📊 Base de données: ${DB_NAME:-talentbridge}"

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

# === COMMANDES BASE DE DONNÉES ===

db-reset: ## Recrée la base de données complètement
	@echo "🗄️  Réinitialisation complète de la base de données..."
	@echo "⚠️  Cela va supprimer TOUTES les données!"
	@read -p "Êtes-vous sûr? (y/N): " confirm && [ "$$confirm" = "y" ]
	docker-compose down -v
	docker volume prune -f
	@echo "🚀 Redémarrage avec nouvelle base..."
	docker-compose up -d talentbridge-db
	@make db-wait
	@echo "✅ Base de données réinitialisée avec succès!"

db-wait: ## Attend que la base de données soit prête
	@echo "⏳ Vérification de la disponibilité de PostgreSQL..."
	@timeout=60; \
	while [ $$timeout -gt 0 ]; do \
		if docker-compose exec -T talentbridge-db pg_isready -U ${DB_USER:-talentbridge_user} -d ${DB_NAME:-talentbridge} >/dev/null 2>&1; then \
			echo "✅ PostgreSQL est prêt!"; \
			break; \
		fi; \
		echo "⏳ Attente... ($$timeout secondes restantes)"; \
		sleep 2; \
		timeout=$$((timeout-2)); \
	done; \
	if [ $$timeout -le 0 ]; then \
		echo "❌ Timeout: PostgreSQL n'est pas prêt"; \
		exit 1; \
	fi

db-status: ## Vérifie le statut de la base de données
	@echo "📊 Statut de la base de données:"
	@docker-compose exec talentbridge-db pg_isready -U ${DB_USER:-talentbridge_user} -d ${DB_NAME:-talentbridge} && echo "✅ Base accessible" || echo "❌ Base inaccessible"
	@echo "📋 Tables présentes:"
	@docker-compose exec -T talentbridge-db psql -U ${DB_USER:-talentbridge_user} -d ${DB_NAME:-talentbridge} -c "\dt" 2>/dev/null || echo "❌ Impossible de lister les tables"

db-init: ## Force la réexécution du script d'initialisation
	@echo "🔄 Réexécution du script d'initialisation..."
	@if [ ! -f "./db/init/01-init.sql" ]; then \
		echo "❌ Fichier db/init/01-init.sql introuvable!"; \
		exit 1; \
	fi
	docker-compose exec -T talentbridge-db psql -U ${DB_USER:-talentbridge_user} -d ${DB_NAME:-talentbridge} -f /docker-entrypoint-initdb.d/01-init.sql
	@echo "✅ Script d'initialisation exécuté!"

backup: ## Sauvegarde la base de données
	@mkdir -p backups
	@echo "💾 Création de la sauvegarde..."
	docker-compose exec -T talentbridge-db pg_dump -U ${DB_USER:-talentbridge_user} ${DB_NAME:-talentbridge} > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Sauvegarde créée dans backups/"

restore: ## Restaure une sauvegarde (usage: make restore BACKUP=fichier.sql)
	@if [ -z "$(BACKUP)" ]; then \
		echo "❌ Usage: make restore BACKUP=backup_20240101_120000.sql"; \
		exit 1; \
	fi
	@if [ ! -f "backups/$(BACKUP)" ]; then \
		echo "❌ Fichier backups/$(BACKUP) introuvable!"; \
		exit 1; \
	fi
	@echo "🔄 Restauration de backups/$(BACKUP)..."
	docker-compose exec -T talentbridge-db psql -U ${DB_USER:-talentbridge_user} -d ${DB_NAME:-talentbridge} < backups/$(BACKUP)
	@echo "✅ Restauration terminée!"

psql: ## Se connecte à PostgreSQL
	docker-compose exec talentbridge-db psql -U ${DB_USER:-talentbridge_user} -d ${DB_NAME:-talentbridge}

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
	./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-format: ## Formate le code Python avec Black et isort
	@if [ ! -d "venv" ]; then echo "❌ Environnement virtuel non trouvé. Lance 'make dev-setup' d'abord."; exit 1; fi
	@echo "🔧 Formatage du code..."
	./venv/bin/black app/ && ./venv/bin/isort app/
	@echo "✅ Code formaté!"

dev-lint: ## Vérifie le code avec flake8
	@if [ ! -d "venv" ]; then echo "❌ Environnement virtuel non trouvé. Lance 'make dev-setup' d'abord."; exit 1; fi
	@echo "🔍 Vérification du code..."
	./venv/bin/flake8 app/
	@echo "✅ Vérification terminée!"

dev-test: ## Lance les tests Python
	@if [ ! -d "venv" ]; then echo "❌ Environnement virtuel non trouvé. Lance 'make dev-setup' d'abord."; exit 1; fi
	@echo "🧪 Lancement des tests..."
	./venv/bin/pytest tests/ -v
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
	@make db-wait
	make dev-start

dev-full-setup: ## Setup complet pour un nouveau développeur
	@echo "🎯 Configuration complète de l'environnement de développement..."
	@if [ ! -f ".env" ]; then \
		echo "⚠️  Fichier .env manquant! Copie .env.example vers .env et configure-le."; \
		exit 1; \
	fi
	make dev-setup
	make start
	@echo "⏳ Attente de l'initialisation complète..."
	@make db-wait
	@make db-status
	@echo "✅ Environnement de développement prêt!"
	@echo ""
	@echo "🎉 Pour commencer le développement:"
	@echo "   1. Active l'environnement: source venv/bin/activate"
	@echo "   2. Lance le serveur: make dev-start"
	@echo "   3. Visite: http://localhost:8000/docs"

# === COMMANDES DE VÉRIFICATION ===

check-env: ## Vérifie la configuration
	@echo "🔍 Vérification de la configuration..."
	@if [ ! -f ".env" ]; then echo "❌ Fichier .env manquant!"; exit 1; fi
	@if [ ! -f "db/init/01-init.sql" ]; then echo "❌ Script d'initialisation manquant!"; exit 1; fi
	@echo "✅ Configuration OK!"

first-run: ## Premier lancement complet (avec vérifications)
	@echo "🎯 Premier lancement de TalentBridge..."
	make check-env
	make clean
	make start
	@make db-status
	@echo "🎉 TalentBridge est prêt à l'emploi!"