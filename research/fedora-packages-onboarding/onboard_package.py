#!/usr/bin/env python3

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import logging
import os
import subprocess
from pathlib import Path

import click
import git
from yaml import safe_dump, safe_load

from ogr import PagureService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

RAWHIDE = "rawhide"
ONBOARD_BRANCH_NAME = "packit-config"

CONFIG_HEADER = """# See the documentation for more information:
# https://packit.dev/docs/configuration/
"""

CONFIG_FILE_NAME = ".packit.yaml"
PR_TITLE = """Add Packit configuration for automating release syncing"""
PR_DESCRIPTION = """
For more details, see https://packit.dev/docs/configuration/ or contact
[the Packit team](https://packit.dev#contacts)

"""


@click.group()
def cli() -> None:
    pass


def parse_actions_from_file(actions_file):
    with open(actions_file) as file:
        actions_content = file.read()

    try:
        actions = safe_load(actions_content)
        if not isinstance(actions, dict):
            raise ValueError("The content of the actions file is not a dictionary.")
    except Exception as e:
        raise ValueError(f"Error parsing YAML content: {e}")


def generate_config_from_input(
    upstream_project_url,
    upstream_tag_template,
    issue_repository,
    upstream_tag_include,
    upstream_tag_exclude,
    include_koji_build,
    include_bodhi_update,
    allowed_committers,
    allowed_pr_authors,
    actions,
):
    config = {"upstream_project_url": upstream_project_url}
    optional_config_keys = [
        "upstream_tag_template",
        "upstream_tag_include",
        "upstream_tag_exclude",
        "issue_repository",
        "allowed_committers",
        "allowed_pr_authors",
        "actions",
    ]

    for key in optional_config_keys:
        value = locals().get(key)
        if value:
            config[key] = value

    config["jobs"] = [
        {
            "job": "pull_from_upstream",
            "trigger": "release",
            # TODO also make this as input parameter?
            "dist_git_branches": ["fedora-all"],
        },
    ]
    if include_koji_build:
        config["jobs"].append(
            {
                "job": "koji_build",
                "trigger": "commit",
                "dist_git_branches": ["fedora-all"],
            }
        )

    # currently it doesn't make sense to create Bodhi job
    # if Koji job is not configured
    if include_bodhi_update and include_koji_build:
        config["jobs"].append(
            {
                "job": "bodhi_update",
                "trigger": "commit",
                "dist_git_branches": ["fedora-branched"],
            }
        )

    return f"{CONFIG_HEADER}\n{safe_dump(config, sort_keys=False)}"


def clone_package(package: str, cwd: Path):
    logger.info(f"Cloning {package}")
    cmd = ["fedpkg", "clone", package]
    subprocess.run(cmd, cwd=cwd)


# TODO test it
# if we incorporated this to packit, this functionality can be replaced
class DistgitRepoUpdater:
    def __init__(self, path_to_repo, remote_name, package_name):
        self.repo = git.Repo(path_to_repo)
        self.remote_name = remote_name
        self._package_name = package_name
        self._ogr_project = None

    @property
    def package_name(self):
        if not self._package_name:
            self._package_name = (
                self.repo.remote(self.remote_name).url.split(".git")[0].split("/")[-1]
            )
        return self._package_name

    @property
    def ogr_project(self):
        if not self._ogr_project:
            service = PagureService(
                instance_url="https://src.fedoraproject.org",
                token=os.getenv("PAGURE_TOKEN"),
            )
            self._ogr_project = service.get_project(
                namespace="rpms", repo=self.package_name
            )
        return self._ogr_project

    def create_onboard_branch(self):
        origin = self.repo.remote(self.remote_name)
        origin.fetch()
        new_branch = self.repo.create_head(ONBOARD_BRANCH_NAME, origin.refs[RAWHIDE])
        new_branch.checkout()

    def commit_packit_config(self):
        logger.info("Creating commit.")
        self.repo.index.add([CONFIG_FILE_NAME])
        self.repo.index.commit(PR_TITLE)

    def push_to_fork(self):
        fork_remote_name = "packit-fork"
        logger.debug(
            f"About to push changes to branch {ONBOARD_BRANCH_NAME} "
            f"of a fork of the dist-git repo.",
        )
        if fork_remote_name not in [remote.name for remote in self.repo.remotes]:
            fork = self.ogr_project.get_fork()
            if not fork:
                logger.debug("Creating a new fork.")
                self.ogr_project.fork_create()
                fork = self.ogr_project.get_fork()
            if not fork:
                raise Exception("Unable to create a fork of the repository ")
            fork_urls = fork.get_git_urls()
            self.repo.create_remote(
                name=fork_remote_name,
                url=fork_urls["ssh"],
            )
        self.push(fork_remote_name, ONBOARD_BRANCH_NAME)

    def push(self, remote: str, branch):
        try:
            self.repo.remote(name=remote).push(refspec=branch, no_verify=True)
        except git.GitError as ex:
            msg = (
                f"Unable to push to remote fork using branch {branch}, "
                f"the error is:\n{ex}"
            )
            raise Exception(msg) from ex

    def push_directly(self):
        # update rawhide
        origin = self.repo.remote(self.remote_name)
        origin.fetch()
        remote_ref = origin.refs[RAWHIDE]
        head = self.repo.heads[RAWHIDE]
        head.set_commit(remote_ref)

        self.repo.git.switch(RAWHIDE)
        self.commit_packit_config()
        self.push(self.remote_name, RAWHIDE)
        logger.info("Changes were successfully pushed.")

    def push_and_create_pr(self):
        self.create_onboard_branch()
        self.commit_packit_config()
        self.push_to_fork()
        logger.info("Creating the PR.")
        pr = self.ogr_project.create_pr(
            title=PR_TITLE,
            body=PR_DESCRIPTION,
            target_branch=RAWHIDE,
            source_branch=ONBOARD_BRANCH_NAME,
        )
        logger.info(f"PR was successfully created: {pr.url}")


