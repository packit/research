#!/usr/bin/python3
""" Generate %patch, %source and %prep data about most patched Fedora spec files. """
import json
import pathlib
import re
from typing import Dict, Tuple
from bodhi.client.bindings import BodhiClient

# rpm-specs-latest.tar.xz unpacked in /fedora-spec-files/rpm-specs/
RPM_SPECS = pathlib.Path("./rpm-specs")
# process this many packages ordered by the amount of patches
PROCESS_PACKAGE_COUNT = 50
bodhi = BodhiClient()


def get_patch_stats() -> Dict[str, int]:
    """provide an ordered dict with package names as keys and number of patches as values"""
    patch_re = re.compile(r"\nPatch\d*:")
    result: Dict[str, int] = {}
    for spec in RPM_SPECS.iterdir():
        spec_content = spec.read_text()
        match = patch_re.findall(spec_content)
        if match:
            result[spec.name[:-5]] = len(match)
    return dict(sorted(result.items(), key=lambda item: item[1], reverse=True))


def get_update_frequency(package_name: str, distro: str = "f34") -> int:
    """provide number of builds a package has in koji in a given distro"""
    return len(bodhi.koji_session.listTagged(distro, package=package_name))


def get_prep_stats(package_name: str) -> Tuple[bool, bool, bool, bool]:
    """
    uses %autosetup, uses %setup, has %patch, has %autopatch
    """
    spec = RPM_SPECS / pathlib.Path(package_name + ".spec")
    spec_content = spec.read_text()

    return (
        "%autosetup" in spec_content,
        "%setup" in spec_content,
        "%patch" in spec_content,
        "%autopatch" in spec_content,
    )


print("Generating data, please hold on...", flush=True)

package_patches = get_patch_stats()

results = []

for package, num_patches in list(package_patches.items())[:PROCESS_PACKAGE_COUNT]:
    results.append(
        (
            package,
            num_patches,
        )
        + get_prep_stats(package)
        + (get_update_frequency(package),)
    )

data_json = pathlib.Path("./data.json")
if data_json.is_file():
    print("About to overwrite the existing data.json", flush=True)

with data_json.open("w") as fd:
    json.dump(results, fd, indent=2)
