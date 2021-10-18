# Setting up syncing of Github issues to Jira

1. Add the repo name as a new component to [our project in Jira](https://issues.redhat.com/projects/PACKIT?selectedItem=com.atlassian.jira.jira-projects-plugin:components-page)
2. Add the repo to [the Sync2Jira Config](https://gitlab.cee.redhat.com/devops/factory2-openshift-templates/-/blob/master/prototypes/sync2jira/sync2jira.yml#L286)
3. Make sure [fedmsg](https://apps.fedoraproject.org/github2fedmsg) is enabled for the repository

If things are not working as expected, you can:

- ping Ralph Bean
- disable & enable again the repo in [github2fedmsg](https://apps.fedoraproject.org/github2fedmsg)
- trigger a fresh [sync of your issues](http://sync2jira-sync-page-sync2jira.apps.ocp-c1.prod.psi.redhat.com/github)
