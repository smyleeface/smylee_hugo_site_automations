"""Test functions for slack message_blocks"""

import logging
import os
import unittest

import hugo_site.blog_post_image_generator.slack.message_blocks as message_blocks


class TestSlackMessageBlocks(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(os.environ.get("LOGGING_LEVEL", logging.DEBUG))

    def test_slack_app_header(self):
        response = message_blocks.slack_app_header("url_foobar", 12, "repo/foobar")
        self.assertTrue(
            "url_foobar" in response.get("blocks")[1].get("text").get("text")
        )
        self.assertTrue("12" in response.get("blocks")[1].get("text").get("text"))
        self.assertTrue(
            "repo/foobar" in response.get("blocks")[1].get("text").get("text")
        )
