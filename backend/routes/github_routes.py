from fastapi import APIRouter, HTTPException
import httpx
import asyncio
import os
from typing import List, Dict, Optional
from datetime import datetime

# Router para integración con GitHub
github_router = APIRouter(
    prefix="/github", 
    tags=["🐙 GitHub Integration"],
    responses={
        500: {"description": "Error de conexión con GitHub API"},
        404: {"description": "Repositorio no encontrado"},
        403: {"description": "Rate limit de GitHub API excedido"}
    }
)

# Configuración de GitHub API
GITHUB_REPO_OWNER = "Yael-Parra"
GITHUB_REPO_NAME = "OrientaTech"
GITHUB_API_BASE = "https://api.github.com"

class GitHubService:
    """Servicio para interactuar con la API de GitHub"""
    
    def __init__(self):
        self.base_url = GITHUB_API_BASE
        self.repo_owner = GITHUB_REPO_OWNER
        self.repo_name = GITHUB_REPO_NAME
        self.repo_path = f"{self.repo_owner}/{self.repo_name}"
    
    async def get_contributors(self) -> List[Dict]:
        """
        Obtener información de contribuidores desde la API de GitHub
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Obtener contribuidores del repositorio
                contributors_url = f"{self.base_url}/repos/{self.repo_path}/contributors"
                contributors_response = await client.get(contributors_url)
                
                if contributors_response.status_code != 200:
                    return []
                
                contributors = contributors_response.json()
                detailed_contributors = []
                
                # Obtener información detallada de cada contribuidor
                for contributor in contributors:
                    user_url = f"{self.base_url}/users/{contributor['login']}"
                    user_response = await client.get(user_url)
                    
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        detailed_contributors.append({
                            "github_username": user_data.get("login"),
                            "name": user_data.get("name") or user_data.get("login"),
                            "avatar_url": user_data.get("avatar_url"),
                            "github_url": user_data.get("html_url"),
                            "bio": user_data.get("bio"),
                            "location": user_data.get("location"),
                            "company": user_data.get("company"),
                            "blog": user_data.get("blog"),
                            "public_repos": user_data.get("public_repos", 0),
                            "followers": user_data.get("followers", 0),
                            "following": user_data.get("following", 0),
                            "contributions": contributor.get("contributions", 0),
                            "type": user_data.get("type", "User"),
                            "created_at": user_data.get("created_at"),
                            "updated_at": user_data.get("updated_at")
                        })
                
                return detailed_contributors
                
        except Exception as e:
            print(f"Error obteniendo contribuidores de GitHub: {e}")
            return []

    async def get_repository_info(self) -> Optional[Dict]:
        """
        Obtener información del repositorio desde la API de GitHub
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                repo_url = f"{self.base_url}/repos/{self.repo_path}"
                response = await client.get(repo_url)
                
                if response.status_code != 200:
                    return None
                    
                repo_data = response.json()
                
                # Obtener información de ramas
                branches_url = f"{self.base_url}/repos/{self.repo_path}/branches"
                branches_response = await client.get(branches_url)
                branches = []
                if branches_response.status_code == 200:
                    branches = [branch["name"] for branch in branches_response.json()]
                
                # Obtener información de releases
                releases_url = f"{self.base_url}/repos/{self.repo_path}/releases"
                releases_response = await client.get(releases_url)
                releases = []
                if releases_response.status_code == 200:
                    releases_data = releases_response.json()
                    releases = [
                        {
                            "tag_name": release["tag_name"],
                            "name": release["name"],
                            "published_at": release["published_at"],
                            "prerelease": release["prerelease"]
                        }
                        for release in releases_data[:5]  # Solo los 5 más recientes
                    ]
                
                # Obtener información de commits recientes
                commits_url = f"{self.base_url}/repos/{self.repo_path}/commits"
                commits_response = await client.get(commits_url + "?per_page=10")
                recent_commits = []
                if commits_response.status_code == 200:
                    commits_data = commits_response.json()
                    recent_commits = [
                        {
                            "sha": commit["sha"][:7],
                            "message": commit["commit"]["message"].split('\n')[0],
                            "author": commit["commit"]["author"]["name"],
                            "date": commit["commit"]["author"]["date"],
                            "url": commit["html_url"]
                        }
                        for commit in commits_data
                    ]
                
                # Obtener lenguajes del repositorio
                languages_url = f"{self.base_url}/repos/{self.repo_path}/languages"
                languages_response = await client.get(languages_url)
                languages = {}
                if languages_response.status_code == 200:
                    languages = languages_response.json()
                
                return {
                    "name": repo_data.get("name"),
                    "full_name": repo_data.get("full_name"),
                    "description": repo_data.get("description"),
                    "html_url": repo_data.get("html_url"),
                    "clone_url": repo_data.get("clone_url"),
                    "ssh_url": repo_data.get("ssh_url"),
                    "language": repo_data.get("language"),
                    "languages": languages,
                    "size": repo_data.get("size"),
                    "stargazers_count": repo_data.get("stargazers_count", 0),
                    "forks_count": repo_data.get("forks_count", 0),
                    "watchers_count": repo_data.get("watchers_count", 0),
                    "open_issues_count": repo_data.get("open_issues_count", 0),
                    "created_at": repo_data.get("created_at"),
                    "updated_at": repo_data.get("updated_at"),
                    "pushed_at": repo_data.get("pushed_at"),
                    "default_branch": repo_data.get("default_branch"),
                    "branches": branches,
                    "recent_commits": recent_commits,
                    "releases": releases,
                    "topics": repo_data.get("topics", []),
                    "license": repo_data.get("license", {}).get("name") if repo_data.get("license") else None,
                    "private": repo_data.get("private", False)
                }
                
        except Exception as e:
            print(f"Error obteniendo información del repositorio: {e}")
            return None

    async def get_repository_stats(self) -> Dict:
        """
        Obtener estadísticas específicas del repositorio
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Obtener estadísticas de commits
                stats_url = f"{self.base_url}/repos/{self.repo_path}/stats/contributors"
                stats_response = await client.get(stats_url)
                
                contributor_stats = []
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    for stat in stats_data:
                        contributor_stats.append({
                            "author": stat["author"]["login"],
                            "total_commits": stat["total"],
                            "weeks_data": len(stat["weeks"])
                        })
                
                return {
                    "contributor_stats": contributor_stats,
                    "last_updated": datetime.utcnow().isoformat() + "Z"
                }
                
        except Exception as e:
            print(f"Error obteniendo estadísticas del repositorio: {e}")
            return {}

# Instancia del servicio
github_service = GitHubService()

@github_router.get(
    "/contributors",
    summary="Lista de contribuidores del repositorio",
    description="""
    **Obtener lista completa de contribuidores desde GitHub API.**
    """,
    response_description="Lista completa de contribuidores con información detallada"
)
async def get_contributors():
    """
    Obtener contribuidores del repositorio desde GitHub API
    """
    try:
        contributors = await github_service.get_contributors()
        
        if not contributors:
            raise HTTPException(
                status_code=404,
                detail="No se pudieron obtener los contribuidores del repositorio"
            )
        
        return {
            "repository": f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}",
            "total_contributors": len(contributors),
            "contributors": contributors,
            "api_info": {
                "source": "GitHub API",
                "endpoint": f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contributors",
                "last_fetch": datetime.utcnow().isoformat() + "Z"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno obteniendo contribuidores: {str(e)}"
        )

@github_router.get(
    "/repository",
    summary="Información completa del repositorio",
    description="""
    **Obtener información detallada del repositorio desde GitHub API.**
    """,
    response_description="Información completa del repositorio"
)
async def get_repository_info():
    """
    Obtener información del repositorio desde GitHub API
    """
    try:
        repo_info = await github_service.get_repository_info()
        
        if not repo_info:
            raise HTTPException(
                status_code=404,
                detail=f"No se pudo obtener información del repositorio {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"
            )
        
        return {
            "repository": repo_info,
            "api_info": {
                "source": "GitHub API",
                "endpoints_used": [
                    f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}",
                    f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/branches",
                    f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/commits",
                    f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases",
                    f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/languages"
                ],
                "last_fetch": datetime.utcnow().isoformat() + "Z"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno obteniendo información del repositorio: {str(e)}"
        )

@github_router.get(
    "/stats",
    summary="Estadísticas avanzadas del repositorio",
    description="""
    **Obtener estadísticas avanzadas del repositorio desde GitHub API.**
    """,
    response_description="Estadísticas avanzadas del repositorio"
)
async def get_repository_stats():
    """
    Obtener estadísticas avanzadas del repositorio
    """
    try:
        stats = await github_service.get_repository_stats()
        
        return {
            "repository": f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}",
            "stats": stats,
            "api_info": {
                "source": "GitHub API",
                "endpoint": f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/stats/contributors",
                "note": "Las estadísticas pueden tardar en generarse la primera vez",
                "last_fetch": datetime.utcnow().isoformat() + "Z"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas del repositorio: {str(e)}"
        )

@github_router.get(
    "/team",
    summary="Información del equipo con datos de GitHub",
    description="""
    **Combinar información del equipo con datos en tiempo real de GitHub.**
   """,
    response_description="Información completa del equipo con contexto académico y datos de GitHub"
)
async def get_team_info():
    """
    Obtener información completa del equipo combinando datos académicos y GitHub
    """
    try:
        # Obtener datos en paralelo
        contributors_task = github_service.get_contributors()
        repo_info_task = github_service.get_repository_info()
        
        contributors, repo_info = await asyncio.gather(
            contributors_task, 
            repo_info_task,
            return_exceptions=True
        )
        
        # Manejar errores en las tareas
        if isinstance(contributors, Exception):
            contributors = []
        if isinstance(repo_info, Exception):
            repo_info = None
        
        # Mapear roles específicos del equipo
        role_mapping = {
            "Yael-Parra": {
                "role": "Project Lead & Full Stack Developer",
                "contributions": [
                    "Arquitectura del proyecto",
                    "API de autenticación con FastAPI", 
                    "Integración con PostgreSQL",
                    "Documentación técnica",
                    "Configuración OAuth2 para Swagger",
                    "Integración con GitHub API"
                ],
                "skills": ["Python", "FastAPI", "PostgreSQL", "JWT", "Docker", "GitHub API"],
                "contact": "yael.parra@factoriaf5.org"
            }
            # Agregar más miembros del equipo aquí
        }
        
        # Procesar miembros del equipo
        team_members = []
        for contributor in contributors:
            username = contributor.get("github_username")
            team_config = role_mapping.get(username, {})
            
            team_member = {
                "name": contributor.get("name"),
                "github_username": username,
                "role": team_config.get("role", "Contributor"),
                "avatar_url": contributor.get("avatar_url"),
                "github_url": contributor.get("github_url"),
                "bio": contributor.get("bio"),
                "location": contributor.get("location"),
                "company": contributor.get("company"),
                "blog": contributor.get("blog"),
                "contributions_count": contributor.get("contributions"),
                "public_repos": contributor.get("public_repos"),
                "followers": contributor.get("followers"),
                "contributions": team_config.get("contributions", ["Contribuciones al proyecto"]),
                "skills": team_config.get("skills", ["Python", "FastAPI", "Git"]),
                "contact": team_config.get("contact", f"{username}@factoriaf5.org")
            }
            
            team_members.append(team_member)
        
        return {
            "project": {
                "name": "OrientaTech",
                "description": "API de autenticación y gestión de usuarios",
                "version": "1.0.0",
                "github_url": repo_info.get("html_url") if repo_info else f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}",
                "clone_url": repo_info.get("clone_url") if repo_info else None,
                "created_at": repo_info.get("created_at") if repo_info else None,
                "last_updated": datetime.utcnow().isoformat() + "Z"
            },
            "organization": {
                "name": "Factoría F5",
                "program": "Bootcamp de Desarrollo Web",
                "course": "Curso de Inteligencia Artificial",
                "type": "Proyecto Final",
                "location": "España"
            },
            "github_stats": {
                "stars": repo_info.get("stargazers_count", 0) if repo_info else 0,
                "forks": repo_info.get("forks_count", 0) if repo_info else 0,
                "watchers": repo_info.get("watchers_count", 0) if repo_info else 0,
                "open_issues": repo_info.get("open_issues_count", 0) if repo_info else 0,
                "size_kb": repo_info.get("size", 0) if repo_info else 0,
                "language": repo_info.get("language") if repo_info else "Python",
                "languages": repo_info.get("languages", {}) if repo_info else {},
                "default_branch": repo_info.get("default_branch", "main") if repo_info else "main",
                "branches": repo_info.get("branches", []) if repo_info else [],
                "recent_commits": repo_info.get("recent_commits", []) if repo_info else [],
                "releases": repo_info.get("releases", []) if repo_info else [],
                "topics": repo_info.get("topics", []) if repo_info else [],
                "license": repo_info.get("license") if repo_info else "MIT"
            },
            "team": team_members,
            "tech_stack": {
                "backend": ["Python 3.8+", "FastAPI", "PostgreSQL", "JWT", "BCrypt"],
                "frontend": ["HTML", "CSS", "JavaScript", "React (planificado)"],
                "tools": ["Git", "GitHub", "VS Code", "Docker", "Swagger UI"],
                "deployment": ["Uvicorn", "Gunicorn (producción)"],
                "apis": ["GitHub API", "OAuth2", "REST"]
            },
            "academic_info": {
                "institution": "Factoría F5",
                "course_duration": "6 meses",
                "focus_areas": [
                    "Desarrollo Full Stack",
                    "Inteligencia Artificial",
                    "APIs REST",
                    "Integración de APIs externas",
                    "Bases de datos relacionales",
                    "Metodologías ágiles"
                ],
                "learning_objectives": [
                    "Crear APIs robustas y seguras",
                    "Implementar autenticación JWT",
                    "Diseñar bases de datos relacionales",
                    "Integrar APIs externas (GitHub)",
                    "Aplicar mejores prácticas de desarrollo",
                    "Trabajo colaborativo con Git/GitHub"
                ]
            },
            "api_info": {
                "data_source": "GitHub API + configuración local",
                "last_fetch": datetime.utcnow().isoformat() + "Z",
                "contributors_count": len(contributors),
                "github_integration": True
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo información del equipo: {str(e)}"
        )