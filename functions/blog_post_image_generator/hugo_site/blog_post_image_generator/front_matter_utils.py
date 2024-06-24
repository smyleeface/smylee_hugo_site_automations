import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGGING_LEVEL", logging.INFO))


def get_data(front_matter):
    title = None
    description = None
    for line in front_matter.split("\n"):
        if line.startswith("title ="):
            title = line.split("=", 1)[1].strip().strip('"')
        if line.startswith("description ="):
            description = line.split("=", 1)[1].strip().strip('"')
    return {"title": title, "description": description}


def update_thumbnail_in_file(repo, file_path, cdn_path, branch_name):
    contents = repo.get_contents(file_path, ref=branch_name)
    content_str = contents.decoded_content.decode("utf-8")

    front_matter, body = content_str.split("+++")[1], "+++".join(
        content_str.split("+++")[2:]
    )
    updated_front_matter = front_matter.replace(
        'thumbnail = ""', f'thumbnail = "{cdn_path}"'
    )
    updated_content = f"+++\n{updated_front_matter}+++\n{body}"

    logger.info(f"Updating Repo: {cdn_path}")
    repo.update_file(
        contents.path,
        f"chore: added thumbnail for {file_path}",
        updated_content,
        contents.sha,
        branch=branch_name,
    )
