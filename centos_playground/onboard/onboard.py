import os
from git import Repo
from ogr.services.pagure import PagureService
from ogr.abstract import AccessLevel

from survey import CentosPkgValidatedConvert


service = PagureService(token=os.getenv('PAGURE_TOKEN'),
                        instance_url='https://git.stg.centos.org/')


class OnboardCentosPKG():
    def __init__(self, pkg_name):
        self.pkg_name = pkg_name
        self.converter = CentosPkgValidatedConvert({
            'fullname': f'rpms/{pkg_name}',
            'name': pkg_name,
        })

    def run(self):
        if service.get_project(namespace='source-git', repo=self.pkg_name).exists():
            print(f'Source repo for {self.pkg_name} already exists')
            return
        self.converter.run()
        print(self.converter.result)
        with open('/in/result.yml', 'a+') as out:
            out.write(f'{self.converter.result}\n')
        if not self.converter.result or \
                "error" in self.converter.result or \
                "conditional_patch" in self.converter.result:
            print(f'Onboard aborted for {self.pkg_name}:')
            return
        print(f'Onboard successful for {self.pkg_name}:')
        new_project = service.project_create(
            repo=self.pkg_name,
            namespace='source-git',
            description=f"Source git repo for {self.pkg_name}.\n"
                        f"For more info see: http://packit.dev/docs/source-git/")

        new_project.add_user('centosrcm', AccessLevel.maintain)
        new_project.add_group('git-packit-team', AccessLevel.maintain)
        git_repo = Repo(self.converter.src_dir)
        git_repo.create_remote('packit', new_project.get_git_urls()['ssh'])
        git_repo.git.push('packit', 'c8', tags=True)


if __name__ == '__main__':
    os.makedirs('/tmp/playground/rpms', exist_ok=True)
    with open('/in/input-pkgs.yml', 'r') as f:
        in_pkgs = f.readlines()

    for pkg in in_pkgs:
        print(f'Onboarding {pkg}')
        ocp = OnboardCentosPKG(pkg.strip())
        ocp.run()
        ocp.converter.cleanup()
