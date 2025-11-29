"""
Traffic Generator for Music Recommender API

Simulates realistic user traffic to generate metrics for monitoring dashboard.
Runs continuously and sends varied requests to the API.
"""

import requests
import random
import time
import sys
from typing import List
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
REQUESTS_PER_MINUTE = 30  # Target: 30 requests/minute (1 every 2 seconds)

# Sample data
MOODS = [
    "heartbreak", "love", "feelgood", "rage", "motivation",
    "party", "chill", "latenight", "rock", "classical", "jazz", "focus"
]

ARTISTS = [
    "radiohead", "the beatles", "coldplay", "pink floyd", "muse",
    "queen", "nirvana", "led zeppelin", "the rolling stones",
    "metallica", "david bowie", "u2", "red hot chili peppers"
]

# Weight moods realistically (some more popular than others)
MOOD_WEIGHTS = {
    "heartbreak": 0.15,
    "party": 0.12,
    "chill": 0.12,
    "feelgood": 0.10,
    "love": 0.08,
    "rock": 0.08,
    "motivation": 0.07,
    "latenight": 0.07,
    "jazz": 0.06,
    "rage": 0.05,
    "classical": 0.05,
    "focus": 0.05
}


class TrafficGenerator:
    """Generate realistic API traffic"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()
    
    def get_stats(self):
        """Get current statistics"""
        elapsed = time.time() - self.start_time
        rpm = (self.request_count / elapsed) * 60 if elapsed > 0 else 0
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            "total_requests": self.request_count,
            "errors": self.error_count,
            "elapsed_seconds": elapsed,
            "requests_per_minute": rpm,
            "error_rate_percent": error_rate
        }
    
    def make_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        self.request_count += 1
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=10, **kwargs)
            elif method == "POST":
                response = requests.post(url, timeout=10, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            self.error_count += 1
            print(f"❌ Error: {e}")
            return None
    
    def mood_recommendation(self):
        """Request mood-based recommendation"""
        mood = random.choices(list(MOOD_WEIGHTS.keys()), 
                             weights=list(MOOD_WEIGHTS.values()))[0]
        k = random.choice([5, 10, 15, 20])
        
        return self.make_request(
            "POST",
            "/recommend",
            json={"type": "mood", "mood": mood, "k": k}
        )
    
    def random_recommendation(self):
        """Request random user recommendation"""
        k = random.choice([10, 15, 20])
        
        return self.make_request(
            "POST",
            "/recommend",
            json={"type": "random", "k": k}
        )
    
    def similar_artist(self):
        """Request similar artists"""
        artist = random.choice(ARTISTS)
        k = random.choice([5, 10])
        
        return self.make_request(
            "POST",
            "/similar",
            json={"artist_name": artist, "k": k}
        )
    
    def get_charts(self):
        """Request top charts"""
        k = random.choice([10, 20, 50])
        
        return self.make_request(
            "GET",
            f"/charts?k={k}"
        )
    
    def health_check(self):
        """Health check request"""
        return self.make_request("GET", "/health")
    
    def simulate_user_session(self):
        """Simulate a realistic user session"""
        # User typically does 3-6 actions per session
        actions = random.randint(3, 6)
        
        for _ in range(actions):
            # Weighted random choice of action
            action_type = random.choices(
                ["mood", "similar", "charts", "random", "health"],
                weights=[0.45, 0.25, 0.15, 0.10, 0.05]
            )[0]
            
            if action_type == "mood":
                self.mood_recommendation()
            elif action_type == "similar":
                self.similar_artist()
            elif action_type == "charts":
                self.get_charts()
            elif action_type == "random":
                self.random_recommendation()
            elif action_type == "health":
                self.health_check()
            
            # Short delay between actions (0.5-2 seconds)
            time.sleep(random.uniform(0.5, 2.0))
        
        # Longer delay between sessions (2-5 seconds)
        time.sleep(random.uniform(2.0, 5.0))


def print_stats(generator: TrafficGenerator):
    """Print current statistics"""
    stats = generator.get_stats()
    
    print("\n" + "="*60)
    print(f"📊 Traffic Generator Statistics")
    print("="*60)
    print(f"Total Requests:      {stats['total_requests']}")
    print(f"Errors:              {stats['errors']}")
    print(f"Elapsed Time:        {stats['elapsed_seconds']:.1f}s")
    print(f"Requests/Minute:     {stats['requests_per_minute']:.1f}")
    print(f"Error Rate:          {stats['error_rate_percent']:.2f}%")
    print("="*60 + "\n")


def main():
    """Main traffic generation loop"""
    print("\n🚀 Starting Traffic Generator")
    print(f"Target: {REQUESTS_PER_MINUTE} requests/minute")
    print(f"API URL: {API_BASE_URL}")
    print("\nPress Ctrl+C to stop\n")
    
    generator = TrafficGenerator()
    
    # Check if API is accessible
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        print(f"✅ API is accessible (status: {response.status_code})\n")
    except Exception as e:
        print(f"❌ Cannot reach API: {e}")
        print("Make sure the API is running on http://localhost:8000")
        sys.exit(1)
    
    # Calculate delay between requests
    delay_seconds = 60.0 / REQUESTS_PER_MINUTE
    
    try:
        iteration = 0
        while True:
            iteration += 1
            
            # Simulate user session
            generator.simulate_user_session()
            
            # Print stats every 50 requests
            if generator.request_count % 50 == 0:
                print_stats(generator)
            
            # Show progress
            if iteration % 10 == 0:
                stats = generator.get_stats()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Requests: {stats['total_requests']}, "
                      f"RPM: {stats['requests_per_minute']:.1f}, "
                      f"Errors: {stats['errors']}")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping traffic generator...")
        print_stats(generator)
        print("✅ Generator stopped\n")


if __name__ == "__main__":
    main()
