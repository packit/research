#!/usr/bin/env python3

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


import difflib
import importlib
import logging
import os
import re
import time
from datetime import datetime
from os import getenv
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import click
import requests

from ogr import get_project, GithubService, GitlabService
from ogr.abstract import GitProject
from ogr.services.github import GithubProject
from ogr.services.gitlab import GitlabProject
from packit.config.package_config import find_remote_package_config

logger = logging.getLogger(__name__)

DEFAULT_MSG: str = "Update Packit configuration"
DEFAULT_CONFIG_DIR: str = "packit_configurations"
SOURCE_BRANCH: str = "packit-configuration-update"
URL_FILE_NAME: str = "url.txt"

services = {
    GithubService(token=getenv("GITHUB_TOKEN")),
    GitlabService(token=getenv("GITLAB_TOKEN")),
    GitlabService(
        instance_url="https://gitlab.freedesktop.org",
        token=getenv("GITLAB_FREEDESKTOP_TOKEN"),
    ),
    GitlabService(
        instance_url="https://gitlab.gnome.org", token=getenv("GITLAB_GNOME_TOKEN")
    ),
}


class Migration:
    def __init__(self, module):
        self.module = module
        self.migrate_fn_present = hasattr(
            module, "migrate_package_config"
        ) and callable(module.migrate_package_config)
        self.is_affected_fn_present = hasattr(
            module, "is_package_config_affected"
        ) and callable(module.is_package_config_affected)

    @classmethod
    def from_file(cls, file_path: str) -> Optional["Migration"]:
        module_id = re.sub(r"\W", "_", Path(file_path).name)
        spec = importlib.util.spec_from_file_location(module_id, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return Migration(module)

    @property
    def commit_message(self) -> str:
        return getattr(self.module, "commit_msg", DEFAULT_MSG)

    def migrate_package_config(self, package_config: str) -> str:
        return self.module.migrate_package_config(package_config)

    def is_package_config_affected(self, package_config: str) -> bool:
        return self.module.is_package_config_affected(package_config)

    def get_affected_from_directory(self, directory: str) -> set:
        affected = set()
        for repo_dir in Path(directory).iterdir():
            if not repo_dir.is_dir():
                continue

            local_repo_info = LocalConfigDirectory.from_directory(directory=repo_dir)
            if not local_repo_info.url or not local_repo_info.package_config_path:
                continue

            if self.is_package_config_affected(local_repo_info.package_config):
                affected.add(local_repo_info)

        return affected


class LocalConfigDirectory:
    def __init__(self, directory: Path, url: str, package_config_path: Path):
        self.directory = directory
        self.url = url
        self.package_config_path: Path = package_config_path

        self._project = None
        self._package_config: Optional[str] = None

    @classmethod
    def get_url_from_file(cls, directory: Path) -> Optional[str]:
        url_file = os.path.join(directory, URL_FILE_NAME)
        if not os.path.isfile(url_file):
            return None

        with open(url_file) as file:
            url = file.read()

        return url

    @classmethod
    def get_packit_config_local_file_path(cls, directory: Path) -> Optional[Path]:
        packit_config = list(Path(directory).glob("*packit*"))
        if not packit_config or not os.path.isfile(filename := packit_config[0]):
            return None

        return filename

    @classmethod
    def from_directory(cls, directory: Path) -> "LocalConfigDirectory":
        url = cls.get_url_from_file(directory)
        packit_config_file_path = cls.get_packit_config_local_file_path(directory)
        return LocalConfigDirectory(directory, url, packit_config_file_path)

    @property
    def project(self):
        if not self._project:
            self._project = get_project(
                self.url, custom_instances=services, force_custom_instance=False
            )
        return self._project

    @property
    def package_config(self):
        if not self._package_config or not self.project or not self.package_config_path:
            with open(self.package_config_path) as file:
                self._package_config = file.read()
        return self._package_config


class RemoteRepositoryInfoGetter:
    def __init__(self, url: str):
        self.url = url
        self._project: Optional[GitProject] = None
        self._package_config_path: Optional[str] = None
        self._package_config: Optional[str] = None

    @property
    def project(self):
        if not self._project:
            self._project = get_project(
                self.url, custom_instances=services, force_custom_instance=False
            )
        return self._project

    @property
    def package_config_path(self):
        if not self._package_config_path or not self.project:
            try:
                self._package_config_path = find_remote_package_config(self.project)
            except Exception:
                click.echo(f"Not able to find the configuration for {self.url}")
        return self._package_config_path

    @property
    def package_config(self):
        if not self._package_config or not self.project or not self.package_config_path:
            self._package_config = self.project.get_file_content(
                path=self.package_config_path
            )
        return self._package_config


class PackageConfigUpdater:
    def __init__(
        self,
        project: GitProject,
        config_file_name: str,
        commit_msg: str,
        updated_packit_config: str,
        pr_title: str,
    ):
        self.project = project
        self.config_file_name = config_file_name
        self.commit_msg = commit_msg
        self.updated_packit_config = updated_packit_config
        self.pr_title = pr_title

        self._fork = None

    @property
    def fork(self):
        if not self._fork:
            if not self.project.is_forked():
                click.echo("Forking the project...")
                self._fork = self.project.get_fork(create=True)
                # the fork is not available via API immediately
                time.sleep(15)
            else:
                self._fork = self.project.get_fork(create=False)
        return self._fork

    def commit_file_in_new_branch(self):
        if isinstance(self.project, GithubProject):
            return self.commit_file_in_new_branch_github()

        if isinstance(self.project, GitlabProject):
            return self.commit_file_in_new_branch_gitlab()

    def commit_file_in_new_branch_github(self):
        commit = self.project.github_repo.get_commit(
            f"refs/heads/{self.project.default_branch}"
        )
        fork_commit = self.fork.github_repo.get_commit(
            f"refs/heads/{self.fork.default_branch}"
        )

        # TODO: do this programmatically
        if commit.sha != fork_commit.sha:
            click.echo(
                "Fork is not synced with the parent repo, skipping the update. "
                "(Please sync the fork and try again.)"
            )
            return False

        ref = f"refs/heads/{SOURCE_BRANCH}"
        refs = [
            reference
            for reference in self.fork.github_repo.get_git_refs()
            if ref in reference.ref
        ]
        if not refs:
            self.fork.github_repo.create_git_ref(ref, commit.sha)

        contents = self.fork.github_repo.get_contents(
            path=self.config_file_name, ref=SOURCE_BRANCH
        )

        try:
            commit = self.fork.github_repo.update_file(
                self.config_file_name,
                self.commit_msg,
                self.updated_packit_config,
                contents.sha,
                branch=SOURCE_BRANCH,
            )
            click.echo(f"Commit URL: {commit['commit'].html_url}")
        except Exception as ex:
            click.echo(f"Updating file raised an exception: {ex}")
            return False

        return True

    def commit_file_in_new_branch_gitlab(self):
        parent_default_branch = self.project.gitlab_repo.branches.get(
            self.project.default_branch
        )
        parent_commit = parent_default_branch.commit["id"]

        refs = [
            branch
            for branch in self.project.gitlab_repo.branches.list()
            if branch.name == SOURCE_BRANCH
        ]
        if refs:
            ref = refs[0]
        else:
            ref = self.fork.gitlab_repo.branches.create(
                {"branch": SOURCE_BRANCH, "ref": parent_commit}
            )

        file = self.fork.gitlab_repo.files.get(
            file_path=self.config_file_name, ref=ref.name
        )
        file.content = self.updated_packit_config
        try:
            file.save(branch=ref.name, commit_message=self.commit_msg)
            click.echo(f"Branch URL: {ref.web_url}")
        except Exception as ex:
            click.echo(f"Updating file raised an exception: {ex}")
            return False

        return True

    def update(self) -> bool:
        """
        Try to update the Packit config and create PR.

        Returns:
            bool whether the update was successful
        """
        existing_pr = [
            pr for pr in self.project.get_pr_list() if pr.title == DEFAULT_MSG
        ]
        if existing_pr:
            click.echo("Update PR exists.")
            return True

        if self.project.is_fork:
            click.echo(
                "The given project is a fork, skipping the update, "
                "please do the update manually (if needed)."
            )
            return False

        if not self.commit_file_in_new_branch():
            return False

        if not click.confirm(
            click.style(
                "Do you want to create PR from the commit that was created?", fg="red"
            ),
            default=True,
        ):
            click.echo("\n===> Not creating PR.\n")
            return True

        try:
            pr = self.fork.create_pr(
                title=self.pr_title,
                body="In case of any questions, please contact "
                "[Packit team](https://packit.dev/#contact).",
                source_branch=SOURCE_BRANCH,
                target_branch=self.project.default_branch,
            )
        except Exception as ex:
            click.echo(f"There was an error while creating the PR: {ex!r}")
            return False

        click.echo(f"PR was created successfully: {pr.url}")
        return True


@click.group()
def cli() -> None:
    pass


def get_active_projects() -> List[str]:
    """
    Get the list of URLs of Packit projects that were active in the past year.
    """
    click.echo("Obtaining the active project URLs via Packit API...")
    now = datetime.now()
    past_year_date = now.replace(year=now.year - 1).strftime("%Y-%m-%d")
    response = requests.get(f"https://prod.packit.dev/api/usage?from={past_year_date}")
    data = response.json()
    active_project_urls = list(
        data["active_projects"]["top_projects_by_events_handled"].keys()
    )
    click.echo(f"Obtained {len(active_project_urls)} project URLs.")
    return active_project_urls


@cli.command(
    "download-configs",
    help="""
    Download configuration files of the projects that used Packit Service
     in the past year to the directory specified as config_dir.

    You may need to specify the GITHUB_TOKEN env var (and additionally
    GITLAB_TOKEN, GITLAB_GNOME_TOKEN, GITLAB_FREEDESKTOP_TOKEN)
    since there is a limit for unauthenticated API calls.

    \b
    The command creates one directory per repository containing:
        - url.txt containing git URL
        - Packit configuration file where the filename matches the filename in the repo

    \b
    Created directories structure example:
    -- github.com_namespace_repo
      -- url.txt
      -- packit.yaml
    -- gitlab.com_namespace_repo
      -- url.txt
      -- .packit.yaml


    """,
)
@click.argument(
    "config_dir",
    required=False,
    default=DEFAULT_CONFIG_DIR,
    type=click.Path(dir_okay=True, file_okay=False),
)
def download_configs(config_dir):
    repo_store_path = Path(config_dir)
    repo_store_path.mkdir(parents=True, exist_ok=True)
    project_urls = get_active_projects()

    click.echo(f"Downloading the configurations into {config_dir}...")

    with click.progressbar(project_urls) as bar:
        for url in bar:
            repo = RemoteRepositoryInfoGetter(url)
            if not repo.package_config_path or not repo.package_config:
                click.echo(f"Not able to get the package config for {url}.")
                continue

            parsed_url = urlparse(url)
            sanitized_path = re.sub(r"[^\w_-]", "_", parsed_url.path)
            dir_name = f"{parsed_url.netloc}{sanitized_path}"
            dir_path = os.path.join(config_dir, dir_name)

            Path(dir_path).mkdir(parents=True, exist_ok=True)

            file_path = os.path.join(dir_path, repo.package_config_path)
            with open(file_path, "w") as config_file:
                config_file.write(repo.package_config)

            url_file_path = os.path.join(dir_path, URL_FILE_NAME)
            with open(url_file_path, "w") as url_file:
                url_file.write(url)


@cli.command(
    "list-affected",
    help="""
    Lists URLs of affected projects (projects that use Packit configuration that
    require migrating).
    A migration file with `is_package_config_affected` function needs
    to be defined.

    Requires calling download-configs first.
    """,
)
@click.argument("migration_file", type=click.Path(exists=True))
@click.argument(
    "config_dir",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
)
def list_affected(migration_file, config_dir) -> set[str]:
    """
    Go through the config_dir and list the URLs of affected repositories
    (determined by specific migration file).
    """
    click.echo(f"Listing affected URLs from directory {config_dir}...")
    migration = Migration.from_file(migration_file)
    if not migration.is_affected_fn_present:
        click.echo(
            "Migration file doesn't contain 'is_package_config_affected' function!"
        )
        return set()

    affected = {repo.url for repo in migration.get_affected_from_directory(config_dir)}
    affected_output = "\n".join(affected)
    click.echo(f"Affected repos ({len(affected)}): \n{affected_output}")
    return affected


def show_diff(old_package_config: str, new_package_config: str):
    """
    Shows the diff for the config.
    """
    diff = difflib.unified_diff(
        old_package_config.split("\n"), new_package_config.split("\n")
    )
    diff_output = "\n".join(list(diff))
    click.echo(f"Diff of the Packit config:\n {diff_output}")


@cli.command(
    help="""
    \b
    Get the affected repositories (determined by specified migration file)
     and for each:
    - try to migrate to a format specified by the migration file
    - show the diff and ask user whether PR should be created
    - try to create fork, branch, commit and PR
    - show repos where the update was not successful

    A migration file with `is_package_config_affected` and
    `migrate_package_config` functions needs to be defined. To override the default
    commit message, 'commit_msg' variable may be defined in the migration file.

    If you want to create the updates, you need to specify the
    GITHUB_TOKEN env var (and additionally
    GITLAB_TOKEN, GITLAB_GNOME_TOKEN, GITLAB_FREEDESKTOP_TOKEN depending on the affected projects).

    Requires calling download-configs first.
    """
)
@click.option(
    "--pr_title",
    default=DEFAULT_MSG,
    show_default=True,
    help="Title for the pull request that will be created",
)
@click.argument("migration_file", type=click.Path(exists=True))
@click.argument(
    "config_dir",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
)
def migrate(pr_title: str, migration_file, config_dir: str = None):
    migration = Migration.from_file(migration_file)
    if not migration.is_affected_fn_present or not migration.migrate_fn_present:
        click.echo(
            "Migration file doesn't contain 'is_package_config_affected' "
            "or 'migrate_package_config' functions!"
        )
        return

    affected: set[LocalConfigDirectory] = migration.get_affected_from_directory(
        config_dir
    )
    not_updated = set()

    for local_repo in affected:
        click.echo(f"Migrating config for {local_repo.url} ")
        new_package_config = migration.migrate_package_config(local_repo.package_config)
        show_diff(local_repo.package_config, new_package_config)

        if not click.confirm(
            click.style(
                "Is the update correct and do you want to commit it?", fg="red"
            ),
            default=True,
        ):
            click.echo("\n===> Not updating the config.\n")
            not_updated.add(local_repo.url)
            continue

        if not PackageConfigUpdater(
            project=local_repo.project,
            config_file_name=local_repo.package_config_path.name,
            commit_msg=migration.commit_message,
            updated_packit_config=new_package_config,
            pr_title=pr_title,
        ).update():
            click.echo(f"Update for {local_repo.url} was not successful.")
            not_updated.add(local_repo.url)
        click.echo("\n\n")

    not_updated_output = "\n".join(not_updated)
    click.echo(f"Not updated repositories ({len(not_updated)}): \n{not_updated_output}")


if __name__ == "__main__":
    cli()
