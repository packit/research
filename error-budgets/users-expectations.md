# Error Budgets

## Users expectations

To adopt [Error Budget](README.md) for Packit Service we asked our users
to provide their feedback on what they expect from the service in areas of
reliability, availability, performance, etc.

The responses are classified into several objectives:

#### latency

In what timeframe users expect first response from the service.

I got first reply from mpitt & mmarusak and they suggested to have some
"accepted" status ASAP. I liked the idea so I asked the other users about
that as well.

- Packit should be reasonably quick to post status to Github - just to let us
  know it was recognized and it will be dealt with. This should be measured in
  "a couple of seconds". I would assume there is some queue where you keep tasks
  that will be run. If that is the case, then I would say there should be some
  limit on how much time a task spends in a queue waiting for a free worker.
  While posting status should take at most a couple of seconds, this should take
  a maximum of "a couple of minutes" and then the task should be running. (mmarusak)
- 95% of "pending" statuses get sent to a PR within 30s, 99.5% of them within 10 minutes.(mpitt)
- Max several minutes. If there was some "accepted" status, then he'd expect
  to see it within 5s. (jkonecny)
- Max 10 minutes. "accepted" status would be handy within 1min. (jrodak)
- Max 5 minutes. "accepted" 30s max.(vtrefny)
- mbocek expects some response in several minutes. Doesn't need any separate "accepted" status.
- Have "pending" state ASAP as indication that the request was accepted and
  then we can wait minutes - hours before results are returned. (fsumsal)

#### reliability / error rate

- A `/packit build` request requeues the test in 95% of cases, and retrying a
  failed requeue a second time then succeeds in 99.5% of all cases. (mpitt)
- 95% of all test requests finish, i.e. get queued, sandcastle starts building
  the srpm, hands it to COPR, then hands it to TF, and that provisions an
  instance and collects the logs. 5% failure rate is pretty high as a user,
  but let's start with modest goals and improve in the future. There's always
  `/packit build` for self-service retries. (mpitt)
- Error rate max 10%. The bugs are expected to be fixed within day(s). (jkonecny)
- 95% (jrodak)
- Units of fails monthly. (vtrefny)
- mbocek would ping us in case of any errors, but would probably survive some
  errors since he's probably able to manually work-around it for some time.
- fsumsal doesn't expect 100% reliability. Can't say any percentage,
  but current stability/reliability is more than satisfactory. It's nice that
  jobs can be easily restarted (would be even better if individual jobs could be restarted).

#### availability

- 99.9% availability of the webhook for controlling GitHub events (PRs and
  `/packit` commands), i.e. 10 min downtime/month (mpitt)
- 85% (jkonecny)
- 90%, downtime max 1 day in one PR. (jrodak)
- No big problem if the service is unavailable for couple of hours up to a day (vtrefny)
- Max like 2 days in a month, i.e. 93% (mbocek)
- Depends whether the downtime is planned or not, i.e. it's better over weekend
  than during week. Anyway 1% sounds reasonable, esp. if it's out of "peak hours". (fsumsal)
- Dashboard is expected to be up and showing production data 99.5% of all times
  (50 min downtime/week) -- again this seems rather modest, but let's start
  somewhere. I find this dashboard really useful. (mpitt)
