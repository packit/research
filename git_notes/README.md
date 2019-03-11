# Git Notes research

The aim of this research is to provide
a feedback around [git notes](https://git-scm.com/docs/git-notes) command.

[Examples](./examples) directory contains [git_notes.sh](./examples/git_notes.sh).
The command adds number of your specific commits into your `git` repository.

## What git_notes.sh does?

* Add N-notes into your `git repository`.
  * The note added into git is:

```Testing notes ${cnt}\npackit_test=yes"```
* Show all notes added by previous command
* Show specific (3th) note from git.

## Can be used git notes as a database?

`git notes` are basically one liners. We can use a separator and for
some things it can be used as a "database".

## Can be used git notes for storing states?

Yes, definitely. We can use `git notes` for storing state.
But, first of all, we have to read note from specific commit and then
append the state into git note.

For 'editing' git notes, a command
`git note add -f -m "some message"` has to be used.
`-f` option is used for overwriting notes.

## Can we check out the commit and its git notes?
Yes, `git notes` where designed for it. See [git_notes.sh](./examples/git_notes.sh).
