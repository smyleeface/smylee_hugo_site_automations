"""Test functions for slack message_blocks"""

import logging
import os
import unittest
from unittest.mock import patch

import hugo_site.blog_post_image_generator.front_matter.convert as convert


class TestToToml(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(os.environ.get("LOGGING_LEVEL", logging.DEBUG))

    @patch("toml.loads")
    def test_to_toml(self, mock_toml_loads):
        # Define the test input
        file_contents = "+++\ntitle = 'Post 1'\nthumbnail = ''\n+++\nAdditional text\n"

        # Define the expected TOML content as a dictionary
        expected_toml_dict = {"title": "Post 1", "thumbnail": ""}

        # Mock the return value of toml.loads to return the expected dictionary
        mock_toml_loads.return_value = expected_toml_dict

        # Call the function under test
        result = convert.to_toml(file_contents)

        # Assert that the result matches the expected dictionary
        self.assertEqual(result, expected_toml_dict)

        # Verify that toml.loads was called with the correct TOML string
        mock_toml_loads.assert_called_once_with("title = 'Post 1'\nthumbnail = ''")
