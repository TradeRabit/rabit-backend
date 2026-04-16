"""
Crypto Category Utilities
Standardize and normalize crypto project categories
"""
from typing import List, Set, Dict


# Standard category mappings (CoinGecko -> Standardized)
CATEGORY_MAPPINGS = {
    # Layer 1 Blockchains
    "layer 1": "Layer 1",
    "layer-1": "Layer 1",
    "l1": "Layer 1",
    "smart contract platform": "Layer 1",
    "platform": "Layer 1",
    
    # Layer 2 Solutions
    "layer 2": "Layer 2",
    "layer-2": "Layer 2",
    "l2": "Layer 2",
    "ethereum ecosystem": "Layer 2",
    "scaling": "Layer 2",
    "rollup": "Layer 2",
    "optimistic rollup": "Layer 2",
    "zk rollup": "Layer 2",
    "zero knowledge": "Layer 2",
    
    # DeFi
    "defi": "DeFi",
    "decentralized finance": "DeFi",
    "decentralized exchange": "DeFi",
    "dex": "DeFi",
    "automated market maker": "DeFi",
    "amm": "DeFi",
    "lending": "DeFi",
    "yield farming": "DeFi",
    "liquid staking": "DeFi",
    "staking": "DeFi",
    
    # Infrastructure
    "infrastructure": "Infrastructure",
    "oracle": "Infrastructure",
    "data": "Infrastructure",
    "storage": "Infrastructure",
    "decentralized storage": "Infrastructure",
    "indexing": "Infrastructure",
    "rpc": "Infrastructure",
    "node": "Infrastructure",
    
    # AI & Machine Learning
    "ai": "AI",
    "artificial intelligence": "AI",
    "machine learning": "AI",
    "ai agent": "AI Agent",
    "ai agents": "AI Agent",
    "autonomous agents": "AI Agent",
    
    # Gaming & Metaverse
    "gaming": "Gaming",
    "gamefi": "Gaming",
    "play to earn": "Gaming",
    "metaverse": "Metaverse",
    "virtual reality": "Metaverse",
    "vr": "Metaverse",
    
    # NFT & Digital Art
    "nft": "NFT",
    "non-fungible token": "NFT",
    "collectibles": "NFT",
    "digital art": "NFT",
    
    # Privacy
    "privacy": "Privacy",
    "privacy coins": "Privacy",
    "zero knowledge": "Privacy",
    "zk": "Privacy",
    
    # Meme Coins
    "meme": "Meme",
    "meme coin": "Meme",
    "memes": "Meme",
    "dog themed": "Meme",
    
    # Stablecoins
    "stablecoin": "Stablecoin",
    "stablecoins": "Stablecoin",
    "algorithmic stablecoin": "Stablecoin",
    
    # Exchange Tokens
    "exchange": "Exchange Token",
    "centralized exchange": "Exchange Token",
    "cex": "Exchange Token",
    
    # Real World Assets
    "rwa": "RWA",
    "real world assets": "RWA",
    "tokenized assets": "RWA",
    
    # Social
    "social": "Social",
    "socialfi": "Social",
    "social media": "Social",
    
    # Derivatives
    "derivatives": "Derivatives",
    "perpetuals": "Derivatives",
    "options": "Derivatives",
    "futures": "Derivatives",
}


# Primary categories (most important)
PRIMARY_CATEGORIES = {
    "Layer 1",
    "Layer 2",
    "DeFi",
    "Infrastructure",
    "AI",
    "AI Agent",
    "Gaming",
    "Metaverse",
    "NFT",
    "Privacy",
    "Meme",
    "Stablecoin",
    "Exchange Token",
    "RWA",
    "Social",
    "Derivatives"
}


def normalize_category(category: str) -> str:
    """
    Normalize a category string to standard format
    
    Args:
        category: Raw category string from CoinGecko
        
    Returns:
        Standardized category name
    """
    if not category:
        return ""
    
    # Convert to lowercase for matching
    category_lower = category.lower().strip()
    
    # Check if we have a mapping
    if category_lower in CATEGORY_MAPPINGS:
        return CATEGORY_MAPPINGS[category_lower]
    
    # Return original with title case if no mapping
    return category.strip().title()


def normalize_categories(categories: List[str]) -> List[str]:
    """
    Normalize a list of categories
    
    Args:
        categories: List of raw category strings
        
    Returns:
        List of standardized category names (deduplicated)
    """
    if not categories:
        return []
    
    normalized = set()
    for cat in categories:
        norm = normalize_category(cat)
        if norm:
            normalized.add(norm)
    
    return sorted(list(normalized))


def get_primary_category(categories: List[str]) -> str:
    """
    Get the primary (most important) category from a list
    Priority order matches PRIMARY_CATEGORIES definition order
    
    Args:
        categories: List of categories
        
    Returns:
        Primary category or "Other"
    """
    if not categories:
        return "Other"
    
    # Normalize first
    normalized = normalize_categories(categories)
    
    # Define priority order (most important first)
    priority_order = [
        "Layer 1",
        "Layer 2",
        "DeFi",
        "AI Agent",  # AI Agent before Infrastructure
        "AI",
        "Infrastructure",
        "Gaming",
        "Metaverse",
        "NFT",
        "Privacy",
        "Meme",
        "Stablecoin",
        "Exchange Token",
        "RWA",
        "Social",
        "Derivatives"
    ]
    
    # Find first category in priority order
    for priority_cat in priority_order:
        if priority_cat in normalized:
            return priority_cat
    
    # Return first category if no primary found
    return normalized[0] if normalized else "Other"


def filter_by_category(category: str, categories: List[str]) -> bool:
    """
    Check if a coin belongs to a specific category
    
    Args:
        category: Category to check for
        categories: List of coin's categories
        
    Returns:
        True if coin belongs to category
    """
    normalized = normalize_categories(categories)
    target = normalize_category(category)
    return target in normalized


def get_category_stats(coins_data: List[Dict]) -> Dict[str, int]:
    """
    Get statistics about category distribution
    
    Args:
        coins_data: List of coin data with 'categories' field
        
    Returns:
        Dictionary with category counts
    """
    stats = {}
    
    for coin in coins_data:
        categories = coin.get("categories", [])
        normalized = normalize_categories(categories)
        
        for cat in normalized:
            stats[cat] = stats.get(cat, 0) + 1
    
    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))


def get_coins_by_category(category: str, coins_data: List[Dict]) -> List[Dict]:
    """
    Filter coins by category
    
    Args:
        category: Category to filter by
        coins_data: List of coin data with 'categories' field
        
    Returns:
        List of coins in that category
    """
    target = normalize_category(category)
    
    return [
        coin for coin in coins_data
        if target in normalize_categories(coin.get("categories", []))
    ]


def get_all_categories() -> List[str]:
    """
    Get all standard categories
    
    Returns:
        Sorted list of all standard categories
    """
    return sorted(list(PRIMARY_CATEGORIES))


def is_primary_category(category: str) -> bool:
    """
    Check if a category is a primary category
    
    Args:
        category: Category to check
        
    Returns:
        True if primary category
    """
    normalized = normalize_category(category)
    return normalized in PRIMARY_CATEGORIES
