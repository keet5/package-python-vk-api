from pydantic import BaseModel


class File(BaseModel):
    type: str
    path: str


class Post(BaseModel):
    text: str
    files: list[File]


File(type="image", path="df")
