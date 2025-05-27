# === COMMANDES DOCKER ===

docker-build: ## Build les images Docker
	docker-compose build
	@echo "✅ Images Docker construites!"

docker-up: ## Démarre tous les services avec Docker
	docker-compose up -d
	@echo "✅ TalentBridge démarré avec Docker!"
	@echo "🗄️  PostgreSQL: localhost:5432"
	@echo "🚀 API FastAPI: http://localhost:8000"
	@echo "📖 Documentation: http://localhost:8000/docs"

docker-down: ## Arrête tous les services Docker
	docker-compose down
	@echo "🛑 TalentBridge arrêté!"

docker-logs: ## Affiche les logs de tous les services
	docker-compose logs -f

docker-logs-api: ## Affiche les logs de l'API
	docker-compose logs -f talentbridge-api

docker-logs-db: ## Affiche les logs de PostgreSQL
	docker-compose logs -f talentbridge-db

docker-restart: ## Redémarre tous les services Docker
	docker-compose restart
	@echo "🔄 TalentBridge redémarré!"

docker-clean: ## Supprime containers, volumes et images
	docker-compose down -v --rmi all
	docker system prune -f
	@echo "🧹 Nettoyage Docker terminé!"

docker-shell-api: ## Ouvre un shell dans le container API
	docker-compose exec talentbridge-api bash

docker-shell-db: ## Ouvre un shell PostgreSQL
	docker-compose exec talentbridge-db psql -U talentbridge_user -d talentbridge

docker-rebuild: ## Rebuild complet
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d
	@echo "🔄 Rebuild complet terminé!"

# === COMMANDES COMBINÉES ===

docker-dev-setup: ## Setup complet Docker pour développement
	@echo "🐳 Configuration Docker complète..."
	docker-compose build
	docker-compose up -d
	@echo "⏳ Attente de la base de données..."
	@sleep 15
	@echo "✅ Environnement Docker prêt!"
	@echo ""
	@echo "🎉 Accès aux services:"
	@echo "   📖 API Documentation: http://localhost:8000/docs"
	@echo "   🏥 Health Check: http://localhost:8000/health"
	@echo "   🗄️  Base de données: localhost:5432"