import argparse

from . import commodity_prices


def main():
    parser = argparse.ArgumentParser(description="Run ingestion pipelines.")
    subparsers = parser.add_subparsers(dest="pipeline", required=True)

    commodity_parser = subparsers.add_parser(
        "commodity_prices", help="Ingest FAOSTAT commodity prices"
    )
    commodity_parser.add_argument(
        "--use-sample", action="store_true", help="Use local CSV sample instead of API."
    )

    args = parser.parse_args()

    if args.pipeline == "commodity_prices":
        commodity_prices.ingest(use_sample=args.use_sample)
    else:
        parser.error(f"Unknown pipeline {args.pipeline}")


if __name__ == "__main__":
    main()
