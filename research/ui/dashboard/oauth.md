---
title: Authentication with remote platforms
authors: ttomecek
---

## Dashboard ← GitHub

This is nicely documented on [Github's "Authorizing OAuth Apps"](https://docs.github.com/en/developers/apps/building-oauth-apps/authorizing-oauth-apps).

### 0. Initiation

A user goes to our dashboard, fools around and clicks "Log in via GitHub".

### 1. Redirect

We will redirect the user to GitHub where they authenticate and authorize our dashboard to obtain data from GitHub. We should request perms to know user's repositories, public orgs and pull requests so we can obtain the list in the next step.

We need to supply [some data to GitHub](https://docs.github.com/en/developers/apps/building-oauth-apps/authorizing-oauth-apps#1-request-a-users-github-identity):

```
GET https://github.com/login/oauth/authorize
```

- `client_id` — our GitHub app ID

- `redirect_url` — either the page within dashboard where the login process started or the personalized view

- `login` — "Suggests a specific account to use for signing in and authorizing the app.", we don't have that info

- `scope` — we only need read-only access so far (except for check runs, it would make sense to perform re-run for the dashboard)

- `state`, `allow_signup` — all blank

### 2. Back to dashboard

Once approved, we're back to dashboard via `redirect_url`.

GitHub granted us a temporary `code` which we can use to get a proper API token to make GitHub requests on behalf of the user.

We concluded that we'd implement the logic in javascript for now to get the data from GitHub and then use it to personalize the dashboard.

### Conclusion

- Get a proper token after the redirect.

- Obtain data from GitHub or get it from p-s' REST API

- Visualize

## Fedora

We'd like to use [Fedora's OpenID Connect](https://fedoraproject.org/wiki/Infrastructure/Authentication):

- to get the FAS username so we can automate the onboarding process

- to authenticate the user in order to provide interface for the Fedora workflow

The OpenID connect workflow is very similar to GitHub's OAuth workflow hence I'm not gonna go through the details.

There is a javascript library to work with OpenID Connect: https://github.com/openid/AppAuth-JS

### Note

We'll need to get a new scope registered for us, see the list in Fedora's docs to get an idea.

## GitLab

[Very similar](https://docs.gitlab.com/ee/api/oauth2.html) to GitHub's OAuth mechanism, except they want the services to create several values (`STATE`, `CODE_VERIFIER` and `CODE_CHALLENGE`) before initiating the process to make sure it's secure.

## Benefits to users

- They can see content they own (pull requests, repositories, pipeline runs), users don't really care about other repos.

- And in future have a single place to interact with all of their projects via dashboard, both in upstream and downstream.

## Dashboard next steps

- Implement the redirect mechanism for GitHub Oauth

- I don't think we should create a new GitHub app specifically for the dashboard, we should keep using the one we have.

- We can either

  1. Create a personalized dashboard with a list of repos, orgs, pipeline runs and PRs

  2. Or we can order the existing views so that user's content is first and sorted by time it was modified (recently modified content first)

- Implement Fedora OpenID Connect workflow.
