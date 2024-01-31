#!/usr/bin/env python3

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import json
import sys
from collections import defaultdict, OrderedDict
from pathlib import Path

from bodhi.client.bindings import BodhiClient

from ogr import PagureService
from ogr.services.pagure import PagureProject
from specfile import Specfile


bodhi_client = BodhiClient()
RPM_SPECS = Path("./rpm-specs")
checks = []


def check_decorator(check_func):
    checks.append(check_func)

    def wrapper(package_name: str, specfile: Specfile, *args, **kwargs):
        return check_func(package_name, specfile, *args, **kwargs)

    return wrapper


@check_decorator
def check_number_of_patches(package_name: str, specfile: Specfile):
    with specfile.patches() as patches:
        patches_number = len(patches)
        print(f"Number of patches: {patches_number}")
        return patches_number <= 1


@check_decorator
def check_number_of_sources(package_name: str, specfile: Specfile):
    with specfile.sources() as sources:
        sources_number = len(sources)
        print(f"Number of sources: {sources_number}")
        return sources_number == 1


@check_decorator
def check_specfile_length(package_name: str, specfile: Specfile):
    with specfile.sections() as sections:
        try:
            changelog_index = sections.find("changelog")
        except ValueError:
            changelog_index = None
        line_count = sum(len(s) for s in sections[:changelog_index])

    print(f"Number of lines before %changelog: {line_count}")
    return line_count < 200


@check_decorator
def check_bodhi_releases(package_name: str, specfile: Specfile):
    updates = bodhi_client.query(package=package_name, releases="f39")["updates"]
    print(f"Number of updates: {len(updates)}")
    # check frequency
    if len(updates) <= 2:
        return False
    # check there is at least one non-multi-package update
    return any(len(update["builds"]) == 1 for update in updates)


def check_package_fits(package_name: str, specfile_path):
    specfile = Specfile(specfile_path)

    for check in checks:
        if not check(package_name, specfile):
            return False

    return True


def analyse_packages() -> dict[str, list]:
    maintainers_with_packages = defaultdict(list)
    number_of_fitting_packages = 0
    for i, specfile_path in enumerate(list(RPM_SPECS.iterdir())[:100], 1):
        try:
            package_name = specfile_path.name[:-5]
            print(f"Analysing {i}. package {package_name}")
            if not check_package_fits(package_name, specfile_path):
                continue

            number_of_fitting_packages += 1

            project = PagureProject(
                repo=package_name,
                namespace="rpms",
                service=PagureService(instance_url="https://src.fedoraproject.org"),
            )
            # if we want only owners, we could do project.get_owners()
            committers = project.who_can_merge_pr()

            for committer in committers:
                maintainers_with_packages[committer].append(package_name)

        except Exception as ex:
            print(ex)

    print(f"\nNumber of packages fitting the checks: {number_of_fitting_packages}")
    return dict(maintainers_with_packages)


number_of_maintainers = int(sys.argv[1]) if len(sys.argv) == 2 else 20
maintainers = analyse_packages()
maintainers_sorted = sorted(maintainers.items(), key=lambda d: len(d[1]), reverse=True)[
    :number_of_maintainers
]
data_json = Path("./maintainers.json")

with data_json.open("w") as fd:
    json.dump(OrderedDict(maintainers_sorted), fd)
