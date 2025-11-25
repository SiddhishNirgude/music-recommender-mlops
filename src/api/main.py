"""
FastAPI Application for Music Recommender System
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from .models import (
    RecommendRequest,
    RecommendResponse,
    RecommendationItem,
    SimilarArtistRequest,
    SimilarArtistResponse,
    ChartsResponse,
    ChartItem,
    HealthResponse,
    ErrorResponse,
    RecommendationType
)
from .recommender import RecommenderService
from .mood_profiles import get_all_moods, get_mood_info

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global recommender service
recommender = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI"""
    global recommender
    
    # Startup
    logger.info("🚀 Starting Music Recommender API...")
    try:
        recommender = RecommenderService()
        logger.info("✅ Recommender service loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load recommender: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Music Recommender API...")


# Create FastAPI app
app = FastAPI(
    title="Music Recommender API",
    description="ALS-based music recommendation system with mood profiles, artist similarity, and more",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Music Recommender API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "recommend": "/recommend",
            "similar": "/similar",
            "charts": "/charts",
            "moods": "/moods"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Returns service status and model information
    """
    try:
        model_info = recommender.get_model_info()
        
        return HealthResponse(
            status="healthy",
            model_loaded=True,
            model_info=model_info
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.post("/recommend", response_model=RecommendResponse, tags=["Recommendations"])
async def get_recommendations(request: RecommendRequest):
    """
    Get recommendations based on different criteria
    
    Supports:
    - User-based: Get recommendations for a specific user
    - Mood-based: Get recommendations based on mood
    - Random: Get recommendations for a random user
    """
    try:
        recommendations = []
        metadata = {}
        
        if request.type == RecommendationType.USER:
            if not request.user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="user_id is required for user-based recommendations"
                )
            
            recs = recommender.get_recommendations_by_user(request.user_id, k=request.k)
            recommendations = [
                RecommendationItem(artist_name=artist, score=score, rank=i+1)
                for i, (artist, score) in enumerate(recs)
            ]
            metadata = {"user_id": request.user_id[:20] + "..."}
        
        elif request.type == RecommendationType.MOOD:
            if not request.mood:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="mood is required for mood-based recommendations"
                )
            
            recs, seed_artists = recommender.get_recommendations_by_mood(request.mood, k=request.k)
            recommendations = [
                RecommendationItem(artist_name=artist, score=score, rank=i+1)
                for i, (artist, score) in enumerate(recs)
            ]
            
            mood_info = get_mood_info(request.mood)
            metadata = {
                "mood": request.mood,
                "mood_name": mood_info["name"] if mood_info else request.mood,
                "seed_artists": seed_artists
            }
        
        elif request.type == RecommendationType.RANDOM:
            recs, user_id = recommender.get_random_recommendations(k=request.k)
            recommendations = [
                RecommendationItem(artist_name=artist, score=score, rank=i+1)
                for i, (artist, score) in enumerate(recs)
            ]
            metadata = {"random_user": user_id[:20] + "..."}
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported recommendation type: {request.type}"
            )
        
        return RecommendResponse(
            recommendations=recommendations,
            type=request.type.value,
            metadata=metadata
        )
    
    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )


@app.post("/similar", response_model=SimilarArtistResponse, tags=["Recommendations"])
async def get_similar_artists(request: SimilarArtistRequest):
    """
    Get similar artists based on collaborative filtering
    
    Uses artist embedding vectors to find similar artists
    """
    try:
        similar = recommender.get_similar_artists(request.artist_name, k=request.k)
        
        similar_artists = [
            RecommendationItem(artist_name=artist, score=score, rank=i+1)
            for i, (artist, score) in enumerate(similar)
        ]
        
        return SimilarArtistResponse(
            query_artist=request.artist_name,
            similar_artists=similar_artists
        )
    
    except ValueError as e:
        logger.warning(f"Artist not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error finding similar artists: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding similar artists: {str(e)}"
        )


@app.get("/charts", response_model=ChartsResponse, tags=["Charts"])
async def get_charts(k: int = 20):
    """
    Get top charts (most popular artists)
    
    Returns artists sorted by total play count
    """
    try:
        if k < 1 or k > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="k must be between 1 and 100"
            )
        
        charts = recommender.get_top_charts(k=k)
        
        chart_items = [
            ChartItem(
                artist_name=artist,
                play_count=plays,
                listener_count=listeners,
                rank=i+1
            )
            for i, (artist, plays, listeners) in enumerate(charts)
        ]
        
        return ChartsResponse(
            charts=chart_items,
            total_artists=len(recommender.artist_mapping)
        )
    
    except Exception as e:
        logger.error(f"Error getting charts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting charts: {str(e)}"
        )


@app.get("/moods", tags=["Metadata"])
async def get_moods():
    """
    Get all available mood profiles
    
    Returns list of moods with their metadata
    """
    try:
        moods = get_all_moods()
        return {"moods": moods}
    except Exception as e:
        logger.error(f"Error getting moods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting moods: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
