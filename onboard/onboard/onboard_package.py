import os
import yaml
import shutil
import logging
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

    def cleanup(self, log_handler=None):
        """
        Change dir back to location of onboard script. Remove cloned repository. Remove package log handler from logger.
        :param log_handler: name of handler to be removed from logger
        """
        os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        if self.repo and self.repo.working_dir:
            if os.path.exists(self.repo.working_dir):
                logger.debug('Removing repository directory: %s', self.repo.working_dir)
                shutil.rmtree(self.repo.working_dir)
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
            self.result['failure_info'] = str(ex)
            raise ex
        self.packit_local_project = LocalProject(self.repo)
        os.chdir(self.repo.working_dir)

    def get_spec_from_packit_config(self):
        """
        Get specfile path from package's packit configuration
        :return str Path to specfile
        """
        with open(self.packit_pkg_cfg) as pcf:
            pc = yaml.safe_load(pcf)
            return os.path.join(self.repo.working_dir, pc['specfile_path'])

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
            return upstream_spec_path
        if len(specs) != 0:
            msg = "Multiple specfiles in upstream, can't decide correct one"
            logger.debug(f"Specfiles:\n{str(specs)}")
            self.result['failure_info'] = msg
            raise OnboardError(msg)
        return ''

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
        return dest

    def ensure_packit_config(self):
        """
        Make sure packit configuration is in the repository
        Use packit generate when not found
        """
        self.announce_operation('Checking packit config')
        self.packit_pkg_cfg = get_existing_config(self.repo.working_dir)
        if self.packit_pkg_cfg:
            logger.info(f"Found packit config {self.packit_pkg_cfg}")

        else:
            logger.info('Packit config not found')
            self.announce_operation('Generating packit config')
            template_data = {
                "upstream_project_name": os.path.basename(self.upstream_url),
                "downstream_package_name": self.downstream_name
            }

            self.packit_pkg_cfg = os.path.join(self.repo.working_dir, '.packit.yaml')
            generate_config(
                write_to_file=True,
                template_data=template_data,
                config_file_name=self.packit_pkg_cfg,
            )
            logger.info(f"Generated new packit config {self.packit_pkg_cfg}")

    def build_srpm(self):
        """
        Run srpm build using packit API
        :return: True on success
        """
        if not self.specfile_path or not os.path.exists(self.specfile_path):
            logger.info("Specfile not provided")
            return False

        srpm_path = self.packit_api.create_srpm()
        logger.info("SRPM: %s", srpm_path)
        return True

    def _run(self):
        self.clone_repo()
        self.ensure_packit_config()

        # try running status
        self.packit_api = get_packit_api(config=self.packit_cfg, local_project=self.packit_local_project)
        # self.announce_operation('Getting status')
        # self.packit_api.status()

        # trying srpm build with upstream specfile
        self.specfile_path = self.get_upstream_spec()
        self.announce_operation("Building srpm with upstream spec")
        self.build_srpm()

        # trying srpm build with downstream specfile
        self.specfile_path = self.get_downstream_spec(dest=self.get_spec_from_packit_config())
        self.announce_operation("Building srpm with downstream spec")
        self.build_srpm()

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
            self.cleanup(log_handler=fh)
            self.result['failed_during'] = self.operation
            self.result['fail_info'] = str(ex)
            return self.result

        self.cleanup(log_handler=fh)
        self.result['successful'] = True
        return self.result

