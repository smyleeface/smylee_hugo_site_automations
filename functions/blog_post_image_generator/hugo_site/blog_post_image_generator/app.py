"""Main module for the blog post image generator."""

import logging
import os

from hugo_site.blog_post_image_generator.aws import bedrock
from hugo_site.blog_post_image_generator.aws import s3
from hugo_site.blog_post_image_generator.front_matter import find

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGGING_LEVEL", logging.INFO))


def run(ctx, repository_name, pull_request_number, image_temp_directory, model_type):
    github_client = ctx["github_client"]
    bedrock_client = ctx["bedrock_client"]
    s3_client = ctx["s3_client"]
    images_bucket_name = ctx["images_bucket_name"]
    os.makedirs(image_temp_directory, exist_ok=True)
    repo = github_client.get_repo(repository_name)
    url_to_pull_request = repo.get_pull(pull_request_number).html_url
    pull_request = repo.get_pull(pull_request_number)
    files_changed = pull_request.get_files()
    filtered_files = [
        file.filename for file in files_changed if "content/post" in file.filename
    ]
    files_with_empty_thumbnail = find.files_with_empty_thumbnail(
        filtered_files, repo, pull_request
    )
    pull_request_images = {
        "url_to_pull_request": url_to_pull_request,
        "pull_request_number": pull_request_number,
        "repo_name": repository_name,
        "posts": [],
    }
    for section_index, file_info in enumerate(files_with_empty_thumbnail):
        filename = file_info["filename"]
        title = file_info["title"]
        description = file_info["description"]
        logger.info(f"Filename: {filename}\nTitle: {title}\nDescription: {description}")
        generated_images = bedrock.generate_image(
            title,
            description,
            filename,
            bedrock_client,
            image_temp_directory,
            model_type,
        )
        image_options = []
        for image_index, image_path in enumerate(generated_images):
            s3.upload(
                image_temp_directory,
                images_bucket_name,
                s3_client,
                image_path,
                "image/png",
            )
            logger.info(f"Image uploaded to S3: {image_path}")
            image_options.append(
                {
                    "text": f"Option #{image_index + 1}",
                    "image_url": f"https://cdn.smylee.com/{image_path}",
                    "alt_text": title,
                    "value": f"section_{section_index}_option_{image_index}",
                }
            )
        pull_request_images["posts"].append(
            {
                "text": f"Section {section_index + 1} options for {title} ({filename})",
                "image_options": image_options,
            }
        )
    return pull_request_images
