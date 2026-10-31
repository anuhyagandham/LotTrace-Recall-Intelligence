"""
Command-line interface for LotTrace AI Synthetic Data Generator.
Usage:
    python -m src.generator --profile starter --seed 20261022
    python -m src.generator --profile full --seed 20261022
"""

import argparse
import sys
from config import DEFAULT_RANDOM_SEED
from src.generator.data_generator import DataGenerator
from src.utils.logging_config import logger


def main():
    parser = argparse.ArgumentParser(
        description="LotTrace AI Synthetic Supply Chain Data Generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--profile",
        choices=["starter", "full"],
        default="starter",
        help="Dataset profile scale ('starter' for quick dev/test, 'full' for production baseline)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Random seed for deterministic reproducibility",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Do not drop database tables prior to generation",
    )

    args = parser.parse_args()

    logger.info(f"Invoking LotTrace AI Data Generator [Profile: {args.profile}, Seed: {args.seed}]")
    try:
        generator = DataGenerator(profile_name=args.profile, seed=args.seed)
        counts = generator.run(reset_db=not args.no_reset)
        print("\n" + "=" * 60)
        print("LOTTRACE AI - DATA GENERATION SUMMARY")
        print("=" * 60)
        for entity, count in counts.items():
            print(f"  {entity:<25} : {count:>8} records")
        print("=" * 60)
        print(f"SUCCESS: Profile '{args.profile}' generated and verified.\n")
    except Exception as e:
        logger.exception(f"Data generation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
