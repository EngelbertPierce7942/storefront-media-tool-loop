import argparse

from media_service import MediaRequest, run_media_loop


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--creator-email", required=True, help="Recipient email address")
    args = parser.parse_args()
    request = MediaRequest(asset_id="lookbook-42", storefront="northwind", creator_email=args.creator_email)
    print(run_media_loop(request).model_dump_json())
