import git
import os
import re
import requests
import subprocess
import shutil
import yaml

from git import Repo
from packit.config import Config
from packit.cli.utils import get_packit_api
from packit.local_project import LocalProject

work_dir = '/tmp/playground'
result = []
packit_conf = Config.get_user_config()


class CentosPackageSurvey:
    def __init__(self, project_info):
        self.project_info = project_info
        self.src_dir = ""
        self.rpm_dir = ""
        self.pkg_res = {}

    def clone(self):
        git_url = f"https://git.centos.org/{self.project_info['fullname']}"
        try:
            Repo.clone_from(git_url, f"{work_dir}/rpms/{self.project_info['name']}", branch="c8s")
            return True
        except git.exc.GitCommandError as ex:
            if 'Remote branch c8s not found' in str(ex):
                return False

    def run_srpm(self):
        try:
            packit_api = get_packit_api(config=packit_conf, local_project=LocalProject(Repo(self.src_dir)))
            packit_api.create_srpm(srpm_dir=self.src_dir)
        except Exception as e:
            self.pkg_res['error'] = f"SRPMError: {e}"

    def convert(self):
        try:
            output = subprocess.check_output(['/tmp/playground/dist2src.py',
                                              'convert',
                                              f"{self.rpm_dir}:c8s",
                                              f"{self.src_dir}:c8s"],
                                             timeout=300)
            return not bool(output)
        except Exception as ex:
            self.pkg_res['error'] = f"ConvertError: {ex}"
            return False

    def cleanup(self):
        if os.path.exists(self.rpm_dir):
            shutil.rmtree(self.rpm_dir)
        if os.path.exists(self.src_dir):
            shutil.rmtree(self.src_dir)

    def run(self):
        if not self.clone():
            return
        self.rpm_dir = f"{work_dir}/rpms/{self.project_info['name']}"
        self.src_dir = f"{work_dir}/src/{self.project_info['name']}"

        with open(f"{self.rpm_dir}/SPECS/{self.project_info['name']}.spec", "r") as spec:
            spec_cont = spec.read()
            self.pkg_res.update({
                "package_name": self.project_info['name'],
                "autosetup": bool(re.search(r'\n%autosetup', spec_cont)),
                "setup": bool(re.search(r'\n%setup', spec_cont)),
                "conditional_patch": bool(re.findall(r'\n%if.*?\n%patch.*?\n%endif', spec_cont, re.DOTALL)),
            })

        if self.convert():
            self.run_srpm()
            self.pkg_res['size'] = subprocess.check_output(['du', '-s', self.src_dir]).split()[0].decode('utf-8')
        else:
            self.pkg_res['size_rpms'] = subprocess.check_output(['du', '-s', self.rpm_dir]).split()[0].decode('utf-8')
        self.cleanup()


def fetch_centos_pkgs_info(page):
    i = 0
    while True:
        r = requests.get(page)
        for p in r.json()["projects"]:
            cps = CentosPackageSurvey(p)
            cps.run()
            if cps.pkg_res:
                print(cps.pkg_res)
                result.append(cps.pkg_res)
        page = r.json()["pagination"]["next"]
        if not page:
            break
        i = i+1
        if not (i % 2):
            with open('intermediate-result.yml', 'w') as outfile:
                yaml.dump(result, outfile)

#TODO: store convert stderr in a nice way
#TODO: better logging - page numbers and visibly separated single runs
#TODO: mockbuild - with reasonable timeout
#TODO: add other branches that are relevant for us
#TODO: failsafe for unexpected spec name (e.g https://git.centos.org/rpms/gcc-toolset-9-annobin/blob/c8s/f/SPECS/annobin.spec)

if __name__ == '__main__':
    fetch_centos_pkgs_info('https://git.centos.org/api/0/projects?namespace=rpms&owner=centosrcm&short=true&page=42')
    with open('result-data.yml', 'w') as outfile:
        yaml.dump(result, outfile)

