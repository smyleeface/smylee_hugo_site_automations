"""Main CLI for the blog post image generator."""

import json
import logging
import os

import boto3
import click
from github import Github

import hugo_site.blog_post_image_generator.app as app

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGGING_LEVEL", logging.INFO))


@click.command()
@click.option("--repository-name", required=True, help="The repository name")
@click.option(
    "--pull-request-number", required=True, help="The pull request number", type=int
)
@click.option("--image-temp-directory", default="tmp", help="The image temp directory")
@click.option(
    "--model-type",
    default="titan",
    help="The model type",
    type=click.Choice(["titan", "stability_ai"]),
)
@click.pass_context
def main(ctx, repository_name, pull_request_number, image_temp_directory, model_type):
    pull_request_images = app.run(
        ctx.obj, repository_name, pull_request_number, image_temp_directory, model_type
    )
    print(json.dumps(pull_request_images, indent=2))


if __name__ == "__main__":
    contexts = {
        "images_bucket_name": os.environ.get("CDN_BUCKET_NAME"),
        "github_client": Github(os.environ.get("GITHUB_TOKEN")),
        "bedrock_client": boto3.client("bedrock-runtime"),
        "s3_client": boto3.client("s3"),
    }
    main(obj=contexts)  # pylint: disable=all
