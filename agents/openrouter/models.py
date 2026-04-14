"""
OpenRouter Models Management
Fetch, filter, and manage available models from OpenRouter
"""
import aiohttp
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelInfo(BaseModel):
    """Model information from OpenRouter"""
    id: str = Field(..., description="Model ID (e.g., 'anthropic/claude-3.5-sonnet')")
    name: str = Field(..., description="Model display name")
    provider: str = Field(..., description="Provider name (e.g., 'anthropic', 'openai')")
    description: Optional[str] = Field(None, description="Model description")
    context_length: int = Field(..., description="Maximum context length")
    
    # Pricing (per 1M tokens)
    input_price: float = Field(..., description="Input price per 1M tokens (USD)")
    output_price: float = Field(..., description="Output price per 1M tokens (USD)")
    
    # Capabilities
    supports_tools: bool = Field(False, description="Supports tool/function calling")
    supports_reasoning: bool = Field(False, description="Supports reasoning/thinking")
    
    # Metadata
    knowledge_cutoff: Optional[str] = Field(None, description="Knowledge cutoff date")
    created: Optional[int] = Field(None, description="Model creation timestamp")
    
    # Additional info
    modality: Optional[str] = Field(None, description="Input/output modality")
    tokenizer: Optional[str] = Field(None, description="Tokenizer type")
    
    # Enable/disable
    enabled: bool = Field(True, description="Whether this model is enabled for use")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Anthropic: Claude 3.5 Sonnet",
                "provider": "anthropic",
                "description": "Claude 3.5 Sonnet...",
                "context_length": 200000,
                "input_price": 3.0,
                "output_price": 15.0,
                "supports_tools": True,
                "supports_reasoning": True,
                "knowledge_cutoff": "2024-04-30",
                "enabled": True
            }
        }


