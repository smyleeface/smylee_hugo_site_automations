import logging
import json
import os

import boto3
from botocore.exceptions import ClientError

from github import GithubIntegration
from github import Auth

import hugo_site.blog_post_image_generator.bedrock_images as bedrock_images
import hugo_site.blog_post_image_generator.front_matter_utils as front_matter_utils
import hugo_site.blog_post_image_generator.upload_to_s3 as upload_to_s3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGGING_LEVEL", logging.INFO))

image_temp_directory = os.getenv("IMAGE_TEMP_DIR", "tmp")
os.makedirs(image_temp_directory, exist_ok=True)

model_type = os.getenv("MODEL_TYPE", "titan")  # titan or stability_ai

boto3_session = boto3.session.Session()
ssm_client = boto3_session.client(service_name="ssm", region_name="us-west-2")
s3_client = boto3_session.client(service_name="s3", region_name="us-west-2")
images_bucket_name = os.getenv("WEBSITE_CDN_IMAGES_BUCKET")

try:
    app_parameters = ssm_client.get_parameters(
        Names=[
            "/SmyleeDevWorkflows/GitHubApp/Id",
            "/SmyleeDevWorkflows/GitHubApp/PrivateKey",
        ],
        WithDecryption=True,
    )
except ClientError as e:
    raise e

gh_app_id = app_parameters["Parameters"][0]["Value"]
gh_private_key = app_parameters["Parameters"][1]["Value"]

github_auth = Auth.AppAuth(gh_app_id, gh_private_key)
github_integration = GithubIntegration(auth=github_auth)
installation = github_integration.get_installations()[0]
github_client = installation.get_github_for_installation()

bedrock_client = boto3.client("bedrock-runtime")


def lambda_handler(event, context):
    message_str = event.get("Records", [{}])[0].get("Sns", {}).get("Message", "")
    message = json.loads(json.loads(json.dumps(message_str)))
    repo_name = message.get("repository_name", "")
    repo = github_client.get_repo(repo_name)
    pull_request_number = message.get("pull_request_number", "")
    pull_request = repo.get_pull(pull_request_number)
    files_changed = pull_request.get_files()
    branch_name = pull_request.head.ref

    # Filter files changed to only include strings with `content/post`
    filtered_files = [
        file.filename for file in files_changed if "content/post" in file.filename
    ]
    empty_thumbnail_files = []

    for file in filtered_files:
        file_contents = repo.get_contents(file, ref=pull_request.head.sha)
        content_str = file_contents.decoded_content.decode("utf-8")

        # Check if the thumbnail value is empty in the front matter
        if "+++" in content_str:
            front_matter = content_str.split("+++")[1]
            if 'thumbnail = ""' in front_matter:
                file_data = front_matter_utils.get_data(front_matter)
                file_data.update({"filename": file})
                empty_thumbnail_files.append(file_data)

    # Print files with empty thumbnail values and their title and description
    for index, file_info in enumerate(empty_thumbnail_files):
        filename = file_info["filename"]
        title = file_info["title"]
        description = file_info["description"]
        logger.info(f"Filename: {filename}")
        logger.info(f"Title: {title}")
        logger.info(f"Description: {description}")
        prompt = f'Create an image for a blog post where the title and description are:\n\n"{title}"\n"{description}"\n\n.'
        negative_prompt = "avoid using typography"
        if model_type == "stability_ai":
            bedrock_image_names = bedrock_images.run_stability_ai(
                prompt, negative_prompt, bedrock_client, filename, image_temp_directory
            )
        else:
            bedrock_image_names = bedrock_images.run_titan_image_generator(
                prompt, negative_prompt, bedrock_client, filename, image_temp_directory
            )
        empty_thumbnail_files[index]["image"] = bedrock_image_names[0]

    # Upload the entire temp directory to S3
    for file_info in empty_thumbnail_files:
        upload_to_s3.run(
            image_temp_directory, images_bucket_name, s3_client, file_info["image"]
        )
        cdn_path = f"{file_info.get('image', '')}"
        logger.info(f"Image uploaded to S3: {cdn_path}")
        front_matter_utils.update_thumbnail_in_file(
            repo, file_info["filename"], cdn_path, branch_name
        )

    return "done"
