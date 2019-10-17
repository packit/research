import os
import yaml
import jinja2
import shutil
import logging
import traceback
import urllib.request
from urllib.error import HTTPError
from pathlib import Path
from packit.utils import get_repo
from packit.cli.generate import generate_config, get_existing_config
from packit.cli.utils import get_packit_api
from packit.config import Config
from packit.local_project import LocalProject

logger = logging.getLogger('packit')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)-7s |%(name)s: %(message)s')
DOWNSTREAM_RPM_URL = 'https://src.fedoraproject.org/rpms/'
WHOAMI = os.getenv('USER')
ONBOARD_BRANCH_NAME = 'packit-onboard-w-copr'

logging.getLogger('packit').setLevel(logging.DEBUG)


class OnboardError(Exception):
    pass


class PackageOnboarder:
    def __init__(self, info):
        self.upstream_url = info['upstream_url']
        self.downstream_name = info['downstream_name']
        self.repo = None
        self.result = {
            'downstream_name': info['downstream_name'],
            'successful': False
        }
        self.operation = ''
        self.downstream_spec = ''
        self.packit_cfg = Config.get_user_config()
        self.packit_local_project = None
        self.packit_api = None
        self.pkg_cfg_path = ''
        self.pkg_cfg = None
        self.git_project = None

    def cleanup(self, log_handler=None):
        """
        Change dir back to location of onboard script. Remove cloned repository. Remove package log handler from logger.
        :param log_handler: name of handler to be removed from logger
        """
        os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        if self.repo and self.repo.working_dir:
            if os.path.exists(self.repo.working_dir):
                logger.debug('Removing repository directory: %s', self.repo.working_dir)
                # shutil.rmtree(self.repo.working_dir)
        if log_handler:
            logger.removeHandler(log_handler)

    def announce_operation(self, op):
        """
        Set actual operation and make it more visible in logs
        :param op: Name of operation
        """
        self.operation = op
        logger.info('-' * len(op))
        logger.info(f"\033[1m{self.operation}\033[0m")
        logger.info('-' * len(op))

    def clone_repo(self):
        """
        Clone upstream repository to tmp and chdir
        :return:
        """
        self.announce_operation('Cloning upstream')
        try:
            self.repo = get_repo(url=self.upstream_url)
        except Exception as ex:
            logger.error(f"Failed to clone {self.upstream_url}")
            raise ex
        self.packit_local_project = LocalProject(self.repo)
        self.git_project = self.packit_cfg.get_project(self.upstream_url)
        os.chdir(self.repo.working_dir)

    def get_spec_from_packit_config(self):
        """
        Get specfile path from package's packit configuration
        :return str Path to specfile
        """
        return os.path.join(self.repo.working_dir, self.pkg_cfg['specfile_path'])

    def get_upstream_spec(self):
        """
        Get specfile path in upstream. Look at path found in packit config
        When not found, try to find any other file with postfix spec.
        :return: str path to upstream specfile or empty
        """
        self.announce_operation('Getting upstream spec')
        from_config = self.get_spec_from_packit_config()
        if os.path.exists(from_config):
            logger.debug(f"Using upstream spec {from_config}")
            return from_config

        # Try to find other spec files
        specs = [str(x) for x in Path(self.repo.working_dir).glob('**/*.spec')]
        if len(specs) == 1:
            upstream_spec_path = specs[0]
            logger.debug(f"Using upstream spec {upstream_spec_path}")
            self.pkg_cfg['specfile_path'] = upstream_spec_path[len(self.packit_local_project.working_dir)+1:]
            self.dump_cfg()
            return upstream_spec_path
        if len(specs) != 0:
            msg = "Multiple specfiles in upstream, can't decide correct one"
            logger.debug(f"Specfiles:\n{str(specs)}")
            self.result['failure_info'] = msg
            raise OnboardError(msg)
        return None

    def get_downstream_spec(self, dest):
        """
        Download specfile from downstream repository and store it in dest
        :param dest: path dest to store the specfile
        """
        self.announce_operation('Getting downstream spec')
        url = f"{DOWNSTREAM_RPM_URL}/{self.downstream_name}/raw/master/f/{self.downstream_name}.spec"
        try:
            downstream_spec, _ = urllib.request.urlretrieve(url)
        except HTTPError as ex:
            msg = f"Failed to fetch spec from downstream repo ({url})"
            self.result['failure_info'] = msg
            raise OnboardError(msg)
        shutil.copy(downstream_spec, dest)
        # Adding the spec before packit srpm makes changes on it
        self.packit_local_project.git_repo.index.add([dest])
        return dest

    def load_packit_config(self):
        """
        Make sure packit configuration is in the repository
        Use packit generate when not found
        """
        self.announce_operation('Checking packit config')
        self.pkg_cfg_path = get_existing_config(Path(self.repo.working_dir))
        if self.pkg_cfg_path:
            logger.info(f"Found packit config {self.pkg_cfg_path}")
            self.result['already_had_packit_conf'] = True
        else:
            logger.info('Packit config not found')
            self.result['already_had_packit_conf'] = False
            self.announce_operation('Generating packit config')
            template_data = {
                "upstream_package_name": os.path.basename(self.upstream_url),
                "downstream_package_name": self.downstream_name
            }

            self.pkg_cfg_path = Path(self.repo.working_dir) / '.packit.yaml'
            generate_config(
                config_file=self.pkg_cfg_path,
                write_to_file=True,
                template_data=template_data,
            )
            logger.info(f"Generated new packit config {self.pkg_cfg_path}")

        with open(self.pkg_cfg_path) as pcf:
            self.pkg_cfg = yaml.safe_load(pcf)

    def dump_cfg(self):
        logger.info(f"Dumping new version of {self.pkg_cfg_path}")
        logger.info(self.pkg_cfg)
        with open(self.pkg_cfg_path, 'w') as pcf:
            yaml.safe_dump(self.pkg_cfg, pcf)
        # reload packit API
        self.packit_api = get_packit_api(config=self.packit_cfg,
                                         local_project=self.packit_local_project)

    def build_srpm(self):
        """
        Run srpm build using packit API
        :return: True on success
        """
        srpm_path = self.packit_api.create_srpm()
        logger.info("SRPM: %s", srpm_path)
        return True

    def build_pr_text(self):
        template_loader = jinja2.FileSystemLoader(searchpath=str(Path(__file__).parent / "data/"))
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template('pr_template.txt.j2')
        output_text = template.render(template_data={
            'first_contact': not self.result['already_had_packit_conf'],
            'spec_fetched': self.result['downstream_spec_used']
        })
        logger.warning('New PR text:')
        logger.debug(output_text)
        return output_text

    def enable_copr_builds(self):
        self.announce_operation("Enabling copr builds")
        if not self.pkg_cfg.get('jobs'):
            self.pkg_cfg['jobs'] = []
        else:
            if 'copr_build' in [x['job'] for x in self.pkg_cfg['jobs']]:
                self.result['already_copr_enabled'] = True
                return
        self.result['already_copr_enabled'] = False
        copr_job = {
          'job': 'copr_build',
          'trigger': 'pull_request',
          'metadata': {
            'targets': [
              'fedora-29-x86_64',
              'fedora-30-x86_64',
              'fedora-31-x86_64',
              'fedora-rawhide-x86_64'
            ]
          }
        }
        self.pkg_cfg['jobs'].append(copr_job)
        self.dump_cfg()

    def prepare_fork(self):
        gr = self.packit_local_project.git_repo
        if not self.git_project.is_forked():
            logger.debug(f"Creating new fork for {WHOAMI}")
            fork = self.git_project.fork_create()
        else:
            logger.debug('Using already existing fork')
            fork = self.git_project.get_fork()

        if WHOAMI not in [r.name for r in gr.remotes]:
            logger.debug(f"Adding remote {WHOAMI} - {fork.get_git_urls()['ssh']}")
            gr.create_remote(WHOAMI, fork.get_git_urls()['ssh'])
        return fork

    def is_onboared(self):
        if not self.git_project.is_forked():
            return False
        fork = self.git_project.get_fork()
        # WHILE onboarding pr is in review, branch is existing. When the PR is merged and the branch gets
        # deleted for some reason anyway, the onboarding will have no effect (because no PR would be required)
        # But this works only for one user :(
        if ONBOARD_BRANCH_NAME in fork.get_branches():
            return True

    def push_and_create_pr(self):
        if not self.result['already_had_packit_conf']:
            subject = 'Enable copr builds and add packit config'
        else:
            subject = 'Enable copr builds for packit config'
        fork = self.prepare_fork()

        # commit
        logger.info("Creating commit")
        self.packit_local_project.git_repo.index.add([str(self.pkg_cfg_path)])
        self.packit_local_project.git_repo.index.commit(subject)

        # push
        logger.info("Pushing")
        r = self.packit_local_project.git_repo.remote(WHOAMI)
        r.push()

        body = self.build_pr_text()
        logger.info("Creating PR")
        self.git_project.pr_create(
            title=subject,
            body=body,
            target_branch='master',
            source_branch=f"{WHOAMI}:{ONBOARD_BRANCH_NAME}"
        )

    def _run(self):
        self.clone_repo()
        self.load_packit_config()

        # try running status
        self.packit_api = get_packit_api(config=self.packit_cfg,
                                         local_project=self.packit_local_project)

        if self.is_onboared():
            self.result['skipped'] = True
            logger.info(f"Project already has a branch {ONBOARD_BRANCH_NAME} in {WHOAMI} namespace. Skipping.")
            return

        # TODO: https://github.com/packit-service/packit/issues/570
        # self.announce_operation('Getting status')
        # self.packit_api.status()

        self.packit_local_project.git_repo.create_head(ONBOARD_BRANCH_NAME).checkout()
        up_spec = self.get_upstream_spec()
        if up_spec and os.path.exists(up_spec):
            self.announce_operation("Building srpm with upstream spec")
            self.result['downstream_spec_used'] = False
            self.build_srpm()
        else:
            self.result['downstream_spec_used'] = True
            down_spec = self.get_spec_from_packit_config()
            self.announce_operation("Building srpm with downstream spec")
            self.get_downstream_spec(dest=down_spec)
            self.build_srpm()

        self.enable_copr_builds()
        if self.result['already_had_packit_conf'] and self.result['already_copr_enabled']:
            logger.info(f"Repo had already copr enabled in packit")
            return

        self.push_and_create_pr()

    def run(self, log_dir):
        """
        Try running onboard operations on package

        :param log_dir: Directory where to store results
        :return: dict of result info
        """
        log_file = os.path.join(log_dir, f"{self.downstream_name}")
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info(f"Handling package {self.downstream_name} from upstream url {self.upstream_url}")

        try:
            self._run()
        except Exception as ex:
            logger.error(ex)
            traceback.print_exc()
            self.cleanup(log_handler=fh)
            self.result['failed_during'] = self.operation
            self.result['fail_info'] = str(ex)
            return self.result

        self.cleanup(log_handler=fh)
        self.result['successful'] = True
        return self.result
