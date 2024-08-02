"""Main module for updating the thumbnail on the pull request."""

import logging
import os

from hugo_site.blog_post_image_updater.front_matter import convert

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGGING_LEVEL", logging.INFO))


def run(ctx, repository_name, branch_name, file_path, cdn_path):
    """Update the thumbnail in the front matter of the file."""
    github_client = ctx["github_client"]
    repo = github_client.get_repo(repository_name)
    contents = repo.get_contents(file_path, ref=branch_name)
    content_str = contents.decoded_content.decode("utf-8")

    post_content = content_str.split("+++")[-1]

    front_matter_json = convert.toml_str_to_dict(content_str)
    front_matter_json["thumbnail"] = cdn_path
    updated_content = convert.dict_to_toml_str(front_matter_json) + post_content

    logger.info("Updating Repo: %d", cdn_path)
    repo.update_file(
        contents.path,
        f"chore: added thumbnail for {file_path}",
        updated_content,
        contents.sha,
        branch=branch_name,
    )

    return "done"
