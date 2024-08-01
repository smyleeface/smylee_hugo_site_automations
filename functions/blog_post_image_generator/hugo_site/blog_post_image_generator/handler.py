"""Lambda function to generate images for blog posts."""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError
from github import Auth
from github import GithubIntegration

import hugo_site.blog_post_image_generator.app as app
import hugo_site.blog_post_image_generator.slack.message as slack_message
import hugo_site.blog_post_image_generator.slack.message_blocks as message_blocks

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGGING_LEVEL", logging.INFO))

image_temp_directory = os.getenv("IMAGE_TEMP_DIR", "tmp")
os.makedirs(image_temp_directory, exist_ok=True)

model_type = os.getenv("MODEL_TYPE", "titan")  # titan or stability_ai

boto3_session = boto3.session.Session()
ssm_client = boto3_session.client(service_name="ssm", region_name="us-west-2")
s3_client = boto3_session.client(service_name="s3", region_name="us-west-2")
images_bucket_name = os.getenv("WEBSITE_CDN_IMAGES_BUCKET", "smylee.com.assets")
workflow_assets_bucket_name = os.getenv(
    "WORKFLOW_ASSETS_BUCKET", "devworkflow-payload-storage-n567md2s"
)

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
sns_client = boto3_session.client(service_name="sns", region_name="us-west-2")


def lambda_handler(event, context):
    message_str = event.get("Records", [{}])[0].get("Sns", {}).get("Message", "")
    message = json.loads(json.loads(json.dumps(message_str)))
    repo_name = message.get("github", {}).get("repository_name", "")
    pull_request_number = message.get("github", {}).get("pull_request_number", "")
    response_url = message.get("slack", {}).get("response_url", "")

    # run the app
    ctx = {
        "github_client": github_client,
        "bedrock_client": bedrock_client,
        "s3_client": s3_client,
        "images_bucket_name": images_bucket_name,
    }
    generated_images = app.run(
        ctx, repo_name, pull_request_number, image_temp_directory, model_type
    )

    # construct and write message to file
    slack_message_data = message_blocks.slack_app_header(
        generated_images.get("url_to_pull_request"),
        generated_images.get("pull_request_number"),
        generated_images.get("repo_name"),
    )
    for generated_image in generated_images.get("posts"):
        slack_message_data.append(
            message_blocks.slack_section_header(generated_image.get("title"))
        )
        for generated_image_option in generated_image.get("options"):
            slack_message_data.append(
                message_blocks.slack_image_option(
                    generated_image_option.get("text"),
                    generated_image_option.get("image_url"),
                    generated_image_option.get("alt_text"),
                )
            )
            slack_message_data.append(
                message_blocks.slack_image_option_button(
                    generated_image_option.get("text"),
                    generated_image_option.get("value"),
                )
            )
    slack_message.send(response_url, slack_message_data)
