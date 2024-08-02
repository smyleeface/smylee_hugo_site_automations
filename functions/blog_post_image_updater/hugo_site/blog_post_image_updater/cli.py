"""Main CLI for the blog post image generator."""

import logging
import os

import click
from dotenv import load_dotenv
from github import Github

import hugo_site.blog_post_image_updater.app as app

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGGING_LEVEL", logging.INFO))


@click.command()
@click.option("--repository-name", required=True, help="The repository name")
@click.option("--branch-name", required=True, help="The branch name to make the update")
@click.option("--file-path", required=True, help="Path to the file to update in the pull request")
@click.option("--cdn-path", required=True, help="Address to the image on the CDN")
@click.pass_context
def main(ctx, repository_name, branch_name, file_path, cdn_path):
    app.run(ctx.obj, repository_name, branch_name, file_path, cdn_path)


if __name__ == "__main__":
    load_dotenv()
    contexts = {
        "github_client": Github(os.environ.get("GITHUB_TOKEN")),
    }
    main(obj=contexts)  # pylint: disable=all
