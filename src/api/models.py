"""
Pydantic Models for FastAPI

Request and response models for all endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class RecommendRequest(BaseModel):
    """Request model for recommendations"""
    type: str = Field(..., description="Type of recommendation: mood, user, or random")
    mood: Optional[str] = Field(None, description="Mood name for mood-based recommendations")
    user_id: Optional[int] = Field(None, description="User ID for user-based recommendations")
    k: int = Field(10, description="Number of recommendations to return", ge=1, le=50)


class RecommendationItem(BaseModel):
    """Single recommendation item"""
    artist_name: str
    score: float
    rank: int


class RecommendResponse(BaseModel):
    """Response model for recommendations"""
    recommendations: List[RecommendationItem]
    type: str
    metadata: Dict[str, Any]


class SimilarArtistRequest(BaseModel):
    """Request model for similar artists"""
    artist_name: str = Field(..., description="Name of the artist")
    k: int = Field(10, description="Number of similar artists to return", ge=1, le=50)


class SimilarArtistItem(BaseModel):
    """Single similar artist item"""
    artist_name: str
    score: float
    rank: int


class SimilarArtistResponse(BaseModel):
    """Response model for similar artists"""
    query_artist: str
    similar_artists: List[SimilarArtistItem]


class ChartItem(BaseModel):
    """Single chart item"""
    artist_name: str
    play_count: int
    listener_count: int
    rank: int


class ChartsResponse(BaseModel):
    """Response model for top charts"""
    charts: List[ChartItem]


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    model_loaded: bool
    model_info: Dict[str, int]


class MoodsResponse(BaseModel):
    """Response model for available moods"""
    moods: Dict[str, Dict[str, Any]]
