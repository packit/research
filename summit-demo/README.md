# This is how I totally not faked the demo

## Create project

1. Go here https://git.stg.centos.org/

2. Log in. (use prod credentials, there doesn't seem to be stg.accounts)

3. Create an API token.

Now the code I ran:

```python
In [1]: import ogr

In [2]: s = ogr.PagureService(token="da_token", instance_url="https://git.stg.centos.org/")

In [4]: s.get_api_url()
Out[4]: 'https://git.stg.centos.org//api/0/'

In [9]: p = s.project_create(repo="rpm-demo", namespace="source-git")
```

And voilà... https://git.stg.centos.org/source-git/rpm-demo

Now we need to grant our group the commit access (use packit's token - it can be found in secrets/stg/p-s.yaml):
```python
In [21]: s.change_token('the-token')

In [30]: mod_acls = {
    ...:     'user_type': 'group',
    ...:     'name': 'git-packit-team',
    ...:     'acl': 'commit',
    ...: }

In [31]: s.call_api(u + 'source-git/rpm-demo/git/modifyacls', "POST", data=mod_acls)
```

## Push stuff

Let's push rpm source-git content to the repo.

```
$ upsint fork packit-service-testing-organisation/source-git-rpm
16:11:33 INFO   forking repo packit-service-testing-organisation/source-git-rpm to TomasTomecek
16:11:34 DEBUG  clone git@github.com:TomasTomecek/source-git-rpm.git
Cloning into 'source-git-rpm'...
remote: Enumerating objects: 1373, done.
remote: Counting objects: 100% (1373/1373), done.
remote: Compressing objects: 100% (777/777), done.
remote: Total 1373 (delta 490), reused 1372 (delta 489), pack-reused 0
Receiving objects: 100% (1373/1373), 5.03 MiB | 1.17 MiB/s, done.
Resolving deltas: 100% (490/490), done.
16:11:41 DEBUG  clone return code: 0
16:11:41 DEBUG  set remote upstream to https://github.com/packit-service-testing-organisation/source-git-rpm.git
16:11:41 DEBUG  adding fetch rule to get PRs for upstream
16:11:41 DEBUG  set remote origin to git@github.com:TomasTomecek/source-git-rpm.git
16:11:41 DEBUG  adding fetch rule to get PRs for origin
16:11:41 DEBUG  fetching everything
remote: Enumerating objects: 8, done.
remote: Counting objects: 100% (8/8), done.
remote: Compressing objects: 100% (2/2), done.
remote: Total 6 (delta 4), reused 6 (delta 4), pack-reused 0
Unpacking objects: 100% (6/6), 1.26 KiB | 214.00 KiB/s, done.
From https://github.com/packit-service-testing-organisation/source-git-rpm
 * [new ref]         refs/pull/1/head    -> upstream/pr/1
 * [new ref]         refs/pull/2/head    -> upstream/pr/2
 * [new ref]         refs/pull/3/head    -> upstream/pr/3
 * [new branch]      a-downstream-change -> upstream/a-downstream-change
 * [new branch]      c8s                 -> upstream/c8s
 * [new branch]      master              -> upstream/master
From github.com:packit-service-testing-organisation/source-git-rpm
 * [new branch]      a-downstream-change -> upstream-w/a-downstream-change
 * [new branch]      c8s                 -> upstream-w/c8s
 * [new branch]      master              -> upstream-w/master

$ cd packit-service-testing-organisation/source-git-rpm
```

The main change I did in source-git was to move the spec to `SPECS/*.spec` so
they are compatible with dist-git and one can cherry-pick patches from there.

```
$ packit srpm
Packit 0.8.2.dev117+g68cd942 is being used.
Input is a directory: /home/tt/g/packit-service-testing-organisation/source-git-rpm
Input directory is an upstream repository.
100%[=============================>]     3.96M  eta 00:00:00
66 patches added to /home/tt/g/packit-service-testing-organisation/source-git-rpm/centos-packaging/SPECS/rpm.spec
SRPM is /home/tt/g/packit-service-testing-organisation/source-git-rpm/rpm-4.14.2-37.g824233d8.fc31.src.rpm
SRPM: /home/tt/g/packit-service-testing-organisation/source-git-rpm/rpm-4.14.2-37.g824233d8.fc31.src.rpm
```

Werks, nice!

```
$ git remote add sg ssh://git@git.stg.centos.org/source-git/rpm.git
```

Let's not push to master just yet.

```
$ git checkout -B preview
Switched to a new branch 'preview'

$ git push -u sg
The authenticity of host 'git.stg.centos.org (8.43.84.204)' can't be established.
RSA key fingerprint is SHA256:e0tkihPvgWKC/ull50CaD4i40cYqPEOhVzW8jKaAa0M.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added 'git.stg.centos.org,8.43.84.204' (RSA) to the list of known hosts.
Enumerating objects: 1367, done.
Counting objects: 100% (1367/1367), done.
Delta compression using up to 8 threads
Compressing objects: 100% (774/774), done.
Writing objects: 100% (1367/1367), 5.03 MiB | 1.65 MiB/s, done.
Total 1367 (delta 486), reused 1366 (delta 486)
remote:   - to mqtt
remote: ERROR: [u'git', u'rev-list', u'824233d87b25e8fa7211079f561c79baf34b3fa7', u'^HEAD'] =-- 128
remote:
remote: fatal: bad revision '^HEAD'
remote:
remote: Sending to redis to send commit notification emails
To ssh://git.stg.centos.org/source-git/rpm.git
 * [new branch]      preview -> preview
Branch 'preview' set up to track remote branch 'preview' from 'sg'.
```

In the end I did demo on a "demo" branch, not master.


## Create a PR

I did this via web ui: https://git.stg.centos.org/source-git/rpm/pull-request/1


## Build

Build kicked off locally using `copr-cli`:
```
$ packit srpm
$ copr build ttomecek/centos-stream-rpm ./rpm-4.14.2-37.g8d29d36c.fc31.src.rpm
```

## Update check status

Sadly the commit check status (flag in pagure terminology) did not show up:
```
In [22]: cs = p.set_commit_status("8d29d36c13cf23a02d66789edb7ff735208b7ddd", CommitStatus.pending, "https://copr.fedorainfracloud.org/coprs/build/1315419", "RPM build", "The build is pending")

In [24]: cs.comment
Out[24]: 'RPM build'

In [25]: cs.commit
Out[25]: '8d29d36c13cf23a02d66789edb7ff735208b7ddd'

In [26]: cs.context
Out[26]: 'The build is pending'

In [27]: cs.state
Out[27]: <CommitStatus.pending: 1>

In [28]: cs.url
Out[28]: 'https://copr.fedorainfracloud.org/coprs/build/1315419'

In [38]: css = p.get_commit_statuses("8d29d36c13cf23a02d66789edb7ff735208b7ddd")

In [39]: css
Out[39]:
[<ogr.services.pagure.flag.PagureCommitFlag at 0x7f242f5f19d0>,
 <ogr.services.pagure.flag.PagureCommitFlag at 0x7f242f506190>]
```

Instead, I posted a comment to the PR on packit's behalf:
```
In [36]: msg = """
RPM build [has finished](https://copr.fedorainfracloud.org/coprs/build/1320138).
Status: **succeeded**

If you wish to try the change locally, you can install it in a [ubi8](https://access.redhat.com/articles/4238681) container like this:

1. Run the container first:
    ```
    podman run --rm -ti registry.access.redhat.com/ubi8 bash
    ```
2. Install the CentOS Stream repositories:
    ```
    dnf config-manager --add-repo=http://mirror.centos.org/centos/8-stream/BaseOS/x86_64/os/
    ```
    ```
    dnf config-manager --add-repo=http://mirror.centos.org/centos/8-stream/AppStream/x86_64/os/
    ```
3. And finally install the build with your change:
    ```
    dnf copr enable ttomecek/centos-stream-rpm centos-stream-x86_64
    ```
    ```
    dnf update rpm --nogpgcheck
    ```
"""

In [37]: pr.comment(msg)
Out[37]: <ogr.services.pagure.comments.PagurePRComment at 0x7f242f6dec90>
```


## Review and accept

Another PR comment done via web ui, I faked the username and the icon.


## Run locally

See the steps in the comment above.

