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

class GitHubService:
    """Servicio simplificado para GitHub API"""
    
    async def get_contributors(self) -> List[Dict]:
        """Obtener solo nombres de contribuidores"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{API}/repos/{REPO}/contributors")
                if response.status_code == 200:
                    contributors = response.json()
                    return [
                        {
                            "name": contrib.get("login"),
                            "avatar_url": contrib.get("avatar_url"),
                            "contributions": contrib.get("contributions", 0)
                        }
                        for contrib in contributors
                    ]
                return []
        except Exception:
            return []

# Instancia del servicio
service = GitHubService()

@github_router.get("/contributors")
async def get_contributors():
    """Obtener contribuidores del repositorio"""
    contributors = await service.get_contributors()
    if not contributors:
        raise HTTPException(404, "No se pudieron obtener los contribuidores")
    
    return {
        "repository": REPO,
        "contributors": contributors,
        "total": len(contributors),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }