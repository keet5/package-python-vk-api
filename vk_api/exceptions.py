class VkRequestError(Exception):
    def __init__(self, error_code: int, error_msg: str, request_params: list):
        self.error_code = error_code
        self.error_msg = error_msg
        self.request_params = request_params

    def __str__(self):
        return f"\n\tcode: {self.error_code}\n\tmessage: {self.error_msg}\n\tparams: {self.request_params}"


class VkUploadImageError(Exception):
    pass
