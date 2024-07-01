# Research notes

This repo is used to document research performed by the Packit Team.

## Organization of this repository

### How to add new findings?

1. Try to find an appropriate category for your topic. In case there is none yet,
   you can create a new directory with `_category_.yml` file that describes the
   category.
1. Please create a new directory in the [research](research/) directory.
1. Create an `index.md` document in that directory.
1. Make sure your `index.md` contains a clear description of what the outcome is
   from your research topic: ideally propose what the next steps should be.
   It's completely fine to tell that the technology is not interesting to us
   and there are no further actions.
1. Add everything related to your topic in the directory.
1. Open a pull request.

> [!NOTE]
> In case you're working on a follow-up research, feel free to just add a new
> Markdown file next to already existing research.

### Template for research

```md
---
title: ‹Title of your research›
authors: ‹Kerberos logins of authors, e.g. login or [login_a, login_b]›
---

## Description

## Acceptance criteria

---

‹findings›

---

## Next steps
```

> [!WARNING]
> Authors are not checked against the list of authors as with the blog posts,
> keeping the authors in the attributes of research is just a courtesy to avoid
> unnecessary _git blaming_.
