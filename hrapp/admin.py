from django.contrib import admin
from .models import LineMessage, Customer, UploadedPPT, Patent

# 注册 LineMessage 模型到 Django 管理后台
@admin.register(LineMessage)
class LineMessageAdmin(admin.ModelAdmin):
    list_display = ('customer', 'messages', 'timestamp')  # 在列表中显示的字段
    search_fields = ('user_id', 'message_text')  # 可搜索的字段

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'name', 'occupation', 'specialty', 'created_at')
    search_fields = ('user_name', 'name', 'occupation', 'specialty')

@admin.register(Patent)
class PatentAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_description', 'slide_number', 'created_at')
    search_fields = ('title', 'description')

    # 自定义方法来显示description的前30个字符
    def short_description(self, obj):
        return obj.description[:30] + '...' if len(obj.description) > 30 else obj.description

    short_description.short_description = 'Description'  # 这是admin中显示的列名

admin.site.register(UploadedPPT)
