# Image Builder Research

We would like to use Image Builder to compose bootable images that would
contain upstream code that anyone can boot and play with it, especially
contributors.

Packit needs to work with Image Builder API in order to start those image builds.

## Image Builder API

[@ondrejbudai](https://github.com/ondrejbudai) created [a great intro blog
post](https://hackmd.io/Lrbf_6Q9SZy06iEj5S5Wuw) how to use the API. Please read
it before continuing reading.

TL;DR

1. Create a token [here](https://access.redhat.com/management/api) and generate
   an access token from it to use with Image Builder API
2. API docs: https://github.com/osbuild/image-builder/blob/main/internal/v1/api.yaml
3. Web UI: https://console.redhat.com/insights/image-builder/
4. [Image Builder service docs](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/uploading_a_customized_rhel_system_image_to_cloud_environments/creating-a-customized-rhel-system-image-for-aws-using-image-builder)
5. The team has their own gchat room, guess the name :)

## Drawbacks

The API works well, but the experience wasn't perfect. Be aware of these:

1. There are no build logs and there is no plan right now to have them.
2. In case of failure, there is only a single error message provided that can
   be confusing (see Jira tickets linked from
   https://issues.redhat.com/browse/PACKIT-1940 to HMSIB)
3. No callbacks, one needs to poll to find out about the completion about an
   image build

## PoPoC

We have a PoC in mind (Installer team needs bootable images off PRs to see the
change in action). I started a simple python script that submits an image build
and waits for it to finish. The image installs cockpit on RHEL 9 from cockpit's
releases Copr project.

Once the image is built, there is a link in the webui to launch an AWS EC2
instance and play with it. Neat!

### Usage

Set the offline token via `REDHAT_API_OFFLINE_TOKEN` env var and run the
"image_build.py" script.

## Next steps

The integration is pretty straightforward:

1. Create a new job: "image-builder" (or "image-build"?)
2. Implement a handler for it (trigger = successful Copr build)
3. Create a babysit task that will wait for the build completion
4. Auth - create a 'service' account for Packit on access.redhat.com

- Attach employee SKU to it
- Create a refresh token & store it in bitwarden
- Inform Image Builder team about this user so they are aware of it (maybe
  increase quota)
- We need to figure out how images will be shared with users (they can
  provide their AWS/GCP/Azure account ID so Image Builder can share the
  uploaded image with it)

5. Once the build is done, put a comment in a PR that the build is done and
   provide steps how to launch it