class OpenRouterModels:
    """Manage OpenRouter models"""
    
    API_URL = "https://openrouter.ai/api/v1/models"
    
    def __init__(self):
        """Initialize OpenRouter models manager"""
        self.models: List[ModelInfo] = []
        self.last_updated: Optional[datetime] = None
        self.db = None  # Will be initialized on first use
        
    def _ensure_db(self):
        """Ensure database is initialized"""
        if self.db is None:
            from agents.openrouter.database import get_models_database
            self.db = get_models_database()
    
    async def fetch_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """
        Fetch models from database or OpenRouter API
        
        Args:
            force_refresh: Force refresh from API even if database is fresh
            
        Returns:
            List of model information
        """
        self._ensure_db()
        
        # If models already loaded in memory and not forcing refresh, return cached
        if self.models and not force_refresh:
            logger.debug("Using in-memory cached models")
            return self.models
        
        # Check if we should use database
        if not force_refresh and not self.db.is_stale():
            logger.info("Loading models from database (fresh)")
            self.models = self.db.get_all_models()
            
            # Get last updated from database
            stats = self.db.get_stats()
            if stats.get("last_updated"):
                try:
                    self.last_updated = datetime.fromisoformat(stats["last_updated"])
                except:
                    pass
            
            return self.models
        
        # Database is stale or force refresh, fetch from API
        logger.info("Fetching models from OpenRouter API (database stale or force refresh)...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.API_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        models_data = data.get("data", [])
                        
                        self.models = []
                        for model_data in models_data:
                            try:
                                model_info = self._parse_model(model_data)
                                if model_info:
                                    self.models.append(model_info)
                            except Exception as e:
                                logger.warning(f"Error parsing model {model_data.get('id')}: {e}")
                        
                        # Save to database
                        self.db.save_models(self.models)
                        
                        self.last_updated = datetime.utcnow()
                        logger.info(f"Fetched and saved {len(self.models)} models to database")
                        return self.models
                    else:
                        logger.error(f"Error fetching models: HTTP {response.status}")
                        
                        # Fallback to database even if stale
                        logger.info("Falling back to database (stale)")
                        self.models = self.db.get_all_models()
                        return self.models
        
        except Exception as e:
            logger.error(f"Error fetching models from OpenRouter: {e}")
            
            # Fallback to database
            logger.info("Falling back to database due to error")
            self.models = self.db.get_all_models()
            return self.models
    
    def _parse_model(self, data: Dict[str, Any]) -> Optional[ModelInfo]:
        """
        Parse model data from OpenRouter API
        
        Args:
            data: Raw model data from API
            
        Returns:
            ModelInfo or None if parsing fails
        """
        try:
            # Extract pricing
            pricing = data.get("pricing", {})
            input_price = float(pricing.get("prompt", "0")) * 1_000_000  # Convert to per 1M tokens
            output_price = float(pricing.get("completion", "0")) * 1_000_000
            
            # Check capabilities
            supported_params = data.get("supported_parameters", [])
            supports_tools = "tools" in supported_params or "tool_choice" in supported_params
            supports_reasoning = "reasoning" in supported_params or "include_reasoning" in supported_params
            
            # Extract architecture info
            architecture = data.get("architecture", {})
            modality = architecture.get("modality", "")
            tokenizer = architecture.get("tokenizer", "")
            
            # Extract provider from model ID (e.g., "anthropic/claude-3.5-sonnet" -> "anthropic")
            model_id = data.get("id", "")
            provider = model_id.split("/")[0] if "/" in model_id else "unknown"
            
            return ModelInfo(
                id=model_id,
                name=data.get("name", ""),
                provider=provider,
                description=data.get("description", ""),
                context_length=data.get("context_length", 0),
                input_price=input_price,
                output_price=output_price,
                supports_tools=supports_tools,
                supports_reasoning=supports_reasoning,
                knowledge_cutoff=data.get("knowledge_cutoff"),
                created=data.get("created"),
                modality=modality,
                tokenizer=tokenizer,
                enabled=True  # Default enabled
            )
        
        except Exception as e:
            logger.error(f"Error parsing model data: {e}")
            return None
    
    def filter_models(
        self,
        require_tools: bool = False,
        require_reasoning: bool = False,
        min_context: Optional[int] = None,
        max_input_price: Optional[float] = None,
        max_output_price: Optional[float] = None,
        provider: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[ModelInfo]:
        """
        Filter models by criteria
        
        Args:
            require_tools: Only models that support tool calling
            require_reasoning: Only models that support reasoning
            min_context: Minimum context length
            max_input_price: Maximum input price per 1M tokens
            max_output_price: Maximum output price per 1M tokens
            provider: Filter by provider (e.g., 'anthropic', 'openai')
            enabled_only: Only return enabled models
            
        Returns:
            Filtered list of models
        """
        filtered = self.models
        
        # Filter by enabled status
        if enabled_only:
            filtered = [m for m in filtered if m.enabled]
        
        # Filter by tool support
        if require_tools:
            filtered = [m for m in filtered if m.supports_tools]
        
        # Filter by reasoning support
        if require_reasoning:
            filtered = [m for m in filtered if m.supports_reasoning]
        
        # Filter by context length
        if min_context:
            filtered = [m for m in filtered if m.context_length >= min_context]
        
        # Filter by pricing
        if max_input_price:
            filtered = [m for m in filtered if m.input_price <= max_input_price]
        
        if max_output_price:
            filtered = [m for m in filtered if m.output_price <= max_output_price]
        
        # Filter by provider
        if provider:
            filtered = [m for m in filtered if m.id.startswith(f"{provider}/")]
        
        return filtered
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get model by ID
        
        Args:
            model_id: Model ID
            
        Returns:
            ModelInfo or None
        """
        for model in self.models:
            if model.id == model_id:
                return model
        return None
    
    def enable_model(self, model_id: str):
        """Enable a model"""
        model = self.get_model(model_id)
        if model:
            model.enabled = True
            logger.info(f"Enabled model: {model_id}")
            
            # Update in database
            self._ensure_db()
            self.db.save_model(model)
    
    def disable_model(self, model_id: str):
        """Disable a model"""
        model = self.get_model(model_id)
        if model:
            model.enabled = False
            logger.info(f"Disabled model: {model_id}")
            
            # Update in database
            self._ensure_db()
            self.db.save_model(model)
    
    def get_enabled_models(self) -> List[ModelInfo]:
        """Get all enabled models"""
        return [m for m in self.models if m.enabled]
    
    def get_models_by_provider(self, enabled_only: bool = True) -> Dict[str, List[ModelInfo]]:
        """
        Group models by provider
        
        Args:
            enabled_only: Only include enabled models
            
        Returns:
            Dictionary with provider as key and list of models as value
        """
        models_to_group = self.get_enabled_models() if enabled_only else self.models
        
        grouped = {}
        for model in models_to_group:
            provider = model.provider
            if provider not in grouped:
                grouped[provider] = []
            grouped[provider].append(model)
        
        # Sort providers alphabetically
        return dict(sorted(grouped.items()))
    
    def get_providers(self) -> List[str]:
        """Get list of all providers"""
        providers = set(m.provider for m in self.models)
        return sorted(list(providers))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about models"""
        enabled = self.get_enabled_models()
        
        # Group by provider
        providers = {}
        for model in self.models:
            provider = model.provider
            if provider not in providers:
                providers[provider] = {
                    "total": 0,
                    "enabled": 0,
                    "with_tools": 0,
                    "with_reasoning": 0
                }
            providers[provider]["total"] += 1
            if model.enabled:
                providers[provider]["enabled"] += 1
            if model.supports_tools:
                providers[provider]["with_tools"] += 1
            if model.supports_reasoning:
                providers[provider]["with_reasoning"] += 1
        
        return {
            "total_models": len(self.models),
            "enabled_models": len(enabled),
            "disabled_models": len(self.models) - len(enabled),
            "models_with_tools": len([m for m in self.models if m.supports_tools]),
            "models_with_reasoning": len([m for m in self.models if m.supports_reasoning]),
            "providers": providers,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }


# Singleton instance
_openrouter_models: Optional[OpenRouterModels] = None


def get_openrouter_models() -> OpenRouterModels:
    """Get or create OpenRouterModels singleton"""
    global _openrouter_models
    if _openrouter_models is None:
        _openrouter_models = OpenRouterModels()
    return _openrouter_models
