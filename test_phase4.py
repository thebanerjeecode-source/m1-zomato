import os
import sys
from pathlib import Path

# Setup paths so we can import phase4 modules
root_dir = Path(__file__).parent.resolve()
sys.path.append(str(root_dir))

# Load .env variables
env_path = root_dir / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k] = v

from phase4.app import recommend, UIRequest

def test():
    print("Testing phase4 live example...")
    # Input is Bellandur, Budget is 2000 (mapping to high), rating is 4.0
    req = UIRequest(
        location="Bellandur",
        cuisine="any", # cuisine is required by UIRequest
        budget="high", # mapping 2000 to "high"
        min_rating=4.0,
        top_n=5
    )
    print(f"Request: {req}")
    
    try:
        resp = recommend(req)
        print("\nResponse:")
        print(f"Used LLM: {resp.used_llm}")
        print(f"Model: {resp.model}")
        if resp.warnings:
            print("Warnings:")
            for w in resp.warnings:
                print(f" - {w}")
        
        print(f"\nTop {len(resp.recommendations)} Recommendations:")
        for i, rec in enumerate(resp.recommendations, 1):
            name = rec.get("name", "Unknown")
            rating = rec.get("rating", "N/A")
            cost = rec.get("cost", "N/A")
            cuisines = rec.get("cuisines", [])
            explanation = rec.get("explanation", "No explanation")
            print(f"{i}. {name} - Rating: {rating}, Cost: {cost}, Cuisines: {cuisines}")
            print(f"   Explanation from LLM: {explanation}\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
