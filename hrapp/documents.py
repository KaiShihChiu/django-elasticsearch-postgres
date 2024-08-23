from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from .models import Patent

# 定义索引
patents_index = Index('patents')

@registry.register_document
class PatentDocument(Document):
    id = fields.IntegerField(attr='id')  # 显式地将 Django 模型的 id 字段包含进来
    title = fields.TextField(
        attr="title",
        fields={
            'raw': fields.KeywordField(),
        }
    )
    description = fields.TextField(
        attr="description",
        fields={
            'raw': fields.KeywordField(),
        }
    )
    slide_number = fields.IntegerField()
    created_at = fields.DateField()
    image = fields.TextField(attr='get_image_url')  # 使用自定义方法处理 image 字段

    class Index:
        name = 'patents'

    class Django:
        model = Patent

    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return obj.image.url
        return '/media/default-placeholder.png'  # 默认占位符图片