from yaml import safe_load, safe_dump

from packit.config import JobType

commit_msg = """Add missing build job(s) to Packit config

Packit will now additionally require for each test job requiring build
a build job definition to be present in the Packit configuration file. See details
in https://github.com/packit/packit-service/issues/1775.
"""


def is_package_config_affected(package_config: str) -> bool:
    packit_config_dict = safe_load(package_config)
    jobs = packit_config_dict.get("jobs")
    if not jobs:
        return False

    test_jobs_requiring_build = [
        job
        for job in jobs
        if job.get("job") == JobType.tests.value
        and not job.get("skip_build", False)
        and not job.get("metadata", {}).get("skip_build", False)
    ]
    if not test_jobs_requiring_build:
        return False

    for test_job in test_jobs_requiring_build:
        build_jobs_with_same_trigger = [
            job
            for job in jobs
            if job.get("job") in (JobType.copr_build.value, JobType.build.value)
            and job.get("trigger") == test_job.get("trigger")
        ]
        if not build_jobs_with_same_trigger:
            return True

    return False


def migrate_package_config(package_config: str) -> str:
    packit_config_dict = safe_load(package_config)
    jobs = packit_config_dict.get("jobs")

    test_jobs_without_build_job = get_affected_test_jobs(jobs)
    new_jobs = create_missing_build_jobs(test_jobs_without_build_job)

    jobs_section_string = "jobs:"
    jobs_idx = package_config.index(jobs_section_string) + len(jobs_section_string)

    first_job_line = [line for line in package_config.split("\n") if "job:" in line][0]
    job_indentation = len(first_job_line) - len(first_job_line.lstrip())

    lines_to_add = "\n".join(
        (" " * job_indentation) + line
        for line in safe_dump(new_jobs, sort_keys=False).split("\n")
    )

    migrated_config = (
        package_config[:jobs_idx] + "\n" + lines_to_add + package_config[jobs_idx:]
    )

    return migrated_config


def get_affected_test_jobs(jobs: list) -> list:
    test_jobs_requiring_build = [
        job
        for job in jobs
        if job.get("job") == JobType.tests.value
        and not job.get("skip_build", False)
        and not job.get("metadata", {}).get("skip_build", False)
    ]

    test_jobs_without_build_job = []

    # collect the test jobs without corresponding build job
    for test_job in test_jobs_requiring_build:
        build_jobs = [
            job
            for job in jobs
            if job.get("job") in (JobType.copr_build.value, JobType.build.value)
            and job.get("trigger") == test_job.get("trigger")
        ]
        if not build_jobs:
            test_jobs_without_build_job.append(test_job)

    return test_jobs_without_build_job


def create_missing_build_jobs(test_jobs_without_build_job: list) -> list:
    """
    Go through the test jobs without build definition and create one for each.
    """
    new_jobs = []
    for test_job_without_build in test_jobs_without_build_job:
        targets = test_job_without_build.get("targets") or test_job_without_build.get(
            "metadata", {}
        ).get("targets")
        build_job = {
            "job": "copr_build",
            "trigger": test_job_without_build.get("trigger"),
            "targets": targets,
        }
        new_jobs.append(build_job)
    return new_jobs
