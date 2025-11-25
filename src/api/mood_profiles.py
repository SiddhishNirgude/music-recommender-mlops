"""
Mood Profiles Configuration
Maps moods to seed artists for recommendation generation
"""

MOOD_PROFILES = {
    "heartbreak": {
        "name": "Heartbreak 💔",
        "description": "For when you need to feel it all...",
        "seed_artists": ["radiohead", "bon iver", "elliott smith", "the smiths", "jeff buckley"]
    },
    "love": {
        "name": "Romance ❤️",
        "description": "Perfect for those in love",
        "seed_artists": ["arctic monkeys", "the xx", "vampire weekend", "beach house", "mazzy star"]
    },
    "feelgood": {
        "name": "Feel Good 😊",
        "description": "Uplifting and positive vibes",
        "seed_artists": ["the beatles", "coldplay", "phoenix", "mgmt", "vampire weekend"]
    },
    "rage": {
        "name": "Rage 🔥",
        "description": "Let it all out",
        "seed_artists": ["rage against the machine", "system of a down", "metallica", "slipknot", "tool"]
    },
    "motivation": {
        "name": "Motivation 💪",
        "description": "Get pumped up",
        "seed_artists": ["queen", "imagine dragons", "foo fighters", "linkin park", "muse"]
    },
    "party": {
        "name": "Party 🎉",
        "description": "Dance the night away",
        "seed_artists": ["daft punk", "calvin harris", "david guetta", "avicii", "deadmau5"]
    },
    "chill": {
        "name": "Chill 😌",
        "description": "Relax and unwind",
        "seed_artists": ["bonobo", "tycho", "zero 7", "air", "thievery corporation"]
    },
    "latenight": {
        "name": "Late Night 🌙",
        "description": "For those midnight hours",
        "seed_artists": ["the weeknd", "massive attack", "portishead", "fka twigs", "james blake"]
    },
    "rock": {
        "name": "Rock Out 🎸",
        "description": "Classic rock energy",
        "seed_artists": ["led zeppelin", "pink floyd", "the rolling stones", "ac/dc", "the who"]
    },
    "classical": {
        "name": "Classical 🎩",
        "description": "Timeless elegance",
        "seed_artists": ["ludovico einaudi", "yiruma", "ólafur arnalds", "max richter", "nils frahm"]
    },
    "jazz": {
        "name": "Jazz 🎷",
        "description": "Smooth and sophisticated",
        "seed_artists": ["miles davis", "john coltrane", "billie holiday", "ella fitzgerald", "chet baker"]
    },
    "focus": {
        "name": "Focus 📚",
        "description": "Concentration music",
        "seed_artists": ["ludovico einaudi", "max richter", "ólafur arnalds", "nils frahm", "explosions in the sky"]
    }
}


def get_mood_seed_artists(mood: str) -> list:
    """
    Get seed artists for a given mood
    
    Args:
        mood: Mood identifier (e.g., 'heartbreak', 'party')
        
    Returns:
        List of seed artist names (lowercase)
    """
    mood = mood.lower()
    if mood in MOOD_PROFILES:
        return MOOD_PROFILES[mood]["seed_artists"]
    return []


def get_all_moods() -> dict:
    """
    Get all available moods with metadata
    
    Returns:
        Dictionary of all mood profiles
    """
    return MOOD_PROFILES


def get_mood_info(mood: str) -> dict:
    """
    Get information about a specific mood
    
    Args:
        mood: Mood identifier
        
    Returns:
        Dictionary with mood information or None
    """
    mood = mood.lower()
    return MOOD_PROFILES.get(mood)
