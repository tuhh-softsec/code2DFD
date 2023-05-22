import core.file_interaction as fi

env_vars = dict()

def extract_environment_variables():
    """Extracts environemnt avriables from .env file, if exiting.
    """

    global env_vars

    env_files = fi.get_file_as_lines(".env")
    for f in env_files:
        for line in env_files[f]["content"]:
            if "=" in line:
                var = line.split("=")[0]
                value = line.split("=")[1]
                env_vars[var] = value


def resolve_env_var(env_var: str) -> str:
    """Looks up the handed environment variable and returns its value.
    """

    global env_vars

    if not env_vars:
        extract_environment_variables()

    env_var = env_var.strip("\"${}")

    try:
        resolved = env_vars[env_var]
    except:
        resolved = env_var

    return resolved
