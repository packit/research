---
title: Local Testing of RPMs
authors: kayodegigz
---

Enable Packit to locally run TMT tests against RPMs built for specific targets (e.g., fedora-39-x86_64) to mirror what CI does via Testing Farm, but without uploading to a public repo.
The high level end goal of this would be to have a new packit command called "test", which would allow us to run tests on an rpm `while mirroring packit CI scenarios locally.
```bash
packit test --rpm_path=path/to/local/rpm
```

## Use cases

- Easy installation and testing of rpms locally to mirror what happens on packit CI
- Faster feedback loops and easy debugging
- Catching errors early before raising a PR/release
- Testing the changes on as many Fedora distros as are defined by the user(in the test plans)

## Implementation Plan
- Build rpm locally
- Provision TMT environment to match the target.
- Automatically install the RPM into the provisioned environment.
- Run tests using `tmt run`.

### Step 1: Build the RPM Locally
This step is valuable when there's no rpm path specified. In this case we create an rpm with the content of the upstream repository and return the path.

```bash
packit build in-mock -r=fedora-40-x86_64
```
This create an RPM in mock using content of the upstream repository.

### Step 2: validate rpm exists
This step just checks if the rpm_path(whether user defined or generated) exists. If it doesn't exist I think an error should be thrown.

### Step 3: Provision Matching TMT Environment
When the rpm_path is validated, then we proceed to provision a local environment for tmt- container or virtual(local is discouraged because of the unpredictable side effects). This is done using the provision step in the fmf file. We also need to ensure image or distro specified in the fmf file matches the target in the packit config.
#### P.S: I think we should also allow the sub-commands(eg provision --how=container) with the packit test command too(eg packit test provision --how=container). This would allow the user override the content of the fmf file with the cli commands. So basically we're reading the tmt steps from the fmf file ourselves, overriding them - if the user passed the commands via cli, and "calling" tmt via the full cli command. 
#### We probably wouldn't be able to directly run the command "tmt run --all" if we're going with the above, since that command would pick the test plans

### Step 4: Install the RPM into the Provisioned Env
The rpm should be installed into the fresh environment provisioned in step 3. The command used would be this.

```bash
tmt run prepare --how=install --package=our/rpm/path/from/step/1
```

### Step 5: Run Tests with TMT
Execute the test plan as usual with:
```bash
tmt run
```
with all its passed commands/subcommands.

We should handle:
- Mapping the --target to a proper image/distro in the TMT plan
- Injecting the built RPM
- Triggering tmt run


#### Questions
- How do we ensure distro/image mapping stays consistent with TMT? Do we want to trow an error when there's a mismatch?

Feel free to leave comments or suggestions!
