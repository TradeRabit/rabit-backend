"""
OpenRouter Models Database
Persistent storage for models to avoid repeated API calls
"""
import json
import os
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
from pathlib import Path

from agents.openrouter.models import ModelInfo

logger = logging.getLogger(__name__)


class ModelsDatabase:
    """
    JSON-based database for OpenRouter models
    Stores models permanently to avoid repeated API calls
    """
    
    def __init__(self, db_path: str = "data/openrouter_models.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, dict] = {}
        self.metadata: Dict[str, any] = {}
        self.load()
        
    def load(self):
        """Load database from file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    db_content = json.load(f)
                    self.data = db_content.get("models", {})
                    self.metadata = db_content.get("metadata", {})
                logger.info(f"Loaded {len(self.data)} models from database")
            except Exception as e:
                logger.error(f"Error loading database: {e}")
                self.data = {}
                self.metadata = {}
        else:
            logger.info("Database file not found, starting fresh")
            self.data = {}
            self.metadata = {}
    
    def save(self):
        """Save database to file"""
        try:
            db_content = {
                "models": self.data,
                "metadata": self.metadata
            }
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(db_content, f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"Saved {len(self.data)} models to database")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get model from database
        
        Args:
            model_id: Model ID
            
        Returns:
            ModelInfo or None if not found
        """
        if model_id not in self.data:
            return None
        
        try:
            model_data = self.data[model_id]
            return ModelInfo(**model_data)
        except Exception as e:
            logger.error(f"Error parsing model {model_id}: {e}")
            return None
    
    def save_model(self, model: ModelInfo):
        """
        Save model to database
        
        Args:
            model: ModelInfo object to save
        """
        try:
            self.data[model.id] = model.model_dump(mode='json')
            logger.debug(f"Saved model: {model.id}")
        except Exception as e:
            logger.error(f"Error saving model {model.id}: {e}")
    
    def save_models(self, models: List[ModelInfo]):
        """
        Save multiple models to database
        
        Args:
            models: List of ModelInfo objects
        """
        for model in models:
            self.save_model(model)
        
        # Update metadata
        self.metadata["last_updated"] = datetime.utcnow().isoformat()
        self.metadata["total_models"] = len(self.data)
        
        self.save()
        logger.info(f"Saved {len(models)} models to database")
    
    def get_all_models(self) -> List[ModelInfo]:
        """Get all models from database"""
        models = []
        for model_id, model_data in self.data.items():
            try:
                model = ModelInfo(**model_data)
                models.append(model)
            except Exception as e:
                logger.error(f"Error parsing model {model_id}: {e}")
        return models
    
    def is_stale(self, max_age_days: int = 7) -> bool:
        """
        Check if database is stale and needs refresh
        
        Args:
            max_age_days: Maximum age in days before considering stale
            
        Returns:
            True if stale or empty, False if fresh
        """
        if not self.data:
            return True
        
        last_updated_str = self.metadata.get("last_updated")
        if not last_updated_str:
            return True
        
        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            age = datetime.utcnow() - last_updated
            return age > timedelta(days=max_age_days)
        except:
            return True
    
    def delete_model(self, model_id: str):
        """Delete model from database"""
        if model_id in self.data:
            del self.data[model_id]
            self.save()
            logger.info(f"Deleted model {model_id} from database")
    
    def clear(self):
        """Clear all data from database"""
        self.data = {}
        self.metadata = {}
        self.save()
        logger.info("Cleared database")
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        models = self.get_all_models()
        
        if not models:
            return {
                "total_models": 0,
                "last_updated": None,
                "is_stale": True
            }
        
        return {
            "total_models": len(models),
            "last_updated": self.metadata.get("last_updated"),
            "is_stale": self.is_stale(),
            "providers": len(set(m.provider for m in models)),
            "models_with_tools": len([m for m in models if m.supports_tools]),
            "models_with_reasoning": len([m for m in models if m.supports_reasoning])
        }


# Singleton instance
_models_database: Optional[ModelsDatabase] = None


def get_models_database(db_path: str = "data/openrouter_models.json") -> ModelsDatabase:
    """Get or create ModelsDatabase singleton"""
    global _models_database
    if _models_database is None:
        _models_database = ModelsDatabase(db_path)
    return _models_database
