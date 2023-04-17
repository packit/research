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

- There is no UI: instances are launched in the Image Builder interface.
- The official name is "Launch" (API's still called provisioning).
- The other interface is the sources setup via Settings in top right corner.
- Sources is the mechanism to connect console.rh.c and da cloudz.
- The API handles only the happy path:
  - It doesn't provide errors, I need to write to the team and they check logs.
  - #hms-devel on slack, @oezr and @lzap
- Our integration _needs to_ utilize AWS Launch Templates:
  - A preconfiguration of an instance
  - Especially security groups (= firewall)
  - Instance details can't be configured using the API
