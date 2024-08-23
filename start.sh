#!/bin/bash

echo "Running setup_dirs.sh"
# 创建必要的目录
mkdir -p docker_volumes/postgres_data
mkdir -p docker_volumes/es_data
echo "Directories have been created."

# # ngrok
# echo "Running ngrok setup"
# ngrok config add-authtoken 2kdrXuQMDc0mNub3nwfLgrbiJcG_51xLmqnBGyDPcdcaDMEdJ
# echo "Ngrok authtoken has been added."

# echo "Running docker-compose build django template"
# docker-compose run web django-admin startproject linebot .
# docker-compose run web python manage.py startapp hrapp
# docker-compose run web python manage.py migrate
# mkdir -p hrapp/templates
# echo "Django project has been created."

# docker-compose restart web


