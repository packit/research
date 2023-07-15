#!/usr/bin/python3

import os
import sys
import time

import requests
from pprint import pprint

try:
    offline_token = os.environ["REDHAT_API_OFFLINE_TOKEN"]
except KeyError:
    print(
        "Please generate an offline token here:\n"
        "  https://access.redhat.com/management/api\n"
        "and set it with REDHAT_API_OFFLINE_TOKEN env var."
    )
    sys.exit(1)

image_builder_api_url = "https://console.redhat.com/api/image-builder/v1"


class Client:
    def __init__(self):
        self.access_token = self.get_access_token()
        self.image_builder_session = requests.Session()
        self.image_builder_session.headers.update(
            {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
            }
        )

    def get_access_token(self) -> str:
        """
        curl -X POST -d grant_type=refresh_token \
          -d client_id=rhsm-api -d refresh_token=$o \
          https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
        :return: access_token
        """
        sso = requests.Session()
        response = sso.post(
            "https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token",
            data={
                "grant_type": "refresh_token",
                "client_id": "rhsm-api",
                "refresh_token": offline_token,
            },
        )
        output = response.json()
        print("Output from obtaining the access token:")
        pprint(output)
        return output["access_token"]

    def check_token(self):
        response = requests.get(
            "https://api.access.redhat.com/account/v1/user",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        json_output = response.json()
        print(f"User info (Code: {response.status_code}): ")
        pprint(json_output)

    def touch_api(self):
        """access readonly API endpoints - mostly to check that all is good"""
        url = f"{image_builder_api_url}/openapi.json"
        print(f"Image Builder API is available at {url}")
        response = self.image_builder_session.get(url)
        print(f"Response [{response.status_code}]")
        pprint(response.json())

        print("/ready version")
        response = self.image_builder_session.get(f"{image_builder_api_url}/version")
        print(f"Response [{response.status_code}]")
        pprint(response.text)

        print("/ready endpoint")
        response = self.image_builder_session.get(f"{image_builder_api_url}/ready")
        print(f"Response [{response.status_code}]")
        pprint(response.text)

    def create_image(self):
        payload = {
            "image_name": f"{os.getlogin()}-{time.time()}-90",
            "distribution": "rhel-90",
            "image_requests": [
                {
                    "architecture": "x86_64",
                    "image_type": "aws",
                    "upload_request": {
                        "type": "aws",
                        "options": {"share_with_accounts": ["727920394381"]},
                    },
                }
            ],
            "customizations": {
                "packages": ["cockpit"],
                "payload_repositories": [
                    {
                        "rhsm": False,
                        "baseurl": (
                            "https://download.copr.fedorainfracloud.org"
                            "/results/@cockpit/cockpit-preview/centos-stream-9-x86_64/"
                        ),
                        # needs to be the actual key, not link:
                        # https://issues.redhat.com/browse/HMSIB-14
                        # "gpgkey": "https://download.copr.../@cockpit/cockpit-preview/pubkey.gpg",
                        "check_gpg": False,
                    }
                    # {
                    #     "rhsm": False,
                    #     "baseurl": ("https://download.copr.fedorainfracloud.org"
                    #                 "/results/packit/packit-releases/epel-8-x86_64/"),
                    # },
                    # {
                    #     "rhsm": True,
                    #     "baseurl": (
                    #         "https://cdn.redhat.com/content/dist/codeready-builder/8/x86_64/baseos/os/"
                    #     ),
                    # },
                    # {
                    #     "rhsm": False,
                    #     "metalink": ("https://mirrors.fedoraproject.org/metalink"
                    #                  "?repo=epel-8&arch=x86_64"),
                    # },
                ],
            },
        }
        response = self.image_builder_session.post(
            f"{image_builder_api_url}/compose", json=payload
        )
        response_json = response.json()
        print(f"Image creation requested [{response.status_code}]")
        pprint(response_json)
        return response_json["id"]

    def wait_for_image_build(self, build_id: str):
        while True:
            response_json = self.image_builder_session.get(
                f"{image_builder_api_url}/composes/{build_id}",
            ).json()
            status = response_json["image_status"]["status"]
            if status not in ("building", "pending"):
                pprint(response_json)
                break
            print(f"{build_id} - {status}")
            time.sleep(3.0)


def main():
    c = Client()
    # c.check_token()
    # c.touch_api()
    build_id = c.create_image()
    # build_id = "3a5d6a43-6b49-4f3f-a678-45bd0dc21938"
    c.wait_for_image_build(build_id)


main()
