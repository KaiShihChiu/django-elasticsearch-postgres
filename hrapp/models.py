from django.db import models
import os

class Customer(models.Model):
    user_id = models.CharField(max_length=100, unique=True)
    user_name = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    # email = models.EmailField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    specialty = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name or 'Unknown User'}"


class LineMessage(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='chat_messages')  # 使用 ForeignKey 代替 OneToOneField
    messages = models.TextField()  # 使用 TextField 来存储单条消息记录
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name}"
    
class UploadedPPT(models.Model):
    file = models.FileField(upload_to='uploads/ppt/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def filename(self):
        return os.path.basename(self.file.name)
    
    def __str__(self):
        return self.filename()
    
class Patent(models.Model):
    ppt = models.ForeignKey(UploadedPPT, on_delete=models.CASCADE, related_name='patents', null=True, blank=True, default=1)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    # 其他字段，例如图片的路径
    image = models.ImageField(upload_to='patents/', null=True, blank=True)  # 將圖片上傳到 'patents/' 目錄
    created_at = models.DateTimeField(auto_now_add=True)
    slide_number = models.PositiveIntegerField()
    # embedding = models.JSONField(null=True, blank=True)  # Storing the vector embedding


    def __str__(self):
        return f"{self.title}"