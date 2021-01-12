import re
import traceback
import logging

import jwt
from channels.db import database_sync_to_async
from django.conf import LazySettings
from django.contrib.auth.models import AnonymousUser
from jwt import InvalidSignatureError, ExpiredSignatureError, DecodeError

from chat.models import User

settings = LazySettings()
logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except:
        return AnonymousUser()


class TokenAuthMiddleware:
    """
    自定义 jwt 校验器
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):

        headers = dict(scope['headers'])
        auth_header = None
        if b'authorization' in headers:
            auth_header = headers[b'authorization'].decode()
        else:
            # 测试使用 不允许放在cookie头里
            try:
                auth_header = _str_to_dict(headers[b'cookie'].decode())['X-Authorization']
            except:
                pass

        logger.info(auth_header)
        if auth_header:
            try:
                user_jwt = jwt.decode(
                    auth_header,
                    settings.SECRET_KEY,
                )
                # 拿到用户信息
                scope['user'] = await get_user(user_jwt['user_id'])
            except (InvalidSignatureError, KeyError, ExpiredSignatureError, DecodeError):
                traceback.print_exc()
                pass
            except Exception as e:
                logger.error(scope)
                traceback.print_exc()

        return await self.app(scope, receive, send)


def _str_to_dict(str):
    return {k: v.strip('"') for k, v in re.findall(r'(\S+)=(".*?"|\S+)', str)}
