import json
import ssl
import urllib.request


class AuthProxy:
    def __init__(self, auth_type="none", token=None):
        self.auth_type = auth_type
        self.token = token

    def build_headers(self):
        if self.auth_type == "api_key":
            return {"X-API-Key": self.token}
        if self.auth_type == "jwt":
            return {"Authorization": f"Bearer {self.token}"}
        if self.auth_type == "oauth":
            return {"Authorization": f"OAuth {self.token}"}
        return {}

    def get_json(self, url):
        request_obj = urllib.request.Request(url, headers=self.build_headers())
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(request_obj, context=context) as response:
            return json.loads(response.read().decode())
