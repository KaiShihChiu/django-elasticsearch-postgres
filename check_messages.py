import os
import django

# 设置 Django 环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_linebot.settings')
django.setup()

from hrapp.models import LineMessage

# 查询所有的 LineMessage 记录
messages = LineMessage.objects.all()

# 打印出所有查询到的记录
for message in messages:
    print(f"User ID: {message.user_id}, Message: {message.message_text}, Timestamp: {message.timestamp}")
