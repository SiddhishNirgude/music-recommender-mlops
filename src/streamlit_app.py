"""
Music Recommender Streamlit Application
MLOps Project - End-to-End Music Recommendation System
"""

import streamlit as st
import requests
import pandas as pd
import json
import os
from typing import List, Dict, Optional
import time

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Music Recommender",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1DB954;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .mood-card {
        padding: 2rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
        margin-bottom: 1rem;
    }
    .mood-card:hover {
        transform: translateY(-5px);
    }
    .artist-card {
        padding: 1rem;
        border-radius: 8px;
        background: #f8f9fa;
        border-left: 4px solid #1DB954;
        margin-bottom: 0.5rem;
    }
    .profile-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: white;
        border: 2px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .stat-box {
        padding: 1rem;
        border-radius: 8px;
        background: #e8f5e9;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# Helper Functions
def call_api(endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
    """
    Call FastAPI endpoint
    
    Args:
        endpoint: API endpoint (e.g., "/health")
        method: HTTP method (GET or POST)
        data: Request data for POST
        
    Returns:
        Response JSON or None if error
    """
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=30)
        else:
            response = requests.post(url, json=data, timeout=30)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        st.info("Make sure FastAPI is running: `bash scripts/start_api.sh`")
        return None


def display_recommendations(recommendations: List[Dict], title: str = "Recommendations"):
    """Display recommendations in a nice format"""
    st.subheader(title)
    
    for rec in recommendations:
        col1, col2, col3 = st.columns([1, 4, 2])
        
        with col1:
            st.markdown(f"**#{rec['rank']}**")
        
        with col2:
            st.markdown(f"**{rec['artist_name'].title()}**")
        
        with col3:
            st.markdown(f"Score: `{rec['score']:.2f}`")
        
        st.divider()


# Page 1: Mood Recommendations
def page_mood_recommendations():
    """Mood-based recommendations page"""
    
    st.markdown('<p class="main-header">🎵 Music for Every Mood</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Discover music based on how you feel</p>', unsafe_allow_html=True)
    
    # Get available moods from API
    moods_data = call_api("/moods")
    
    if not moods_data:
        st.error("Could not load moods. Please check if API is running.")
        return
    
    moods = moods_data.get("moods", {})
    
    # Display mood cards in grid
    st.markdown("### Select Your Mood:")
    
    # Create 4 columns for mood cards
    mood_list = list(moods.items())
    
    for i in range(0, len(mood_list), 4):
        cols = st.columns(4)
        
        for j, col in enumerate(cols):
            if i + j < len(mood_list):
                mood_id, mood_info = mood_list[i + j]
                
                with col:
                    # Extract emoji from name (first character)
                    emoji = mood_info['name'].split()[0] if mood_info['name'] else "🎵"
                    mood_name = ' '.join(mood_info['name'].split()[1:]) if len(mood_info['name'].split()) > 1 else mood_info['name']
                    
                    if st.button(
                        f"{emoji}\n\n{mood_name}", 
                        key=f"mood_{mood_id}",
                        use_container_width=True
                    ):
                        st.session_state.selected_mood = mood_id
                        st.session_state.mood_name = mood_info['name']
                        st.session_state.mood_description = mood_info['description']
    
    # Display recommendations if mood selected
    if 'selected_mood' in st.session_state:
        st.markdown("---")
        
        mood_name = st.session_state.get('mood_name', 'Unknown')
        mood_desc = st.session_state.get('mood_description', '')
        
        st.markdown(f"## {mood_name}")
        st.markdown(f"*{mood_desc}*")
        
        # Number of recommendations
        k = st.slider("Number of recommendations:", 5, 20, 10)
        
        if st.button("🎧 Get Recommendations", type="primary"):
            with st.spinner("Finding perfect tracks for your mood..."):
                # Call API
                data = {
                    "type": "mood",
                    "mood": st.session_state.selected_mood,
                    "k": k
                }
                
                result = call_api("/recommend", method="POST", data=data)
                
                if result:
                    st.success(f"Found {len(result['recommendations'])} recommendations!")
                    
                    # Show seed artists
                    if 'metadata' in result and 'seed_artists' in result['metadata']:
                        seed_artists = result['metadata']['seed_artists']
                        st.info(f"Based on listeners who enjoy: {', '.join([a.title() for a in seed_artists])}")
                    
                    # Display recommendations
                    display_recommendations(result['recommendations'], "Your Playlist:")
        
        if st.button("← Back to Moods"):
            del st.session_state.selected_mood
            st.rerun()


# Page 2: Music Twins
def page_music_twins():
    """Music twin profiles page"""
    
    st.markdown('<p class="main-header">🎸 Find Your Music Twin</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Discover what listeners with similar taste enjoy</p>', unsafe_allow_html=True)
    
    # Pre-defined music twin profiles
    profiles = [
        {
            "name": "Rock Enthusiast",
            "icon": "🎸",
            "description": "Classic rock lover",
            "top_artists": ["The Beatles", "Pink Floyd", "Led Zeppelin"],
            "mood": "rock"
        },
        {
            "name": "Indie Explorer",
            "icon": "🎤",
            "description": "Alternative and indie vibes",
            "top_artists": ["Radiohead", "Arctic Monkeys", "Muse"],
            "mood": "feelgood"
        },
        {
            "name": "Party Animal",
            "icon": "🎉",
            "description": "Electronic and dance music",
            "top_artists": ["Daft Punk", "Calvin Harris", "Avicii"],
            "mood": "party"
        },
        {
            "name": "Chill Vibes",
            "icon": "😌",
            "description": "Relaxing and mellow",
            "top_artists": ["Bon Iver", "The xx", "Beach House"],
            "mood": "chill"
        },
        {
            "name": "Heartbreak Hotel",
            "icon": "💔",
            "description": "Emotional and deep",
            "top_artists": ["Radiohead", "Elliott Smith", "The Smiths"],
            "mood": "heartbreak"
        },
        {
            "name": "Motivation Machine",
            "icon": "💪",
            "description": "Get pumped up",
            "top_artists": ["Queen", "Imagine Dragons", "Muse"],
            "mood": "motivation"
        },
        {
            "name": "Jazz Connoisseur",
            "icon": "🎷",
            "description": "Smooth jazz lover",
            "top_artists": ["Miles Davis", "John Coltrane", "Billie Holiday"],
            "mood": "jazz"
        },
        {
            "name": "Classical Soul",
            "icon": "🎩",
            "description": "Timeless elegance",
            "top_artists": ["Ludovico Einaudi", "Max Richter", "Yiruma"],
            "mood": "classical"
        },
        {
            "name": "Late Night Owl",
            "icon": "🌙",
            "description": "Midnight melodies",
            "top_artists": ["The Weeknd", "Massive Attack", "FKA Twigs"],
            "mood": "latenight"
        },
        {
            "name": "Love Struck",
            "icon": "❤️",
            "description": "Romantic tunes",
            "top_artists": ["Arctic Monkeys", "The xx", "Vampire Weekend"],
            "mood": "love"
        }
    ]
    
    # Display profiles in grid
    for i in range(0, len(profiles), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(profiles):
                profile = profiles[i + j]
                
                with col:
                    with st.container():
                        st.markdown(f"### {profile['icon']} {profile['name']}")
                        st.markdown(f"*{profile['description']}*")
                        st.markdown(f"**Favorite Artists:** {', '.join(profile['top_artists'])}")
                        
                        if st.button(
                            "🎧 See Their Recommendations", 
                            key=f"profile_{i}_{j}",
                            use_container_width=True
                        ):
                            st.session_state.selected_profile = profile
    
    # Display recommendations if profile selected
    if 'selected_profile' in st.session_state:
        st.markdown("---")
        profile = st.session_state.selected_profile
        
        st.markdown(f"## {profile['icon']} {profile['name']}'s Playlist")
        st.markdown(f"*{profile['description']}*")
        
        k = st.slider("Number of recommendations:", 5, 20, 10, key="profile_k")
        
        if st.button("🎧 Get Recommendations", type="primary", key="profile_get"):
            with st.spinner(f"Finding what {profile['name']} would recommend..."):
                # Call API with profile's mood
                data = {
                    "type": "mood",
                    "mood": profile['mood'],
                    "k": k
                }
                
                result = call_api("/recommend", method="POST", data=data)
                
                if result:
                    st.success(f"Found {len(result['recommendations'])} recommendations!")
                    display_recommendations(result['recommendations'], "Playlist:")
        
        if st.button("← Back to Profiles"):
            del st.session_state.selected_profile
            st.rerun()


# Page 3: Explore (Artist Similarity, Charts, Random)
def page_explore():
    """Explore page with multiple features"""
    
    st.markdown('<p class="main-header">🔍 Explore Music</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Search artists, browse charts, or discover randomly</p>', unsafe_allow_html=True)
    
    # Tabs for different features
    tab1, tab2, tab3 = st.tabs(["🔍 Similar Artists", "📊 Top Charts", "🎲 Random Discovery"])
    
    # Tab 1: Artist Similarity
    with tab1:
        st.markdown("### Find Similar Artists")
        st.markdown("Enter an artist name to discover similar artists based on collaborative filtering")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            artist_name = st.text_input(
                "Artist name:",
                placeholder="e.g., Radiohead, The Beatles, Drake...",
                label_visibility="collapsed"
            )
        
        with col2:
            search_button = st.button("🔍 Search", use_container_width=True, type="primary")
        
        if search_button and artist_name:
            with st.spinner(f"Finding artists similar to {artist_name}..."):
                data = {
                    "artist_name": artist_name.lower(),
                    "k": 10
                }
                
                result = call_api("/similar", method="POST", data=data)
                
                if result:
                    st.success(f"Found similar artists to **{result['query_artist'].title()}**")
                    
                    st.markdown("### Similar Artists:")
                    for artist in result['similar_artists']:
                        col1, col2, col3 = st.columns([1, 4, 2])
                        
                        with col1:
                            st.markdown(f"**#{artist['rank']}**")
                        
                        with col2:
                            st.markdown(f"**{artist['artist_name'].title()}**")
                        
                        with col3:
                            similarity_pct = artist['score'] * 100
                            st.markdown(f"Similarity: `{similarity_pct:.1f}%`")
                        
                        st.divider()
    
    # Tab 2: Top Charts
    with tab2:
        st.markdown("### Top Charts")
        st.markdown("Most popular artists based on total play counts")
        
        k = st.selectbox("Show top:", [10, 20, 50, 100], index=1)
        
        if st.button("📊 Load Charts", type="primary"):
            with st.spinner("Loading charts..."):
                result = call_api(f"/charts?k={k}")
                
                if result:
                    st.success(f"Showing top {len(result['charts'])} artists")
                    
                    # Create dataframe for better display
                    charts_data = []
                    for chart in result['charts']:
                        charts_data.append({
                            "Rank": f"{'🏆' if chart['rank'] == 1 else '🥈' if chart['rank'] == 2 else '🥉' if chart['rank'] == 3 else chart['rank']}",
                            "Artist": chart['artist_name'].title(),
                            "Total Plays": f"{chart['play_count']:,}",
                            "Listeners": f"{chart['listener_count']:,}"
                        })
                    
                    df = pd.DataFrame(charts_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Tab 3: Random Discovery
    with tab3:
        st.markdown("### Random Discovery")
        st.markdown("Feeling adventurous? Get recommendations from a random listener!")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🎲 SURPRISE ME!", type="primary", use_container_width=True):
                with st.spinner("Picking a random music lover..."):
                    data = {
                        "type": "random",
                        "k": 10
                    }
                    
                    result = call_api("/recommend", method="POST", data=data)
                    
                    if result:
                        st.success("Here's what they're listening to!")
                        
                        if 'metadata' in result and 'random_user' in result['metadata']:
                            st.info(f"Random listener: {result['metadata']['random_user']}")
                        
                        display_recommendations(result['recommendations'], "Random Playlist:")


# Page 4: About
def page_about():
    """About page with system information"""
    
    st.markdown('<p class="main-header">ℹ️ About This System</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Music Recommendation System - MLOps Project</p>', unsafe_allow_html=True)
    
    # Get system health
    health = call_api("/health")
    
    if health:
        st.markdown("### 🎯 System Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_color = "🟢" if health.get('model_loaded') else "🔴"
            st.markdown(f"#### {status_color} Status")
            st.markdown(f"**{health.get('status', 'Unknown').upper()}**")
        
        with col2:
            st.markdown("#### 📊 Model")
            st.markdown(f"**{'Loaded' if health.get('model_loaded') else 'Not Loaded'}**")
        
        with col3:
            st.markdown("#### 🔢 Version")
            st.markdown("**1.0.0**")
        
        st.markdown("---")
        
        # Model information
        if 'model_info' in health:
            info = health['model_info']
            
            st.markdown("### 📊 Dataset Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Users", f"{info.get('n_users', 0):,}")
            
            with col2:
                st.metric("Total Artists", f"{info.get('n_artists', 0):,}")
            
            with col3:
                st.metric("Latent Factors", info.get('factors', 0))
        
        st.markdown("---")
    
    # System description
    st.markdown("### 🤖 How It Works")
    
    st.markdown("""
    This system uses **ALS (Alternating Least Squares) Collaborative Filtering** to generate personalized music recommendations.
    
    **Key Features:**
    - **Mood-Based Recommendations**: Get music based on your current mood
    - **Music Twin Profiles**: Discover what similar listeners enjoy
    - **Artist Similarity**: Find artists similar to your favorites
    - **Top Charts**: Browse the most popular artists
    - **Random Discovery**: Explore music from random listeners
    
    **How Recommendations Work:**
    1. The model analyzes listening patterns from 358K users
    2. It learns hidden patterns in 14M user-artist interactions
    3. It finds users with similar taste to you
    4. It recommends artists that similar users enjoy
    """)
    
    st.markdown("---")
    
    st.markdown("### 🛠️ MLOps Pipeline")
    
    st.markdown("""
    **End-to-End Data Science Solution:**
    
    ```
    Data (Last.fm) → DVC → Preprocessing → ALS Model → MLflow → FastAPI → Streamlit → You
    ```
    
    **Technologies Used:**
    - **Data Versioning**: DVC + AWS S3
    - **Model Training**: Implicit ALS
    - **Experiment Tracking**: MLflow
    - **Backend API**: FastAPI
    - **Frontend**: Streamlit
    - **Deployment**: Docker + Kubernetes
    - **Monitoring**: Prometheus + Grafana
    """)
    
    st.markdown("---")
    
    st.markdown("### 👥 Project Team")
    st.markdown("**MLOps Course Project** - Michigan State University")
    st.markdown("Built with ❤️ using Python, FastAPI, Streamlit, and ALS")


# Main App
def main():
    """Main application"""
    
    # Sidebar navigation
    st.sidebar.title("🎵 Music Recommender")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["🎭 Mood Recommendations", "🎸 Music Twins", "🔍 Explore", "ℹ️ About"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Links")
    st.sidebar.markdown("- [API Docs]({API_URL}/docs)")
    st.sidebar.markdown("- [GitHub Repo](#)")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("MLOps Project © 2025")
    
    # Route to pages
    if page == "🎭 Mood Recommendations":
        page_mood_recommendations()
    elif page == "🎸 Music Twins":
        page_music_twins()
    elif page == "🔍 Explore":
        page_explore()
    elif page == "ℹ️ About":
        page_about()


if __name__ == "__main__":
    main()
