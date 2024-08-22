# from django_elasticsearch_dsl import Document
# from django_elasticsearch_dsl.registries import registry
# from hrapp.models import MyModel

# @registry.register_document
# class MyModelDocument(Document):
#     class Index:
#         # 定义索引名称
#         name = 'mymodel_index'
    
#     class Django:
#         # 关联的 Django 模型
#         model = MyModel
#         # 指定需要索引的字段
#         fields = [
#             'field1',
#             'field2',
#         ]
