import base64
import json
import os

from rest_framework.renderers import JSONRenderer


class APIJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a bytestring.
        """
        data_response = {
            "status": "Success",
            "code": renderer_context["response"].status_code,
            "data": data,
        }

        if renderer_context["response"].exception:
            data_response["status"] = "Failure"

        return super().render(data_response, accepted_media_type, renderer_context)

