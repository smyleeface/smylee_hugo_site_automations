def slack_section_header(text):
    return [
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text,
            },
        },
    ]


def slack_image_option(text, image_url, alt_text):
    return {
        "type": "image",
        "title": {"type": "plain_text", "text": text, "emoji": True},
        "image_url": image_url,
        "alt_text": alt_text,
    }


def slack_image_option_button(text, value):
    return {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": text,
                    "emoji": True,
                },
                "value": value,
                "action_id": "choose_image_action",
            }
        ],
    }


def slack_app_header(url_to_pull_request, pull_request_number, repo_name):
    return {
        "response_type": "in_channel",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Blog Post Image Generator",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Choose the images you want to use for *<{url_to_pull_request}|pull request #{str(pull_request_number)}>* in _{repo_name}_",
                },
            },
        ],
    }
