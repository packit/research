# Improving https://packit.dev/

This research covers updating https://packit.dev/ so it's more readable &
usable to our users.

## Current status

Well, we're not happy with the present website. Usability is lacking, for more
info see [Raw meeting notes](#raw-meeting-notes).

There are multiple tasks ahead of us to improve the website:

- Layout
- Structure

## What to do?

Let's talk about the details - what we can do?

### "Steal" osbuild's website

Hunor really likes [osbuild.org/](https://osbuild.org/). Gotta say I (Tomas)
like it as well - it's simple, clean, readable, convenient. The problem is that
[the website](https://github.com/osbuild/osbuild.github.io) is not using a
theme, it seems the team created it from scratch, for Jekyll.

**TODO**

- Switch from hugo to jekyll
- Copy-paste the osbuild site sources
- Port packit.dev to the new layout

### Pick a different layout

Since the present layout has so many deficiencies, it's unrealistic to fix all
of them. It is more efficient to move to a more usable layout.

The layout
[digitalcraftsman/hugo-alabaster-theme](https://github.com/digitalcraftsman/hugo-alabaster-theme)
is pretty popular among python projects, but sadly the repo is archived and no
longer maintained.

Other minimalist themes:

- [HugoTeX](https://themes.gohugo.io/hugotex/)
- [Hugo ʕ•ᴥ•ʔ Bear Blog](https://github.com/janraasch/hugo-bearblog)
- [ronu-hugo-theme](https://github.com/softwareyoga/ronu-hugo-theme)
- [tale-hugo](https://github.com/EmielH/tale-hugo)
- [fuji](https://github.com/amzrk2/hugo-theme-fuji/)
- [kiera](https://themes.gohugo.io/hugo-kiera/)
- [harbor](https://themes.gohugo.io/harbor/)

**TODO**

- Pick a theme
- Port current website to it

### Improve site's structure

One of the problems with the current website is the structure - several
documents are "misplaced". Our users have hard times finding the information
they need. We also need the ability to share links with our users to precise
parts of the documentation.

**TODO**

- Think about a new structure and propose it to the team
- Implement the new structure
- Make sure a list of blog posts is well listed and browsable
- Preserve the important links and make redirects when moving content
- Add a way to link to specific config options

### Hugo → Jekyll

GitHub has native support for [Jekyll](https://jekyllrb.com/) - the question is
if it's worth migrating.

The biggest [advantage](https://forestry.io/blog/hugo-and-jekyll-compared/) of
jekyll over hugo are
[plugins](https://docs.github.com/en/free-pro-team@latest/github/working-with-github-pages/about-github-pages-and-jekyll#plugins).
Since hugo is written in go, it has all the batteries included and there is no
support for plugins - do we actually care about this?

When I
[read](https://docs.github.com/en/free-pro-team@latest/github/working-with-github-pages/about-jekyll-build-errors-for-github-pages-sites)
about the jekyll ↔ GitHub integration, I feel like the key features are
missing:

- [No preview support in
  PRs.](https://github.community/t/need-help-with-jekyll-github-project-page-and-team-git-workflow/10440)
- They suggest using travis for testing.
- "It can take up to 20 minutes for changes to your site to publish after you
  push the changes to GitHub."
  - This is already solved for us by the GitHub action Jirka set up.

## Raw meeting notes

```
Hunor:
* logo
* header links are not clickable - javascript copies it for you
* we have a list of posts and they are ordered randomly
* the text is too wide - a reader can get lost easily on a line
* the font is difficult to read
* likes https://www.osbuild.org/

Franta: options in the config cannot be made links
* structure: docs for the app is disconnected from the rest of the docs

Honza: red color does not match
* we can use the colour scheme from packit logo
  * https://github.com/packit/packit/blob/master/design/export/logo-guideline.pdf
* letters are too thin and hard to read

Tomas likes https://flask.palletsprojects.com/en/1.1.x/
* https://github.com/digitalcraftsman/hugo-alabaster-theme
```
