#!/usr/bin/python3

import gitlab
import click
import pathlib


def search_spec(project, branch):
    for file in project.repository_tree(ref=branch, iterator=True):
        if file["type"] == "tree":
            continue
        if file["path"].endswith(".spec"):
            print(f"Found {file['path']}")
            return (
                file["path"],
                project.files.get(file_path=file["path"], ref=branch).decode().decode(),
            )
    return None, None


def get_spec(project, branch):
    try:
        path = f"{project.name}.spec"
        return path, project.files.get(file_path=path, ref=branch).decode().decode()
    except gitlab.exceptions.GitlabGetError:
        pass

    try:
        project.branches.get(branch)
        print("Search for a spec", end=", ")
        return search_spec(project, branch)
    except gitlab.exceptions.GitlabGetError:
        return None, None


@click.command()
@click.argument("branch")
@click.option(
    "--group",
    default="redhat/centos-stream/rpms",
    show_default=True,
    help="Group on GitLab.com from where specfiles are downloaded.",
)
@click.option("--gitlab-token", envvar="GITLAB_TOKEN")
@click.option(
    "-o",
    "--output",
    default=None,
    help="Name of the directory where " "the specfiles are going to be saved.",
)
def download_specs(branch, group, gitlab_token, output):
    """
    Download specfiles from dist-git repositories hosted on GitLab.com.

    Searches for the first file with a '.spec' suffix, if '<repo_name>.spec' is not found.

    A token to be used with the GitLab API can be provided either by the GITLAB_TOKEN environment
    variable or by the --gitlab-token option.
    """
    gl = gitlab.Gitlab(private_token=gitlab_token)
    gl.auth()

    pathlib.Path(output or branch).mkdir(parents=True, exist_ok=True)

    group = gl.groups.get(group)
    for i, project in enumerate(group.projects.list(iterator=True)):
        print(f"{i:04} Getting spec for {project.name}", end=", ")
        project = gl.projects.get(project.id)
        spec, content = get_spec(project, branch)

        if spec is None:
            print("No spec found", flush=True)
            continue
        with open(f"{branch}/{spec}", "w") as file:
            print(f"Saving {spec}", flush=True)
            file.write(content)


if __name__ == "__main__":
    download_specs()
