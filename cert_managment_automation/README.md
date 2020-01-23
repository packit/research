# Why

Currently, deployment of certificates requires manual intervention and involves openshift route deletion-creation-deletion-creation (to have have requests)


# certpod managing commincating wit required pods

communication:
* redis
* some oc/kubernetes communication

action taken:
* certbot + pre post hooks
* httpd config + reload

# cerbot running localy on evrey pod


# additional requirments:
* store keys in gitlab secrets

