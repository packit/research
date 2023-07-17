---
title: Git Notes
authors: phracek
---

The aim of this research is to provide
a feedback around [git notes](https://git-scm.com/docs/git-notes) command.

There's a [git_notes.sh](./git_notes.sh) script, which
adds number of notes into your `git` repository.

## What git_notes.sh does?

- Add N-notes into your git repository.
  - The notes are added with `git node add -f -m "Testing notes ${cnt}\npackit_test=yes" -m "json=${JSON_NOTE}" ${commit}`:
- Show all notes added by previous command
- Show specific (2th) note from git.

## Can git notes be used as a database?

`git notes` are basically one liners. We can use a separator and for
some things it can be used as a "database". The [git_notes.sh](./git_notes.sh) script
also stores JSON object into git.
If `multiple` `-m` options are given, their values
are concatenated as separate paragraphs.

## Can git notes be used for storing states?

Yes, but, first of all, we have to read note from specific commit and then
append the state into git note.
Only one note per one commit is allowed.

For 'editing' git notes, a command
`git note add -f -m "some message"` has to be used.
`-f` option is used for overwriting notes.

## Can we check out the commit and its git notes?

Yes, `git notes` were designed for it. See [git_notes.sh](./git_notes.sh).

## How to push and pull notes to / from git?

To push the notes into git use the command

```bash
git push origin refs/notes/commits
```

To pull the notes from git use the command

```bash
git fetch origin refs/notes/commits:refs/notes/commits
```

## Update .gitconfig for git notes support

```bash

[remote "origin"]
	fetch = +refs/notes/*:refs/notes/*
```
