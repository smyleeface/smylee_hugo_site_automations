import toml


def to_toml(file_contents):
    print("converting front matter")
    start = file_contents.find("+++") + 3
    end = file_contents.find("+++", start)
    toml_content = file_contents[start:end].strip()
    return toml.loads(toml_content)
