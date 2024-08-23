from django.urls import path
from .views import webhook, upload_ppt, upload_success, patent_detail, download_selected_tables

urlpatterns = [
    path("webhook/", webhook, name="webhook"),
    path('upload/', upload_ppt, name='upload_ppt'),  # 配置上傳 PPT 的頁面路徑
    path('upload/success/', upload_success, name='upload_success'),  # 上傳成功頁面的路徑
    path('patents/<int:patent_id>/', patent_detail, name='patent_detail'),
    path('download-tables/', download_selected_tables, name='download_tables'),
]
