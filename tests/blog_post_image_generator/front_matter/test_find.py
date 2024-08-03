"""Test functions for slack message_blocks"""

import logging
import os
import unittest
from unittest.mock import MagicMock, patch

import hugo_site.blog_post_image_generator.front_matter.find as find


class TestFrontMatterFind(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(os.environ.get("LOGGING_LEVEL", logging.DEBUG))

    def test_files_with_empty_thumbnail(self):

        with patch("convert.to_toml") as mock_convert_to_toml:

            # Dummy function to convert content to a dictionary simulating to_toml behavior
            def dummy_to_toml(content):
                # Mock parsing logic: convert content to a dictionary
                if "thumbnail = ''" in content:
                    return {"thumbnail": ""}
                else:
                    return {}

            mock_convert_to_toml.side_effect = dummy_to_toml

            # Define the test fixtures
            filtered_files = ["content/posts/post1.md", "content/posts/post2.md"]
            pull_request = {
                "head": {"sha": "1234567890"},
            }
            repo = MagicMock()

            # Mock return value of repo.get_contents
            repo.get_contents.return_value.decoded_content = (
                b"+++\ntitle = 'Post 1'\nthumbnail = ''\n+++\nAdditional text\n"
            )

            # Call the function under test
            result = find.files_with_empty_thumbnail(filtered_files, repo, pull_request)

            # Define the expected result
            expected_result = [
                {
                    "thumbnail": "",
                    "filename": "content/posts/post1.md",
                    "title": "Post 1",
                },
                {
                    "thumbnail": "",
                    "filename": "content/posts/post2.md",
                    "title": "Post 1",
                },
            ]

            # Assert that the result matches the expected result
            self.assertEqual(result, expected_result)

            # Verify that get_contents is called with the correct parameters
            for file in filtered_files:
                repo.get_contents.assert_any_call(
                    file, ref=pull_request.get("head", {}).get("sha", "")
                )
