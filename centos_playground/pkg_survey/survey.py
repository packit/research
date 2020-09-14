import git
import os
import re
import requests
import subprocess
import shutil
import yaml

from click.testing import CliRunner
from packit.config import Config
from packit.cli.utils import get_packit_api
from packit.local_project import LocalProject
from pathlib import Path
from dist2src.core import Dist2Src

work_dir = '/tmp/playground'
rpms_path = f"{work_dir}/rpms"
result = []
packit_conf = Config.get_user_config()
runner = CliRunner()
BRANCH = "c8"


class CentosPkgValidatedConvert:
    def __init__(self, project_info):
        self.project_info = project_info
        self.src_dir = ""
        self.rpm_dir = ""
        self.result = {}
        self.srpm_path = ""

    def clone(self):
        git_url = f"https://git.centos.org/{self.project_info['fullname']}"
        try:
            git.Git(rpms_path).clone(git_url)
            r = git.Repo(f"{rpms_path}/{self.project_info['name']}")
            r.git.checkout(BRANCH)
            return True
        except Exception as ex:
            if f'Remote branch {BRANCH} not found' in str(ex):
                return False
            self.result["package_name"] = self.project_info['name']
            self.result['error'] = f"CloneError: {ex}"
            return False

    def run_srpm(self):
        try:
            self.packit_api = get_packit_api(config=packit_conf, local_project=LocalProject(git.Repo(self.src_dir)))
            self.srpm_path = self.packit_api.create_srpm(srpm_dir=self.src_dir)
        except Exception as e:
            self.result['error'] = f"SRPMError: {e}"

    def convert(self):
        try:
            self.d2s = Dist2Src(
                dist_git_path=Path(self.rpm_dir),
                source_git_path=Path(self.src_dir),
            )
            self.d2s.convert(BRANCH, BRANCH)
            return True
        except Exception as ex:
            self.result['error'] = f"ConvertError: {ex}"
            return False

    def cleanup(self):
        if os.path.exists(self.rpm_dir):
            shutil.rmtree(self.rpm_dir)
        if os.path.exists(self.src_dir):
            shutil.rmtree(self.src_dir)

    def do_mock_build(self):
        c = subprocess.run(['mock', '-r', 'centos-stream-x86_64', 'rebuild', self.srpm_path])
        if not c.returncode:
            return
        self.result['error'] = f'mock build failed'

    @staticmethod
    def get_conditional_info(spec_cont):
        conditions = re.findall(r'\n%if.*?\n%endif', spec_cont, re.DOTALL)
        result = []
        p = re.compile("\n%if (.*)\n")
        for con in conditions:
            if '\n%patch' in con:
                found = p.search(con)
                if found:
                    result.append(found.group(1))
        return result

    def run(self, cleanup=False):
        if not self.clone():
            return

        self.rpm_dir = f"{rpms_path}/{self.project_info['name']}"
        self.src_dir = f"{work_dir}/src/{self.project_info['name']}"

        self.result["package_name"] = self.project_info['name']
        specfile_path = f"{self.rpm_dir}/SPECS/{self.project_info['name']}.spec"
        if not os.path.exists(specfile_path):
            self.result['error'] = 'Specfile not found.'
            self.cleanup()
            return

        with open(specfile_path, "r") as spec:
            spec_cont = spec.read()
            self.result.update({
                "autosetup": bool(re.search(r'\n%autosetup', spec_cont)),
                "setup": bool(re.search(r'\n%setup', spec_cont)),
                "conditional_patch": self.get_conditional_info(spec_cont),
            })

        if not self.convert():
            self.result['size_rpms'] = subprocess.check_output(['du', '-s', self.rpm_dir]).split()[0].decode('utf-8')
        else:
            self.run_srpm()
            self.result['size'] = subprocess.check_output(['du', '-s', self.src_dir]).split()[0].decode('utf-8')
            if self.srpm_path:
                self.do_mock_build()
        if cleanup:
            self.cleanup()


def fetch_centos_pkgs_info(page):
    i = 0
    while True:
        print(page)
        r = requests.get(page)
        for p in r.json()["projects"]:
            print(f"Processing package: {p['name']}")
            converter = CentosPkgValidatedConvert(p)
            converter.run(cleanup=True)
            if converter.result:
                print(converter.result)
                result.append(converter.result)
        page = r.json()["pagination"]["next"]
        if not page:
            break
        i = i+1
        if not (i % 2):
            with open('intermediate-result.yml', 'w') as outfile:
                yaml.dump(result, outfile)


if __name__ == '__main__':
    if not os.path.exists(work_dir):
        print("Your work_dir is missing.")
    if not os.path.exists(rpms_path):
        os.mkdir(rpms_path)
    if not os.path.exists(f"mock_error_builds"):
        os.mkdir(f"mock_error_builds")
    fetch_centos_pkgs_info('https://git.centos.org/api/0/projects?namespace=rpms&owner=centosrcm&short=true')
    with open('result-data.yml', 'w') as outfile:
        yaml.dump(result, outfile)

