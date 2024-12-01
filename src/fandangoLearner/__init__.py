import importlib.resources as pkg_resources


def get_pattern_file_path():
    return pkg_resources.files("fandango-learn.resources") / "patterns.toml"


def get_islearn_pattern_file_path():
    return pkg_resources.files("fandango-learn.resources") / "patterns_islearn.toml"
