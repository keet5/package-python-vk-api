import math
import magic
from requests import request
from operator import itemgetter
from .exceptions import VkRequestError, VkUploadImageError
from . import schemas


class VkApi:
    def __init__(self, token: str, group_id: int):
        self.token = token
        self.group_id = group_id

    def method_request(
        self,
        method: str,
        params: dict = dict(),
        http_method: str = "GET",
        files: list = [],
    ):
        host = "https://api.vk.com/method"

        all_params = {
            "access_token": self.token,
            "v": 5.131,
        }

        all_params.update(params)

        url = f"{host}/{method}"

        res = request(
            method=http_method, url=url, params=all_params, files=files
        ).json()

        if "error" in res:
            raise VkRequestError(**res["error"])

        return res

    def wall_post(self, post: schemas.Post):
        post.files = post.files[:10]

        attachments = self.get_attachments(post.files)

        params = {
            "owner_id": -self.group_id,
            "friends_only": 0,
            "from_group": 1,
            "message": post.text,
            "attachments": attachments,
        }

        result = self.method_request("wall.post", params=params)
        return result

    def get_attachments(self, files: list[schemas.File]):
        images = []
        videos = []
        documents = []

        for file in files:

            if file.type == "image":
                extension = magic.from_file(file.path, mime=True).split("/")[1]
                if extension == "gif":
                    documents.append(file.path)
                else:
                    images.append(file.path)
            elif file.type == "video":
                videos.append(file.path)

        attachments = ",".join(
            self.photo_attachments(images)
            + self.video_attachments(videos)
            + self.document_attachments(documents)
        )
        return attachments

    def document_attachments(self, documents: list[str]):
        attachments = []
        for document in documents:
            upload_url = self.docs_get_wall_upload_server()
            file = self.upload_document(upload_url, document)
            attachment = self.docs_save(file)
            attachments.append(attachment)
        return attachments

    def docs_save(self, file: str):
        params = {"file": file, "title": "test title", "tags": "tag0,tag1,tag2"}
        res = self.method_request("docs.save", params=params)
        id, owner_id = itemgetter("id", "owner_id")(res["response"]["doc"])
        return f"doc{owner_id}_{id}"

    def upload_document(self, upload_url: str, document: str):
        files = {"file": open(document, "rb")}
        res = request(method="POST", url=upload_url, files=files)
        return res.json()["file"]

    def docs_get_wall_upload_server(self):

        upload_url = self.method_request("docs.getWallUploadServer")["response"][
            "upload_url"
        ]
        return upload_url

    def video_attachments(self, videos: list[str]):
        attachments = []
        for video in videos:
            upload_url = self.video_save()
            owner_id, video_id = itemgetter("owner_id", "video_id")(
                self.upload_video(upload_url, video)
            )
            attachments.append(f"video{owner_id}_{video_id}")

        return attachments

    def video_save(self) -> str:
        params = {"group_id": self.group_id}
        upload_url = self.method_request("video.save", params=params)["response"][
            "upload_url"
        ]
        return upload_url

    def upload_video(self, upload_url, video: str):
        files = {"file": open(video, "rb")}
        res = request(method="POST", url=upload_url, files=files)
        return res.json()

    def photo_attachments(self, photos: list[str]):

        attachments = []
        for i in range(math.ceil(len(photos) / 7)):

            upload_url = self.photos_get_wall_upload_server()

            max_size = 7
            start = i * max_size
            end = start + max_size

            photo_upload_server = self.upload_photos(upload_url, photos[start:end])
            if photo_upload_server["photo"] == "":
                raise VkUploadImageError
            attachments += self.save_wall_photo(photo_upload_server)

        return attachments

    def photos_get_wall_upload_server(self) -> str:
        """
        returns upload url
        """

        params = {"group_id": self.group_id}

        res = self.method_request(method="photos.getWallUploadServer", params=params)
        return res["response"]["upload_url"]

    def upload_photos(self, upload_url: str, photos: list[str]):
        files = {f"file{n}": open(file, "rb") for n, file in enumerate(photos)}
        res = request(method="POST", url=upload_url, files=files)
        upload_server = res.json()
        return upload_server

    def save_wall_photo(self, upload_server: dict):

        params = {
            "group_id": self.group_id,
            "photo": upload_server["photo"],
            "server": upload_server["server"],
            "hash": upload_server["hash"],
        }

        res = self.method_request("photos.saveWallPhoto", params=params)

        attachments = map(
            lambda attachment: "photo"
            + "_".join(
                map(str, itemgetter("owner_id", "id")(attachment)),
            ),
            res["response"],
        )

        return attachments
