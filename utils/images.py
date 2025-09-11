from .s3 import s3_client, BUCKET_NAME
from models import UserRead


def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    return s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET_NAME, "Key": key}, ExpiresIn=expires_in
    )


def attach_presigned_urls(user: UserRead) -> UserRead:
    if user.avatar:
        user.avatar = get_presigned_url(user.avatar)
    return user
