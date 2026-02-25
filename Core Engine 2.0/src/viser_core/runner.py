import argparse, json, sys
from pathlib import Path
from typing import Dict, Any
from loguru import logger

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
# Add Core Engine root for settings
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from viser_core.ai_planner import AIPlanner, compare
from viser_core.intent_router import infer_intent
from viser_core.executor import run, run_with_browser_use_sync

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="", help="Target URL (required for execution)")
    ap.add_argument("--request", required=True)
    ap.add_argument("--provider", default="groq", choices=["groq","gemini","compare"])
    ap.add_argument("--dry", action="store_true", help="Plan only; do not execute")
    args = ap.parse_args()

    logger.info(f"intent={infer_intent(args.request)} provider={args.provider}")
    if args.provider == "compare":
        results = compare(args.request, args.url)
        print(json.dumps(results, indent=2))
        return

    planner = AIPlanner(args.provider)
    
    # Use detailed step-by-step planning for all providers with URL
    plan = planner.plan(args.request, args.url)
    print(json.dumps(plan, indent=2))
    
    if args.dry or plan.get("error") or not args.url:
        return
    
    # Execute with traditional steps for all providers
    run(args.url, plan.get("steps", []))

if __name__ == "__main__":
    main()