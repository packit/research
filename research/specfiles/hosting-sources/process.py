#!/usr/bin/env python3

import gzip
from urllib.parse import urlparse

import click


IGNORED_PROTOCOLS = {
    "",  # None → local files from lookaside cache
    "file",  # same as previous
}
USUAL_PROTOCOLS = {
    "",  # local files; lookaside cache
    "http",
    "https",
    "ftp",
}


def _parse(filename):
    click.echo(click.style("\n=== Parsing sources ===", fg="green"))

    lines = None
    with gzip.open(filename, "rt") as f:
        lines = [line.strip() for line in f]

    return [urlparse(line.split()[1]) for line in lines]


def _check_schemes(sources):
    click.echo(click.style("\n=== Checking schemes ===", fg="green"))

    click.echo(
        "Found schemes: {schemes}".format(schemes={source.scheme for source in sources})
    )
    for source in sources:
        if source.scheme not in USUAL_PROTOCOLS:
            click.echo(source)


def _check_domains(sources):
    click.echo(click.style("\n=== Checking domains ===", fg="green"))

    domains = {
        source.hostname.removeprefix("www.")
        for source in sources
        if source.scheme not in IGNORED_PROTOCOLS
    }
    click.echo("Found domains: {}".format(domains))
    click.echo("Count: {}".format(len(domains)))

    innermost_domains = [
        source.hostname.split(".")[0]
        for source in sources
        if source.scheme not in IGNORED_PROTOCOLS
        and len(source.hostname.split(".")) > 2
    ]
    freqs = {}
    for part in innermost_domains:
        freqs[part] = freqs.get(part, 0) + 1

    freqs_list = list(freqs.items())
    freqs_list.sort(key=lambda f: f[1])

    for domain, count in freqs_list:
        click.echo(f"{count}\t{domain}")

    return domains


def _check_freqs(sources, domains):
    click.echo(click.style("\n=== Checking frequences of domains ===", fg="green"))

    freqs = {}
    for source in sources:
        if source.scheme in ("", "file"):
            continue

        domain = "{scheme}://{host}".format(
            scheme=source.scheme, host=source.hostname.removeprefix("www.")
        )
        freqs[domain] = freqs.get(domain, 0) + 1

    freqs_list = list(freqs.items())
    freqs_list.sort(key=lambda f: f[1])

    for domain, count in freqs_list:
        click.echo(f"{count}\t{domain}")

    with open("domains.txt", "w") as f:
        for domain, count in reversed(freqs_list):
            print(domain, file=f)


@click.command()
@click.argument("filename")
def run(filename):
    sources = _parse(filename)
    _check_schemes(sources)
    domains = _check_domains(sources)
    _check_freqs(sources, domains)


if __name__ == "__main__":
    run()
