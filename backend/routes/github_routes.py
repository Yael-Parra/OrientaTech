from fastapi import APIRouter, HTTPException
import httpx
from typing import List, Dict
from datetime import datetime

# Router para integración con GitHub
github_router = APIRouter(
    prefix="/github", 
    tags=["🐙 GitHub Integration"]
)

# Configuración
REPO = "Yael-Parra/OrientaTech"
API = "https://api.github.com"
DEV_BRANCH = "dev"

class GitHubService:
    """Servicio para obtener contribuidores de la rama dev"""
    
    async def get_dev_contributors(self) -> List[Dict]:
        """Obtener TODOS los contribuidores de la rama dev"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                contributors = {}
                page = 1
                per_page = 100
                
                while True:
                    # Obtener commits de la rama dev con paginación
                    response = await client.get(
                        f"{API}/repos/{REPO}/commits",
                        params={
                            "sha": DEV_BRANCH, 
                            "per_page": per_page,
                            "page": page
                        }
                    )
                    
                    if response.status_code != 200:
                        break
                        
                    commits = response.json()
                    
                    # Si no hay más commits, salir del bucle
                    if not commits or len(commits) == 0:
                        break
                    
                    # Procesar commits de esta página
                    for commit in commits:
                        author = commit.get("author")
                        if author and author.get("login"):
                            login = author.get("login")
                            if login not in contributors:
                                contributors[login] = {
                                    "name": login,
                                    "avatar_url": author.get("avatar_url"),
                                    "contributions": 0
                                }
                            contributors[login]["contributions"] += 1
                    
                    # Si recibimos menos commits que el máximo, es la última página
                    if len(commits) < per_page:
                        break
                        
                    page += 1
                    
                    # Límite de seguridad para evitar bucles infinitos
                    if page > 50:  # Máximo 5000 commits
                        break
                
                # Ordenar por número de contribuciones (descendente)
                return sorted(
                    contributors.values(), 
                    key=lambda x: x["contributions"], 
                    reverse=True
                )
        except Exception as e:
            print(f"Error obteniendo contribuidores de rama dev: {e}")
            return []

# Instancia del servicio
service = GitHubService()

@github_router.get("/contributors")
async def get_dev_contributors():
    """Obtener contribuidores de la rama dev"""
    contributors = await service.get_dev_contributors()
    
    if not contributors:
        raise HTTPException(404, "No se pudieron obtener los contribuidores de la rama dev")
    
    return {
        "repository": REPO,
        "branch": DEV_BRANCH,
        "contributors": contributors,
        "total": len(contributors),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "note": f"Contribuidores de la rama '{DEV_BRANCH}'"
    }