"""
Pydantic models for API request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class RecommendationType(str, Enum):
    """Type of recommendation request"""
    USER = "user"
    MOOD = "mood"
    ARTIST = "artist"
    RANDOM = "random"


class RecommendRequest(BaseModel):
    """Request for recommendations"""
    type: RecommendationType = Field(..., description="Type of recommendation")
    user_id: Optional[str] = Field(None, description="User ID for user-based recommendations")
    mood: Optional[str] = Field(None, description="Mood for mood-based recommendations")
    artist_name: Optional[str] = Field(None, description="Artist name for similar artist recommendations")
    k: int = Field(10, ge=1, le=50, description="Number of recommendations to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "mood",
                "mood": "heartbreak",
                "k": 10
            }
        }


class RecommendationItem(BaseModel):
    """Single recommendation item"""
    artist_name: str = Field(..., description="Artist name")
    score: float = Field(..., description="Recommendation score")
    rank: int = Field(..., description="Rank in recommendations (1-based)")


class RecommendResponse(BaseModel):
    """Response with recommendations"""
    recommendations: List[RecommendationItem]
    type: str = Field(..., description="Type of recommendation")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendations": [
                    {"artist_name": "Radiohead", "score": 0.85, "rank": 1},
                    {"artist_name": "Bon Iver", "score": 0.82, "rank": 2}
                ],
                "type": "mood",
                "metadata": {"mood": "heartbreak", "seed_artists": ["radiohead", "bon iver"]}
            }
        }


class SimilarArtistRequest(BaseModel):
    """Request for similar artists"""
    artist_name: str = Field(..., description="Artist name to find similar artists for")
    k: int = Field(10, ge=1, le=50, description="Number of similar artists to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "artist_name": "Radiohead",
                "k": 10
            }
        }


class SimilarArtistResponse(BaseModel):
    """Response with similar artists"""
    query_artist: str = Field(..., description="Artist that was queried")
    similar_artists: List[RecommendationItem]
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_artist": "Radiohead",
                "similar_artists": [
                    {"artist_name": "Muse", "score": 0.92, "rank": 1},
                    {"artist_name": "Arcade Fire", "score": 0.89, "rank": 2}
                ]
            }
        }


class ChartItem(BaseModel):
    """Single chart item"""
    artist_name: str = Field(..., description="Artist name")
    play_count: int = Field(..., description="Total play count")
    listener_count: int = Field(..., description="Number of unique listeners")
    rank: int = Field(..., description="Rank in charts (1-based)")


class ChartsResponse(BaseModel):
    """Response with top charts"""
    charts: List[ChartItem]
    total_artists: int = Field(..., description="Total number of artists in dataset")
    
    class Config:
        json_schema_extra = {
            "example": {
                "charts": [
                    {"artist_name": "The Beatles", "play_count": 1800000, "listener_count": 50000, "rank": 1}
                ],
                "total_artists": 126442
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    model_info: dict = Field(default_factory=dict, description="Model metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "model_loaded": True,
                "model_info": {
                    "n_users": 358622,
                    "n_artists": 126442,
                    "factors": 100
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Artist not found",
                "detail": "The artist 'Unknown Artist' is not in the dataset"
            }
        }
