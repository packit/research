# Deployment and testing strategies

### Blue-Green deployment

- two identical environments, a “blue” and a “green” environment with different versions
  of a service
- once the software is working in the green environment, router can be switched so that all incoming requests go to the
  green environment - the blue one is now idle
- replicating a production environment can be complex and expensive

---

- similar to our current approach in Packit service - staging and production environment
- requires more resources

### Canary deployment

- running two versions of the application simultaneously - stable, canary
- the new version of the application is gradually deployed while getting a very small amount of live traffic
- test in production with real users and use cases and compare different service versions side by side
- based on the following assumptions:
  1. multiple versions of application can exist together at the same time, getting live traffic
  2. some customers might hit a production server in one request and a canary server in another
     (if no sticky session mechanism used)
- usually the traffic is split based on weight (e.g. 90 percent of the requests go to new version, 10 percent go to old version)
- good for performance and error rate monitoring, when tests are unreliable or lacking

---

- for our use case this could be done on different levels, e.g. do the canary deployment only for the worker,
  also for the service
- to split the traffic on the route level, it is possible to set up a route with multiple services (each service
  different version) in Openshift with defining weight for each ([docs](https://docs.openshift.com/container-platform/3.11/architecture/networking/routes.html#alternateBackends)):

```
apiVersion: v1
kind: Route
metadata:
  name: route-alternate-service
  annotations:
    haproxy.router.openshift.io/balance: roundrobin
spec:
  host: www.example.com
  to:
    kind: Service
    name: service-name
    weight: 20
  alternateBackends:
  - kind: Service
    name: service-name2
    weight: 10
  - kind: Service
    name: service-name3
    weight: 10
```

- one service can back up more pods, grouping is done by labels
- Celery routing - also for retrying the jobs and routing them after failure to the stable version worker - requires
  changes in code
- one database - inconsistency, change between versions and then simultaneous use is risky

### A/B testing

- different versions of the same service run simultaneously as “experiments” in the same environment for a period of time
- released to subset of users under specific condition
- primarily focused on experimentation and exploration
- for testing new features

---

- probably not really relevant to us

### Shadow deployment

- the new version is available alongside the old version, but a copy or forked version of traffic to the
  older version is sent to the new version for production testing
- doesn’t affect users
- service tested with production traffic
- more expensive, more complex setup

---

- lot of operations need to be mocked (e.g. so we don't set the Github status 2 times) - requires extra
  coding work and doesn't verify the code so well

## Comparison

[Source](https://cloud.google.com/architecture/application-deployment-and-testing-strategies)

| Deployment or testing pattern                                                                                     | Zero downtime | Real production traffic testing | Releasing to users based on conditions | Rollback duration |
| ----------------------------------------------------------------------------------------------------------------- | ------------- | ------------------------------- | -------------------------------------- | ----------------- |
| Blue/green (Version 2 is released alongside Version 1; the traffic is switched to Version 2 after it is tested. ) | ✓             | x                               | x                                      | Instant           |
| Canary (Version 2 is released to a subset of users, followed by a full rollout.)                                  | ✓             | ✓                               | x                                      | Fast              |
| A/B (Version 2 is released, under specific conditions, to a subset of users.)                                     | ✓             | ✓                               | ✓                                      | Fast              |
| Shadow (Version 2 receives real-world traffic without impacting user requests.)                                   | ✓             | ✓                               | x                                      | Does not apply    |
