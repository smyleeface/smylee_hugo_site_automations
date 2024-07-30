import logging
import os

import boto3
from botocore.exceptions import ClientError

from github import GithubIntegration
from github import Auth

import hugo_site.blog_post_image_generator.aws.s3 as s3
import hugo_site.blog_post_image_generator.front_matter_util.find as find
import hugo_site.blog_post_image_generator.aws.bedrock as bedrock

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGGING_LEVEL", logging.INFO))

image_temp_directory = os.getenv("IMAGE_TEMP_DIR", "tmp")
os.makedirs(image_temp_directory, exist_ok=True)

model_type = os.getenv("MODEL_TYPE", "titan")  # titan or stability_ai

boto3_session = boto3.session.Session()
ssm_client = boto3_session.client(service_name="ssm", region_name="us-west-2")
s3_client = boto3_session.client(service_name="s3", region_name="us-west-2")
images_bucket_name = os.getenv("WEBSITE_CDN_IMAGES_BUCKET", "smylee.com.assets")

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
    # message_str = event.get("Records", [{}])[0].get("Sns", {}).get("Message", "")
    # message = json.loads(json.loads(json.dumps(message_str)))
    message = event
    repo_name = message.get("github", {}).get("repository_name", "")
    repo = github_client.get_repo(repo_name)
    pull_request_number = message.get("github", {}).get("pull_request_number", "")
    pull_request = repo.get_pull(pull_request_number)
    files_changed = pull_request.get_files()
    branch_name = pull_request.head.ref
    filtered_files = [file.filename for file in files_changed if "content/post" in file.filename]
    files_with_empty_thumbnail = find.files_with_empty_thumbnail(filtered_files, repo, pull_request)

    # Generate image for files with empty thumbnail values and their title and description
    for index, file_info in enumerate(files_with_empty_thumbnail):
        filename = file_info["filename"]
        title = file_info["title"]
        description = file_info["description"]
        logger.info(f"Filename: {filename}\nTitle: {title}\nDescription: {description}")
        files_with_empty_thumbnail[index]["image"] = bedrock.generate_image(title, description, filename, bedrock_client, image_temp_directory, model_type)

    # Upload the entire temp directory to S3
    for file_info in files_with_empty_thumbnail:
        s3.upload(image_temp_directory, images_bucket_name, s3_client, file_info["image"])
        cdn_path = f"{file_info.get('image', '')}"
        logger.info(f"Image uploaded to S3: {cdn_path}")

    return "done"
