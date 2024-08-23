# 定义一些常量
PYTHON := python
MANAGE := $(PYTHON) manage.py

# 默认目标，当只运行 `make` 时执行
.PHONY: all
all: migrate runserver

# 迁移数据库
.PHONY: migrate
migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate

# create superuser
.PHONY: super
super:
	$(MANAGE) createsuperuser

# check postgresql
.PHONY: check
check:
	$(PYTHON) check_messages.py

# 运行单元测试
.PHONY: test
test:
	$(MANAGE) test

# 清理 .pyc 文件和 __pycache__ 目录
.PHONY: clean
clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

# 迁移数据库
.PHONY: index
indexing:
	$(MANAGE) search_index --rebuild

# debug
.PHONY: debug
debug:
	$(MANAGE) shell