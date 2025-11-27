"""
Database migration utilities.
"""

import logging
from typing import Dict, List
from datetime import datetime
from shared.database import get_database

logger = logging.getLogger(__name__)


class Migration:
    """Database migration."""
    
    def __init__(self, version: str, description: str, up_func: callable, down_func: callable = None):
        self.version = version
        self.description = description
        self.up_func = up_func
        self.down_func = down_func
        self.applied_at = None
    
    def up(self):
        """Apply migration."""
        logger.info(f"Applying migration {self.version}: {self.description}")
        self.up_func()
        self.applied_at = datetime.utcnow()
        logger.info(f"Migration {self.version} applied successfully")
    
    def down(self):
        """Rollback migration."""
        if self.down_func:
            logger.info(f"Rolling back migration {self.version}: {self.description}")
            self.down_func()
            logger.info(f"Migration {self.version} rolled back successfully")
        else:
            logger.warning(f"No rollback function for migration {self.version}")


class MigrationManager:
    """Manage database migrations."""
    
    def __init__(self, db_name: str = "market"):
        self.db = get_database()
        self.migrations_collection = self.db["_migrations"]
        self.migrations: List[Migration] = []
    
    def register(self, migration: Migration):
        """Register a migration."""
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.version)
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        applied = self.migrations_collection.find({}, {"version": 1})
        return [m["version"] for m in applied]
    
    def mark_applied(self, migration: Migration):
        """Mark migration as applied."""
        self.migrations_collection.insert_one({
            "version": migration.version,
            "description": migration.description,
            "applied_at": migration.applied_at or datetime.utcnow()
        })
    
    def mark_rolled_back(self, version: str):
        """Mark migration as rolled back."""
        self.migrations_collection.delete_one({"version": version})
    
    def migrate(self):
        """Apply all pending migrations."""
        applied = set(self.get_applied_migrations())
        
        for migration in self.migrations:
            if migration.version not in applied:
                try:
                    migration.up()
                    self.mark_applied(migration)
                except Exception as e:
                    logger.error(f"Failed to apply migration {migration.version}: {e}")
                    raise
    
    def rollback(self, version: str = None):
        """Rollback migrations."""
        applied = self.get_applied_migrations()
        
        if version:
            # Rollback specific migration
            for migration in reversed(self.migrations):
                if migration.version == version and migration.version in applied:
                    migration.down()
                    self.mark_rolled_back(version)
                    break
        else:
            # Rollback last migration
            if applied:
                last_version = applied[-1]
                for migration in reversed(self.migrations):
                    if migration.version == last_version:
                        migration.down()
                        self.mark_rolled_back(last_version)
                        break

