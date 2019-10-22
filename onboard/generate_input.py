from onboard.upstream_finder import UpstreamFinder


if __name__ == '__main__':
    with open('downstream_packages') as dpf:
        downstream_names = dpf.read().splitlines()
    f = UpstreamFinder(downstream_names)
    f.run()
    f.report()
    f.save_successful()
    f.save_prepared_unsuccessful()
