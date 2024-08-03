import toml


def toml_str_to_dict(file_contents):
    start = file_contents.find("+++") + 3
    end = file_contents.find("+++", start)
    toml_content = file_contents[start:end].strip()
    return toml.loads(toml_content)


def dict_to_toml_str(file_contents):
    toml_content = toml.dumps(file_contents)
    return "+++\n" + toml_content + "+++\n"
