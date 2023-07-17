---
title: GitLab integration
authors:
  - name: Shreyas Papinwar
    email: spapinwar@gmail.com
    url: https://github.com/shreyaspapi
    image_url: https://github.com/shreyaspapi.png
---

## Project Webhooks

Project webhooks allow you to trigger a URL if for example new code is pushed or a new issue, merge request is created. You can configure webhooks to listen for specific events like pushes, issues, merge requests. GitLab will send a POST request with data to the webhook URL.

## Project integrations

Just like github apps, GitLab has an equivalent concept of Integrations, but those need to be added to the GitLab codebase itself. There's no extensible "app" model.

Project integrations allow you to integrate GitLab with other applications. They are a bit like plugins in that they allow a lot of freedom in adding functionality to GitLab.

## Integration

There are many ways available for us to move forward.

### 1) Project Webhook:

- For adding packit-service to any gitlab project a webhook can be added by the project maintainers by going to project settings -> webhooks.

- We can process events from GitLab and to return feedback of successful builds or failed tests back into the merge request we can have a **Packit Gitlab User** that needs to have access to the repository in which the webhook is added.

- This way is a start forward way and will work with gitlab.com and all the custom instances like http://gitlab.gnome.org/, https://gitlab.freedesktop.org

### 2) Project Services / Project Integration:

- For us to integrate our Packit-Service to gitlab integrations we need to change the gitlab codebase itself as mentioned in the [docs](https://docs.gitlab.com/ee/user/project/integrations/overview.html#contributing-to-integrations).

- This service can then be enabled by the project maintainer by going to Project settings -> Integrations -> Packit service, eg. [test-instance](http://52.183.132.26:3000/testpackit/testing/-/settings/integrations).

- For adding project integration to gitlab instances we have two options to move forward:

  1. We contribute to the [GitLab](https://gitlab.com/gitlab-org/gitlab/tree/master/app/models/project_services) and can reach large audiance, but for contributing to gitlab is a time taking process. (Currently looking into it)

  2. Add our project integration code directly to the custom gitlab instances that we currently want to support.

## Pros and Cons of having Packit as a Project Integration in Gitlab

A integration / project service in gitlab works in a way that the service does not have the access to the repository and can only work as a webhook to report events based on permissions given (issues, merge requests etc).

### Pros

- Users dont have to setup webhook for each project.
- We can setup a settings page for the packit-service in gitlab which will act as a config for the service instead of tweeking packit config file in the repository.
- We can add more options in the future in the settings of our integration.

### Cons

- Users will still have to give access to a **packit service user** for getting the build updates.
- As Gitlab is written in ruby for us "Packit" to contribute to the project, introduces new language **Ruby** that we will need to work on for maintaining the service in gitlab.
- Less documentation for for adding Integrations - https://docs.gitlab.com/ee/user/project/integrations/overview.html

For now, we dont have to worry about adding project service to gitlab, as it is the same thing as creating a new webhook.

## TODO

Research on authentication:

- Unlike Github the auth token for a webhook need to be filled by the user.
- We will need to think of having unique token for each project we give access to.

## FAQ

### Where and how does the Project Integration run?

Just like github apps which are created in github using GUI, GitLab has an equivalent concept of Integrations, but those need to be added to the GitLab codebase itself. There's no GUI for addding integrations as it is a core part of GitLab.
