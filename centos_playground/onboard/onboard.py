import os
import sys
from typing import List

from git import Repo

from ogr import GitlabService
from ogr.services.gitlab import GitlabProject
from ogr.services.pagure import PagureService
from ogr.abstract import AccessLevel, GitService

from survey import CentosPkgValidatedConvert
from add_master_branch import AddMasterBranch

DEFAULT_BRANCH = "c8s"


class OnboardCentosPKG:
    def __init__(
        self,
        service: GitService,
        namespace: str,
        maintainers: List[str],
        maintainers_group: List[str],
    ):
        self.service = service
        self.namespace = namespace
        self.maintainers = maintainers
        self.maintainers_group = maintainers_group

    def run(self, pkg_name, branch):
        converter = CentosPkgValidatedConvert(
            {
                "fullname": f"rpms/{pkg_name}",
                "name": pkg_name,
            },
            distgit_branch=branch,
        )

        project = self.service.get_project(namespace=self.namespace, repo=pkg_name)
        if project.exists():
            print(f"Source repo for {pkg_name} already exists")
            if (
                isinstance(project, GitlabProject)
                and project.gitlab_repo.visibility == "private"
            ):
                print("Making the repository public.")
                project.gitlab_repo.visibility = "public"
                project.gitlab_repo.save()

            return
        converter.run(skip_build=False)
        print(converter.result)
        with open("/in/result.yml", "a+") as out:
            out.write(f"{converter.result}\n")
        if (
            not converter.result
            or "error" in converter.result
            or converter.result.get("conditional_patch")
        ):
            print(f"Onboard aborted for {pkg_name}:")
            return
        print(f"Onboard successful for {pkg_name}:")
        print(
            f"Creating source-git repo: {self.namespace}/{pkg_name} at {self.service.instance_url}"
        )
        new_project = self.service.project_create(
            repo=pkg_name,
            namespace=self.namespace,
            description=f"Source git repo for {pkg_name}.\n"
            f"For more info see: http://packit.dev/docs/source-git/",
        )
        print(f"Project created: {new_project.get_web_url()}")

        if isinstance(new_project, GitlabProject):
            new_project.gitlab_repo.visibility = "public"
            new_project.gitlab_repo.save()

        for maintainer in self.maintainers:
            new_project.add_user(maintainer, AccessLevel.maintain)
        for group in self.maintainers_group:
            new_project.add_group(group, AccessLevel.maintain)

        git_repo = Repo(converter.src_dir)
        git_repo.create_remote("packit", new_project.get_git_urls()["ssh"])
        git_repo.git.push("packit", branch, tags=True)

        if isinstance(self.service, PagureService):
            add_master = AddMasterBranch(pkg_name)
            add_master.run()
        converter.cleanup()


if __name__ == "__main__":

    pagure_token = os.getenv("PAGURE_TOKEN")
    gitlab_token = os.getenv("GITLAB_TOKEN")
    if pagure_token:

        ocp = OnboardCentosPKG(
            service=PagureService(
                token=pagure_token, instance_url="https://git.stg.centos.org/"
            ),
            namespace="source-git",
            maintainers=["centosrcm"],
            maintainers_group=["git-packit-team"],
        )
    elif gitlab_token:
        ocp = OnboardCentosPKG(
            service=GitlabService(
                token=gitlab_token, instance_url="https://gitlab.com"
            ),
            namespace="packit-service/src",
            maintainers=[],
            maintainers_group=[],
        )
    else:
        print("Define PAGURE_TOKEN or GITLAB_TOKEN")
        sys.exit(1)

    os.makedirs("/tmp/playground/rpms", exist_ok=True)
    with open("/in/input-pkgs.yml", "r") as f:
        in_pkgs = f.readlines()

    for pkg in in_pkgs:
        if not pkg.strip() or pkg.startswith("#"):
            continue

        split = pkg.strip().split(":", maxsplit=1)
        if len(split) == 2:
            package, branch = split
        else:
            package, branch = split[0], DEFAULT_BRANCH
        print(f"Onboarding {package} using '{branch}' branch")
        ocp.run(pkg_name=package, branch=branch)
