## Blog Post Image Generator

For any posts in a pull request that is missing a thumbnail, this script will generate a blog post image using Amazon Bedrock, upload to S3 (CDN bucket), and update the file in the pull request with the path to the image.

I have code for the two models, sending the title and description of the post:

* [Amazon Titan Image Generator](https://aws.amazon.com/bedrock/titan/) (default)
* [Stable Diffusion XL](https://aws.amazon.com/bedrock/stable-diffusion/)

> Include environment variable `MODEL_TYPE=stability_ai` to use the Stable Diffusion XL model.

This will be a lambda function for now, triggered by an SNS topic.

Other apps will have access to write to this SNS topic, so the image generation process can be triggered by multiple sources.

```mermaid
sequenceDiagram
    Lambda-->>GitHub: Get the list of files<br>changed in the pull request 
    GitHub-->>Lambda: Filter any file that's<br>not a post
    Lambda-->>GitHub: Get the file contents<br>of each post
    GitHub-->>Lambda: Filter only files that<br>have `thumbnail = ""`
    Lambda-->>Bedrock: Send prompt with<br>post title and description
    Bedrock-->>Lambda: Save images locally
    Lambda-->>S3: Upload images to S3 CDN
    S3-->>Lambda: Update `thumbnail = ""` with<br>the path to the image<br>generated for that post
    Lambda-->>GitHub: Update the pull request<br>with a commit that<br>has the updated `thumbnail`
```

Expected SNS message format in payload:
```json
{
    "github": {
        "repository_name": "string",
        "pull_request_number": number
    }
}
```