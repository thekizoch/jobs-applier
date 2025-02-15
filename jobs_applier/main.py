# main.py
import argparse
from .config import Config
from .browser_automation import apply_to_jobs
from .logs import get_logger

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Jobs Applier CLI")

    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--keywords", type=str, help="Override config search keywords")
    parser.add_argument("--location", type=str, help="Override config search location")
    parser.add_argument("--max-applications", type=int, help="Max number of applications")

    args = parser.parse_args()

    config = Config(args.config)

    # If the user passed CLI args, override config
    if args.keywords:
        config.data.setdefault("search", {})["keywords"] = args.keywords
    if args.location:
        config.data.setdefault("search", {})["location"] = args.location
    if args.max_applications:
        config.data.setdefault("search", {})["max_applications"] = args.max_applications

    # Now run the main flow
    apply_to_jobs(config)

if __name__ == "__main__":
    main()
