from django.shortcuts import render
from django.http.response import HttpResponse, HttpResponseBadRequest
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from django.http.request import HttpRequest
from django.conf import settings
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger("django")

line_bot_api = LineBotApi(settings.CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.CHANNEL_SECRET)

@csrf_exempt
@require_POST
def webhook(request: HttpRequest):
    signature = request.headers["X-Line-Signature"]
    body = request.body.decode()

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        messages = (
            "Invalid signature. Please check your channel access token/channel secret."
        )
        logger.error(messages)
        return HttpResponseBadRequest(messages)
    return HttpResponse("OK")