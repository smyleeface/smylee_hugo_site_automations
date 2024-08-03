import unittest
from unittest.mock import MagicMock, patch

import hugo_site.blog_post_image_generator.app as app


class TestRunFunction(unittest.TestCase):
    @patch("os.makedirs")
    @patch("hugo_site.blog_post_image_generator.aws.s3.upload")
    @patch("hugo_site.blog_post_image_generator.aws.bedrock.generate_image")
    @patch(
        "hugo_site.blog_post_image_generator.front_matter.find.files_with_empty_thumbnail"
    )
    def test_run(
        self, mock_find_files, mock_generate_image, mock_s3_upload, mock_os_makedirs
    ):
        # Set up mock context and parameters
        github_client = MagicMock()
        bedrock_client = MagicMock()
        s3_client = MagicMock()
        images_bucket_name = "test-bucket"

        ctx = {
            "github_client": github_client,
            "bedrock_client": bedrock_client,
            "s3_client": s3_client,
            "images_bucket_name": images_bucket_name,
        }

        repository_name = "owner/repo"
        pull_request_number = 1
        image_temp_directory = "/tmp/images"
        model_type = "some-model-type"

        # Mock GitHub repo and pull request
        repo = github_client.get_repo.return_value
        pull_request = repo.get_pull.return_value

        # Mock the files changed in the pull request
        pull_request.get_files.return_value = [
            MagicMock(filename="content/post/post1.md"),
            MagicMock(filename="content/other/post2.md"),
            MagicMock(filename="content/post/post3.md"),
        ]

        # Mock the files with empty thumbnail
        mock_find_files.return_value = [
            {
                "filename": "content/post/post1.md",
                "title": "Post 1",
                "description": "Description 1",
            },
            {
                "filename": "content/post/post3.md",
                "title": "Post 3",
                "description": "Description 3",
            },
        ]

        # Mock the image generation
        mock_generate_image.side_effect = (
            lambda title, description, filename, client, directory, model: [
                f"{filename}_image1.png",
                f"{filename}_image2.png",
            ]
        )

        # Call the function under test
        result = app.run(
            ctx, repository_name, pull_request_number, image_temp_directory, model_type
        )

        # Verify that the os.makedirs was called
        mock_os_makedirs.assert_called_once_with(image_temp_directory, exist_ok=True)

        # Verify that get_repo and get_pull were called with correct parameters
        github_client.get_repo.assert_called_once_with(repository_name)
        repo.get_pull.assert_called_with(pull_request_number)

        # Verify that files_with_empty_thumbnail was called with correct parameters
        mock_find_files.assert_called_once_with(
            ["content/post/post1.md", "content/post/post3.md"], repo, pull_request
        )

        # Verify the images are generated and uploaded
        mock_generate_image.assert_any_call(
            "Post 1",
            "Description 1",
            "content/post/post1.md",
            bedrock_client,
            image_temp_directory,
            model_type,
        )
        mock_generate_image.assert_any_call(
            "Post 3",
            "Description 3",
            "content/post/post3.md",
            bedrock_client,
            image_temp_directory,
            model_type,
        )

        # Verify that the images were uploaded to S3
        expected_image_paths = [
            "content/post/post1.md_image1.png",
            "content/post/post1.md_image2.png",
            "content/post/post3.md_image1.png",
            "content/post/post3.md_image2.png",
        ]

        for image_path in expected_image_paths:
            mock_s3_upload.assert_any_call(
                image_temp_directory,
                images_bucket_name,
                s3_client,
                image_path,
                "image/png",
            )

        # Define the expected result
        expected_result = {
            "url_to_pull_request": pull_request.html_url,
            "pull_request_number": pull_request_number,
            "repo_name": repository_name,
            "posts": [
                {
                    "text": "Section 1 options for Post 1 (content/post/post1.md)",
                    "image_options": [
                        {
                            "text": "Option #1",
                            "image_url": "https://cdn.smylee.com/content/post/post1.md_image1.png",
                            "alt_text": "Post 1",
                            "value": "section_0_option_0",
                        },
                        {
                            "text": "Option #2",
                            "image_url": "https://cdn.smylee.com/content/post/post1.md_image2.png",
                            "alt_text": "Post 1",
                            "value": "section_0_option_1",
                        },
                    ],
                },
                {
                    "text": "Section 2 options for Post 3 (content/post/post3.md)",
                    "image_options": [
                        {
                            "text": "Option #1",
                            "image_url": "https://cdn.smylee.com/content/post/post3.md_image1.png",
                            "alt_text": "Post 3",
                            "value": "section_1_option_0",
                        },
                        {
                            "text": "Option #2",
                            "image_url": "https://cdn.smylee.com/content/post/post3.md_image2.png",
                            "alt_text": "Post 3",
                            "value": "section_1_option_1",
                        },
                    ],
                },
            ],
        }

        # Assert the result matches the expected result
        self.assertEqual(result, expected_result)
