# console.redhat.com provisioning

As a followup to our image-builder research, let's have a look at the provisioning service.

This is not thorough at all since the service (and especially the API) is rough
around the edges (April 2023). I'm assuming it will change substantially in
the future.

## Links

- [API Docs](https://console.redhat.com/beta/docs/api/provisioning/v1)
- [Real API examples](https://github.com/RHEnVision/provisioning-backend/tree/8898e972a48387b95b604e612e279ba155682c89/scripts/rest_examples)
  - I needed these to know what to send to the API
- More info in the issue: https://github.com/packit/research/issues/167

## Notes

- There is no dedicated frontend for the provisioning service: instances are
  launched in the Image Builder interface (Launch button next an image).
  - Since one can easily inspect instances in the cloud provider's frontend,
    this is not a problem, just an observation. And probably a subject to
    change in future how the UI looks like.
  - The other interface is the sources setup via Settings in top right corner.
    - Sources is the mechanism to connect console.rh.c and da cloudz. You need
      to set up a source first in order to start creating instances. In the AWS
      world, this is an IAM Policy.
- The official name is "Launch" (API's still called provisioning). Both are
  being used. So you're not confused, both reference the same service.
- The API handles only the happy path:
  - It doesn't provide errors, I need to write to the team and they check logs.
  - #hms-devel on slack, @oezr and @lzap
  - [Tracking issue](https://issues.redhat.com/browse/HMS-1646), thanks Laura for the nudge
- The API creates reservations, which sound like our jobs or tasks.
- Our integration _needs to_ utilize AWS Launch Templates:
  - A preconfiguration of an instance
  - Especially security groups (= firewall)
  - Instance details can't be configured using the API

## Integration

How we can integrate with it?

1. We should use [AWS Launch Templates](https://docs.aws.amazon.com/autoscaling/ec2/userguide/launch-templates.html).

   - One cannot configure instance parameters using the provisioning API.
   - We also need to be strict about this: we don't want users willy nilly
     change their instances (i.e. request 64G mem).
   - But at the same time, some users may require specific setups (networking, storage).
   - Make sure to get security group right: the firewall. I.e. by default all
     incoming traffic to the instance from the outside world is blocked = no
     SSH.
   - The is exactly what Launch templates are in AWS. [We should
     create](https://docs.aws.amazon.com/autoscaling/ec2/userguide/create-launch-template.html#create-launch-template-for-auto-scaling)
     one to use by default and figure out how trusted projects can customize
     them.
   - There needs to be limits.

2. We need to wait for the API to mature (see above) in order to fully integrate
3. SSH Keys: we can obtain them from GitHub: should these also be configurable?
4. Stopping and terminating the instance: when and how?
