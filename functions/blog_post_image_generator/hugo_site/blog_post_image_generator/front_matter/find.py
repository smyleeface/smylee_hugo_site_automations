import hugo_site.blog_post_image_generator.front_matter.convert as convert


def files_with_empty_thumbnail(filtered_files, repo, pull_request):
    print("getting files with empty thumbnail")
    empty_thumbnail_files = []
    for file in filtered_files:
        file_contents = repo.get_contents(file, ref=pull_request.head.sha)
        content_str = file_contents.decoded_content.decode("utf-8")
        if "+++" not in content_str:
            continue
        content_from_toml = convert.to_toml(content_str)
        if content_from_toml.get("thumbnail") == "":
            content_from_toml.update({"filename": file})
            empty_thumbnail_files.append(content_from_toml)
    return empty_thumbnail_files
