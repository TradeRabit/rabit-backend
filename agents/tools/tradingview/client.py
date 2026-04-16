"""WebView client for TradingView chart communication"""
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class TradingViewClient:
    """Client for communicating with TradingView chart via HTTP"""
    
    def __init__(self, base_url: str = "http://localhost:3001"):
        """
        Initialize TradingView client
        
        Args:
            base_url: Base URL of TradingView API server (default: http://localhost:3001)
        """
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=15)
    
    async def send_command(
        self, 
        command: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send command to TradingView chart
        
        Args:
            command: Command name
            params: Command parameters
            
        Returns:
            Response from chart with normalized error handling
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                payload = {
                    "type": "COMMAND",
                    "command": command,
                    "params": params or {}
                }
                
                logger.debug(f"Sending command {command} with params: {params}")
                
                async with session.post(
                    f"{self.base_url}/api/chart",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Command {command} executed successfully")
                        return data
                    elif response.status == 404:
                        logger.error(f"API endpoint not found: {self.base_url}/api/chart")
                        return {
                            "success": False,
                            "error": "API endpoint not found. Make sure the API server is running on port 3001",
                            "command": command,
                            "suggestion": "Start the API server: cd Rabit-mobile/assets/charting/advanced-charts && npm run api"
                        }
                    elif response.status == 500:
                        error_text = await response.text()
                        logger.error(f"Server error for command {command}: {error_text}")
                        return {
                            "success": False,
                            "error": f"Server error: {error_text}",
                            "command": command,
                            "suggestion": "Check the API server logs for details"
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Command {command} failed with status {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "command": command
                        }
        
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Cannot connect to TradingView at {self.base_url}: {str(e)}")
            return {
                "success": False,
                "error": f"Cannot connect to TradingView API server at {self.base_url}",
                "command": command,
                "details": str(e),
                "suggestion": "Make sure both servers are running:\n1. Chart server: npm start (port 3000)\n2. API server: npm run api (port 3001)"
            }
        
        except asyncio.TimeoutError:
            logger.error(f"Command {command} timed out after {self.timeout.total} seconds")
            return {
                "success": False,
                "error": f"Command timed out after {self.timeout.total} seconds",
                "command": command,
                "suggestion": "The chart may be loading or processing. Wait a few seconds and try again"
            }
        
        except aiohttp.ContentTypeError as e:
            logger.error(f"Invalid response format for command {command}: {str(e)}")
            return {
                "success": False,
                "error": "Invalid response format from server",
                "command": command,
                "details": str(e),
                "suggestion": "The API server may be returning HTML instead of JSON. Check if the server is running correctly"
            }
        
        except Exception as e:
            logger.error(f"Unexpected error sending command {command}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "command": command,
                "error_type": type(e).__name__,
                "suggestion": "Check the logs for more details"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if TradingView API server is accessible
        
        Returns:
            Health check result with detailed status
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        logger.info("TradingView API server is healthy")
                        return {
                            "success": True,
                            "status": "healthy",
                            "message": "TradingView API server is accessible",
                            "url": self.base_url
                        }
                    else:
                        logger.warning(f"TradingView API server returned status {response.status}")
                        return {
                            "success": False,
                            "status": "unhealthy",
                            "message": f"Server returned status {response.status}",
                            "url": self.base_url,
                            "suggestion": "Check if the API server is running correctly"
                        }
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Cannot connect to TradingView API server: {str(e)}")
            return {
                "success": False,
                "status": "unreachable",
                "message": f"Cannot connect to {self.base_url}",
                "details": str(e),
                "suggestion": "Start the API server: cd Rabit-mobile/assets/charting/advanced-charts && npm run api"
            }
        except asyncio.TimeoutError:
            logger.error("Health check timed out")
            return {
                "success": False,
                "status": "timeout",
                "message": "Health check timed out",
                "url": self.base_url,
                "suggestion": "The server may be overloaded or not responding"
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "success": False,
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "url": self.base_url
            }


# Global client instance
_client = None


def get_client() -> TradingViewClient:
    """Get or create TradingView client singleton"""
    global _client
    if _client is None:
        _client = TradingViewClient()
    return _client
