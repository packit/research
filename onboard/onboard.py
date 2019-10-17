import os
import sys
import yaml
from onboard.onboard_package import PackageOnboarder, formatter
import logging
from time import gmtime, strftime

logger = logging.getLogger('packit')
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)


results = []
pkg_list = yaml.safe_load(open('input_packages.yml'))
execution_date = str(strftime('%Y_%m_%d-%H_%M_%S', gmtime()))
log_dir = os.path.join(os.getcwd(), 'output', execution_date)
os.makedirs(log_dir)

latest_path = os.path.join(os.getcwd(), 'output', 'latest')
if os.path.exists(latest_path):
    os.unlink(latest_path)
os.symlink(log_dir, latest_path)

for pkg in pkg_list:
    print('*' * os.get_terminal_size().columns)
    logger.info(f"Handling package info: {pkg}")
    po = PackageOnboarder(pkg)
    results.append(po.run(log_dir=log_dir))

yaml.safe_dump(results, open(os.path.join(log_dir, "results.yml"),'w'))