@cli.command(
    "generate-config",
    help="Generate Packit dist-git configuration with jobs automating the "
    "release syncing, optionally push the config to rawhide or create a "
    "PR against rawhide",
)
@click.option(
    "--upstream-git-url", help="URL to the upstream GIT repository", required=True
)
@click.option(
    "--upstream-tag-template",
    help="Template applied for upstream tags if they differ from versions. E.g. 'v{version}' ",
)
@click.option(
    "--upstream-tag-include",
    help="Python regex used for filtering upstream tags to include. ",
)
@click.option(
    "--upstream-tag-exclude",
    help="Python regex used for filtering upstream tags to include. ",
)
@click.option(
    "--issue-repository",
    help="URL of a git repository that can be used for reporting errors. ",
)
@click.option(
    "--no-koji-build",
    default=False,
    is_flag=True,
    help="Do not include the Koji build job in the config",
)
@click.option(
    "--allowed-committers",
    help="Comma separated list of allowed_committers used for Koji builds",
    default="",
)
@click.option(
    "--allowed-pr-authors",
    help="Comma separated list of allowed_pr_authors used for Koji builds",
    default="",
)
@click.option(
    "--no-bodhi-update",
    default=False,
    is_flag=True,
    help="Do not include the Bodhi update job in the config",
)
@click.option(
    "--actions-file",
    help="Yaml file with 'actions' that should be used for the config",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--push-to-distgit",
    "-p",
    default=False,
    is_flag=True,
    help="Push the generated Packit config to the dist-git repository's rawhide",
)
@click.option(
    "--create-pr",
    "-c",
    default=False,
    is_flag=True,
    help="Create a PR with generated Packit config",
)
@click.option(
    "--package-to-clone",
    help="Package name for cloning.",
)
@click.option(
    "--remote-name",
    default="origin",
    help="Remote name for pushing to dist-git (use with --push-to-distgit)",
)
@click.argument(
    "path", type=click.Path(dir_okay=True, file_okay=False), default=os.path.curdir
)
def generate_config(
    upstream_git_url,
    upstream_tag_template,
    upstream_tag_include,
    upstream_tag_exclude,
    issue_repository,
    no_koji_build,
    allowed_committers,
    allowed_pr_authors,
    no_bodhi_update,
    actions_file,
    push_to_distgit,
    create_pr,
    package_to_clone,
    remote_name,
    path,
):
    repo_path = Path(path)

    if package_to_clone:
        clone_package(package_to_clone, repo_path)
        repo_path = repo_path / package_to_clone

    logger.info(f"Generating config for dist-git repository placed in {repo_path}")

    config_path = repo_path / CONFIG_FILE_NAME

    if config_path.exists():
        logger.warning(
            f"Config file {config_path} already exists and will be overwritten."
        )

    config = generate_config_from_input(
        upstream_project_url=upstream_git_url,
        upstream_tag_template=upstream_tag_template,
        upstream_tag_include=upstream_tag_include,
        upstream_tag_exclude=upstream_tag_exclude,
        issue_repository=issue_repository,
        include_koji_build=not no_koji_build,
        include_bodhi_update=not no_bodhi_update,
        allowed_committers=allowed_committers.split(",") if allowed_committers else [],
        allowed_pr_authors=allowed_pr_authors.split(",") if allowed_pr_authors else [],
        actions=parse_actions_from_file(actions_file),
    )
    logger.info(f"Generated config: \n\n{config}\n\n")

    logger.info(f"Writing config to {config_path}")
    config_path.write_text(config)

    if not (push_to_distgit or create_pr):
        return

    updater = DistgitRepoUpdater(repo_path, remote_name, package_to_clone)

    if push_to_distgit:
        logger.info("Pushing the Packit config to the dist-git repository.")
        updater.push_directly()
    elif create_pr:
        logger.info("Creating a PR with the generated Packit config.")
        updater.push_and_create_pr()


if __name__ == "__main__":
    cli()
