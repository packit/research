import os
import yaml
import urllib.request
from urllib.parse import urlparse
from urllib.error import HTTPError
from rebasehelper.specfile import SpecFile
from pprint import pprint

DOWNSTREAM_RPM_URL = 'https://src.fedoraproject.org/rpms'
SUPPORTED_UPSTREAM_HOSTS = ['github.com']


class UpstreamFinder:
    def __init__(self, downstream_package_names):
        self.downstream_names = downstream_package_names
        self.spec_unreached = []
        self.url_not_found = []
        self.results = []
        self.unsuccessful = []
        self.unsuported_hosts = []

    def fetch_spec(self, spec_url):
        print(f"Getting spec {spec_url}")
        try:
            downstream_spec, _ = urllib.request.urlretrieve(spec_url)
            return downstream_spec
        except HTTPError:
            print(f"Failed to get spec {spec_url}")
            self.spec_unreached.append(spec_url)
            return None

    @staticmethod
    def parse_sources(spec_path):
        spec = SpecFile(spec_path)
        upstream_url = ''
        for source in spec.sources:
            print(f"Parsing source: {source}")
            source_parsed = urlparse(source)
            if not source_parsed.netloc:
                print(f"netloc not found - {source}")
                continue
            if source_parsed.netloc not in SUPPORTED_UPSTREAM_HOSTS:
                print(f'unsupported upstream host found - {source_parsed.netloc}')
                # self.unsuported_hosts.append(source_parsed.netloc)
                continue
            repo_path = '/'.join(source_parsed.path.split('/')[:3])
            url = f"{source_parsed.scheme}://{source_parsed.netloc}{repo_path}"
            if not upstream_url:
                upstream_url = url
            else:
                assert upstream_url == url
        return upstream_url

    def report(self):
        print('*' * os.get_terminal_size().columns)
        print('Results:')
        if self.spec_unreached:
            print(f"Specs unreached: ({len(self.spec_unreached)})")
            print('\n'.join(self.spec_unreached))
        if self.url_not_found:
            print(f"URL not found in sources of: ({len(self.url_not_found)})")
            print('\n'.join(self.url_not_found))
        if self.unsuported_hosts:
            print(f"Found unsupported upstream hosts: {self.unsuported_hosts}")
        print(f"Found upstream urls: ({len(self.results)})")
        pprint(self.results)

    def save_successful(self):
        if not self.results:
            return
        with open('input_packages.yml','w') as f:
            yaml.dump(self.results, f)

    def save_prepared_unsuccessful(self):
        if not self.unsuccessful:
            return
        with open('input_packages.yml-add-upsstreams','w') as f:
            yaml.dump(self.unsuccessful, f)

    def run(self):
        for p in self.downstream_names:
            if not p:
                continue
            package_result = {
                'downstream_name': p,
                'upstream_url': ''
            }
            spec_url = f"{DOWNSTREAM_RPM_URL}/{p}/raw/master/f/{p}.spec"
            downstream_spec = self.fetch_spec(spec_url)
            if not downstream_spec:
                self.unsuccessful.append(package_result)
                continue
            upstream_url = self.parse_sources(downstream_spec)
            if not upstream_url:
                print(f"Failed to find upstream url for {spec_url}")
                self.url_not_found.append(spec_url)
                self.unsuccessful.append(package_result)
            else:
                package_result['upstream_url'] = upstream_url
                self.results.append(package_result)
                print(f"Upstream url = {upstream_url}")
