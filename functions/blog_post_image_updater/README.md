## Blog Post Image Updater

This will update the file in the pull request with the path to the image.

CLI usage:

```bash
python cli.py \
    --repository-name "owner/repo_name" \
    --branch-name fun_branch_name \
    --file-path path/to/file/update.md \
    --cdn-path https://cdn.example.com/image/path_to_the_image.png
```