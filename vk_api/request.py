import requests
from .exceptions import VkRequestError


def method_request(
    method: str,
    token: str,
    params: dict = dict(),
    http_method: str = "GET",
    files: list = [],
):
    host = "https://api.vk.com/method"

    all_params = {
        "access_token": token,
        "v": 5.131,
    }

    all_params.update(params)

    url = f"{host}/{method}"

    res = requests.request(
        method=http_method, url=url, params=all_params, files=files
    ).json()

    if "error" in res:
        raise VkRequestError(**res["error"])

    return res
