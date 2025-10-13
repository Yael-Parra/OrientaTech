"""
Migration management system for OrientaTech
Allows applying migrations in order and tracking their status
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import List, Dict, Optional

# Add path to database modules
sys.path.append(os.path.dirname(__file__))

from .db_connection import connect, disconnect

class MigrationManager:
    """Database migration manager"""
    
    def __init__(self):
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.migrations_table = "schema_migrations"
    
    def create_migrations_table(self):
        """Creates table for tracking migrations"""
        conn = connect()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) UNIQUE NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum VARCHAR(64),
                    description TEXT
                );
            """)
            
            conn.commit()
            logger.success("✅ Migrations table created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating migrations table: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            disconnect(conn)
    
    def get_applied_migrations(self) -> List[str]:
        """Gets list of applied migrations"""
        conn = connect()
        if conn is None:
            return []
        
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"""
                SELECT version 
                FROM {self.migrations_table} 
                ORDER BY applied_at
            """)
            
            applied = [row[0] for row in cursor.fetchall()]
            return applied
            
        except Exception as e:
            logger.error(f"❌ Error getting applied migrations: {e}")
            return []
        finally:
            cursor.close()
            disconnect(conn)
    
    def get_available_migrations(self) -> List[Dict]:
        """Gets list of available migrations"""
        if not self.migrations_dir.exists():
            return []
        
        migrations = []
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            # Extract version from filename (e.g., "001_initial.sql" -> "001")
            version = file_path.stem.split('_')[0]
            migrations.append({
                'version': version,
                'filename': file_path.name,
                'path': file_path,
                'description': file_path.stem.replace(f"{version}_", "").replace("_", " ").title()
            })
        
        return migrations
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculates file checksum"""
        import hashlib
        
        with open(file_path, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()
    
    def apply_migration(self, migration: Dict) -> bool:
        """Applies single migration"""
        logger.info(f"📄 Applying migration: {migration['filename']}")
        
        conn = connect()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        
        try:
            # Read SQL file
            with open(migration['path'], 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Execute SQL
            cursor.execute(sql_content)
            
            # Calculate checksum
            checksum = self.calculate_checksum(migration['path'])
            
            # Record migration info
            cursor.execute(f"""
                INSERT INTO {self.migrations_table} 
                (version, filename, checksum, description)
                VALUES (%s, %s, %s, %s)
            """, (
                migration['version'],
                migration['filename'],
                checksum,
                migration['description']
            ))
            
            conn.commit()
            logger.success(f"✅ Migration {migration['filename']} applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error applying migration {migration['filename']}: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            disconnect(conn)
    
    def run_migrations(self, target_version: Optional[str] = None) -> bool:
        """Runs all unapplied migrations"""
        logger.info("🚀 Starting migration system...")
        
        # Create migrations table if not exists
        if not self.create_migrations_table():
            return False
        
        # Get migration lists
        applied_migrations = self.get_applied_migrations()
        available_migrations = self.get_available_migrations()
        
        logger.info(f"📊 Applied migrations: {len(applied_migrations)}")
        logger.info(f"📊 Available migrations: {len(available_migrations)}")
        
        # Find migrations to apply
        migrations_to_apply = []
        for migration in available_migrations:
            if migration['version'] not in applied_migrations:
                if target_version is None or migration['version'] <= target_version:
                    migrations_to_apply.append(migration)
        
        if not migrations_to_apply:
            logger.success("✅ All migrations already applied")
            return True
        
        logger.info(f"📋 Migrations to apply: {len(migrations_to_apply)}")
        
        # Apply migrations
        success_count = 0
        for migration in migrations_to_apply:
            if self.apply_migration(migration):
                success_count += 1
            else:
                logger.error(f"❌ Stopped due to error in migration {migration['filename']}")
                break
        
        logger.info(f"📊 Successfully applied: {success_count}/{len(migrations_to_apply)} migrations")
        
        return success_count == len(migrations_to_apply)
    
    def rollback_migration(self, version: str) -> bool:
        """Rolls back migration (removes record from table)"""
        logger.warning(f"⚠️ Rolling back migration {version}")
        
        conn = connect()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"""
                DELETE FROM {self.migrations_table} 
                WHERE version = %s
            """, (version,))
            
            conn.commit()
            logger.success(f"✅ Migration {version} rolled back")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error rolling back migration {version}: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            disconnect(conn)
    
    def get_migration_status(self) -> Dict:
        """Gets migration status"""
        applied = self.get_applied_migrations()
        available = self.get_available_migrations()
        
        status = {
            'applied_count': len(applied),
            'available_count': len(available),
            'pending_count': len(available) - len(applied),
            'applied_migrations': applied,
            'available_migrations': [m['version'] for m in available],
            'pending_migrations': [m['version'] for m in available if m['version'] not in applied]
        }
        
        return status
    
    def print_status(self):
        """Prints migration status"""
        status = self.get_migration_status()
        
        logger.info("📊 MIGRATION STATUS")
        logger.info("="*50)
        logger.info(f"Applied: {status['applied_count']}")
        logger.info(f"Available: {status['available_count']}")
        logger.info(f"Pending: {status['pending_count']}")
        
        if status['applied_migrations']:
            logger.info("\n✅ Applied migrations:")
            for version in status['applied_migrations']:
                logger.info(f"   - {version}")
        
        if status['pending_migrations']:
            logger.info("\n⏳ Pending migrations:")
            for version in status['pending_migrations']:
                logger.info(f"   - {version}")

def main():
    """Main function to run migrations"""
    manager = MigrationManager()
    
    # Show status
    manager.print_status()
    
    # Run migrations
    if manager.run_migrations():
        logger.success("🎉 All migrations applied successfully!")
    else:
        logger.error("❌ Error applying migrations")

if __name__ == "__main__":
    main()
