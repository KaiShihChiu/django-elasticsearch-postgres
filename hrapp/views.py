import logging

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBadRequest
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from .models import Customer, Patent, LineMessage
import os
from pathlib import Path
LOCAL_DIR = Path(__file__).resolve().parent
from django.contrib import messages
from django.shortcuts import render, redirect
# from .forms import UploadPPTForm
# from .models import UploadedPPT
# from .tasks import process_ppt_files

# views.py
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
import sqlite3
import os
import csv
# from .forms import TableSelectionForm
from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponseNotFound
import io
import zipfile
import pandas as pd
from io import BytesIO

########## Settings ##########
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


########## Data uploading ##########
from .management.commands.upload_data import Command
from .forms import UploadPPTForm
from .models import UploadedPPT

def upload_ppt(request):
    if request.method == 'POST':
        form = UploadPPTForm(request.POST, request.FILES)
        if form.is_valid():
            ppt_file = request.FILES['file']  # 获取上传的文件
            # 检查数据库中是否已经存在相同名称的文件
            if UploadedPPT.objects.filter(file__icontains=ppt_file.name).exists():
                messages.error(request, 'PPT 文件已存在，請上傳其他文件。')
            else:
                ppt_instance = form.save()  # 保存到資料庫，返回的是已保存的對象
                # file_path = ppt_instance.file.path  # 獲取文件的完整路徑
                # 上傳成功後直接運行 upload_data.py 的邏輯
                command = Command()
                command.handle()
                
                # 刪除已處理的 PPT 文件
                # if os.path.exists(file_path):
                #     os.remove(file_path)
                return redirect('upload_success')
    else:
        form = UploadPPTForm()
    return render(request, 'upload_ppt.html', {'form': form})

def upload_success(request):
    return render(request, 'upload_success.html')


########## Data downloading ##########
from .forms import TableSelectionForm

def download_selected_tables(request):
    if request.method == 'POST':
        form = TableSelectionForm(request.POST)
        if form.is_valid():
            selected_tables = form.cleaned_data['tables']
            file_size_limit = 50 * 1024 * 1024  # 50MB
            zip_buffer = BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                for table in selected_tables:
                    file_counter = 1
                    current_file_size = 0
                    buffer = BytesIO()

                    db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')

                    with sqlite3.connect(db_path) as conn:
                        df = pd.read_sql_query(f'SELECT * FROM "{table}"', conn)

                        # The 'with' statement automatically saves and closes the Excel file
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                            df.to_excel(writer, sheet_name=table, index=False)

                        # After writing, retrieve the contents of the buffer
                        excel_data = buffer.getvalue()
                        current_file_size += len(excel_data)

                        if current_file_size > file_size_limit:
                            part_file_name = f"{table}_part{file_counter}.xlsx"
                            zip_file.writestr(part_file_name, excel_data)
                            file_counter += 1
                            current_file_size = 0
                            buffer.seek(0)
                            buffer.truncate(0)

                        # Write remaining data
                        if current_file_size > 0:
                            part_file_name = f"{table}_part{file_counter}.xlsx"
                            zip_file.writestr(part_file_name, excel_data)

            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="selected_tables.zip"'
            return response
    else:
        form = TableSelectionForm()

    return render(request, 'download_tables.html', {'form': form})


########## Elasticsearch settings ##########
from .documents import PatentDocument
from linebot.models import CarouselTemplate, CarouselColumn, TemplateSendMessage, URITemplateAction

def search_patents(query):
    # 在 title 和 description 中搜索
    search = PatentDocument.search().query("multi_match", query=query, fields=["title", "description"])
    response = search.execute()
    return response

# def format_search_results(results):
#     # 格式化搜索结果
#     formatted_results = []
#     for result in results:
#         formatted_results.append(f"Title: {result.title}\nDescription: {result.description[:50]}...")
#     return "\n\n".join(formatted_results)

def create_carousel_message(patents):
    columns = []

    # Domain URL for building complete image URLs
    domain = settings.CSRF_TRUSTED_ORIGINS[0]

    # Limit to a maximum of 10 Carousel Columns
    for patent in patents[:10]:
        # Ensure every patent has an image; use a placeholder if not
        image_url = f"{domain}/media/{patent.image}" if patent.image else f"{domain}/media/default-placeholder.png"
        print(f"image: {patent.image}")
        print(f"Image URL: {image_url}")
        # Ensure title and description fit within LINE's constraints
        title = patent.title[:40] if patent.title else "No Title"
        text = patent.description[:60] if patent.description else "No Description"

        # Create a Carousel Column
        column = CarouselColumn(
            thumbnail_image_url=image_url,
            title=title,
            text=text,
            actions=[
                URITemplateAction(
                    label="查看詳情",
                    uri=f"{domain}/hrapp/patents/{patent.id}"  # Link to the patent's detail page
                )
            ]
        )
        columns.append(column)

    # Check if any columns were created; otherwise return a message indicating no results
    if not columns:
        return TextSendMessage(text="未找到與您的搜尋相關的資料。")

    # Create and return the Carousel Template
    carousel_template = CarouselTemplate(columns=columns)
    return TemplateSendMessage(alt_text="搜索结果", template=carousel_template)


########## PPT description (carsoral) ##########
from django.shortcuts import render, get_object_or_404

def parse_description(description):
    sections = description.split('\n\n')  # Split based on empty lines
    parsed_sections = {}

    for section in sections:
        if '預期用途' in section:
            parsed_sections['預期用途'] = section.replace('預期用途', '').strip()
        elif '技術架構' in section:
            parsed_sections['技術架構'] = section.replace('技術架構', '').strip()
        elif '競爭優勢' in section:
            parsed_sections['競爭優勢'] = section.replace('競爭優勢', '').strip()
        elif '應用範圍' in section:
            parsed_sections['應用範圍'] = section.replace('應用範圍', '').strip()
        elif '技術合作夥伴' in section:
            parsed_sections['技術合作夥伴'] = section.replace('技術合作夥伴', '').strip()
        elif '研究成果和獎項' in section:
            parsed_sections['研究成果和獎項'] = section.replace('研究成果和獎項', '').strip()
        elif '關鍵字' in section:
            parsed_sections['關鍵字'] = section.replace('關鍵字', '').strip()
    
    return parsed_sections

def patent_detail(request, patent_id):
    patent = get_object_or_404(Patent, id=patent_id)
    parsed_sections = parse_description(patent.description)
    return render(request, 'patent_detail.html', {'patent': patent, 'parsed_sections': parsed_sections})


########### Welcome message, flex message ##########
from linebot.models import FollowEvent
from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, SeparatorComponent, ButtonComponent, ImageComponent, URIAction
)

def send_question_intro(event):
    # 构建 Flex Message 的内容
    bubble = BubbleContainer(
        # hero=ImageComponent(
        #     url="https://your-image-url.com/welcome-image.jpg",
        #     size="full",
        #     aspect_ratio="20:13",
        #     aspect_mode="cover",
        #     action=URIAction(uri="https://your-website.com", label="Learn More")
        # ),
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text="歡迎使用我們的服務！", weight="bold", size="xl", color="#1DB446"),
                SeparatorComponent(margin='md'),
                TextComponent(text="請回答以下問題", size="md", color="#555555"),
                SeparatorComponent(margin='md'),
                TextComponent(text="1. 請問您的名字是？", size="md", color="#111111"),
                SeparatorComponent(margin='sm'),
                TextComponent(text="2. 請問您的職業是？", size="md", color="#111111"),
                SeparatorComponent(margin='sm'),
                TextComponent(text="3. 請問您的專業是？", size="md", color="#111111"),
                SeparatorComponent(margin='md'),
            ]
        ),
        footer=BoxComponent(
            layout='vertical',
            spacing='sm',
            contents=[
                # ButtonComponent(
                #     style='link',
                #     height='sm',
                #     action=URIAction(label="了解更多", uri="https://your-website.com")
                # ),
                # SeparatorComponent(margin='md'),
                TextComponent(text="開始您的旅程吧！", size="xs", color="#aaaaaa", align="center"),
            ]
        )
    )

    # 创建 Flex Message
    flex_message = FlexSendMessage(alt_text="請回答問題", contents=bubble)
    
    # 发送 Flex Message 和第一个问题
    line_bot_api.reply_message(
        event.reply_token, 
        [flex_message, TextSendMessage(text="請問您的名字是？")]
    )

user_states = {}
def save_answer(user_id, question, answer):
    # 获取或创建 Customer 实例
    customer, created = Customer.objects.get_or_create(user_id=user_id)

    # 根据问题更新相应的字段
    if question == 'name':
        customer.name = answer
        profile = line_bot_api.get_profile(user_id)
        customer.user_name = profile.display_name  # 获取用户的显示名称
    elif question == 'occupation':
        customer.occupation = answer
    elif question == 'specialty':
        customer.specialty = answer
    
    # 保存更新后的 Customer 实例
    customer.save()

def update_user_state(user_id, state):
    # 更新用户的状态
    user_states[user_id] = state

def get_user_state(user_id):
    customer, created = Customer.objects.get_or_create(user_id=user_id)
    print(f"Customer: {customer.name}, Created: {created}")

    if created or customer.name == None:
        print("New user")
        return user_states.get(user_id, 'start')
    else:
        return user_states.get(user_id, 'complete')


@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    send_question_intro(event)
    update_user_state(user_id, 'asking_name')


########## Serial answering and keyword searching ##########
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()
    user_state = get_user_state(user_id)
    
    # update_user_state(user_id, 'start')
    # send_question_intro(event)

    # if user_state == 'start':
    #     # 初始化状态，并发送问题介绍和第一个问题
    #     update_user_state(user_id, 'asking_name')
    #     send_question_intro(event)
    if user_state == 'asking_name':
        # 保存第一个问题的答案并问第二个问题
        save_answer(user_id, question='name', answer=user_message)
        update_user_state(user_id, 'asking_occupation')
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請問您的職業是？")
        )
    elif user_state == 'asking_occupation':
        # 保存第二个问题的答案并问第三个问题
        save_answer(user_id, question='occupation', answer=user_message)
        update_user_state(user_id, 'asking_specialty')
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請問您的專業是？")
        )
    elif user_state == 'asking_specialty':
        # 保存第三个问题的答案并结束对话
        save_answer(user_id, question='specialty', answer=user_message)
        update_user_state(user_id, 'complete')
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text="感謝您的回答，所有問題已完成！請輸入關鍵字查詢相關技術；或是點選下方選單瞭解更多！")],
            #  TextSendMessage(text="请稍后选择您感兴趣的类别。")]
        )
        # assign_rich_menu(user_id)
   
   
    elif user_state == 'complete':
        # 处理用户选择的类别
        # print(user_state)
        # rich_id = get_or_create_rich_menu()

        # rich_menu_list = line_bot_api.get_rich_menu_list()
        # for rm in rich_menu_list:
        #     print(f"Rich Menu ID: {rm.rich_menu_id}, Name: {rm.name}")
        #     # 如果有图片，检验图片 URL
        #     try:
        #         image_content = line_bot_api.get_rich_menu_image(rm.rich_menu_id)
        #         print(f"Rich Menu {rm.rich_menu_id} has an associated image.")
        #         # 上传 Rich Menu 的图像

        #     except Exception as e:
        #         print(f"No image found for Rich Menu ID {rm.rich_menu_id}: {e}")
        #         image_path = os.path.join(LOCAL_DIR, 'static', 'images', 'rich_menu_1.png')
        #         try:
        #             with open(image_path, 'rb') as f:
        #                 line_bot_api.set_rich_menu_image(rm.rich_menu_id, 'image/png', f)
        #                 print(f"Image uploaded for Rich Menu ID {rm.rich_menu_id}")
        #         except Exception as e:
        #             print(f"Error uploading image for Rich Menu ID {rm.rich_menu_id}: {e}")

        # line_bot_api.link_rich_menu_to_user(user_id, rich_menu_id)
        # assign_rich_menu(user_id)
        
        if user_message == "专利":
            # 获取所有专利内容
            patents = Patent.objects.all()
            if patents.exists():
                messages = [TextSendMessage(text=f"专利名称: {patent.title}\n描述: {patent.description}\n链接: {patent.link}") for patent in patents]
                line_bot_api.push_message(user_id, messages)  # 使用 push_message 发送
            else:
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text="目前没有相关的专利信息。")
                )
        else:
            customer = Customer.objects.get(user_id=user_id)
            # chat_message, created = LineMessage.objects.create(customer=customer)

            # 创建一个新的 LineMessage 实例，每个实例存储一条新消息
            new_chat_message = LineMessage.objects.create(
                customer=customer,
                messages=user_message  # 这里直接保存用户发送的消息
            )

            # 保存新消息实例
            new_chat_message.save()
            
            # 搜索专利
            search_results = search_patents(user_message)

            if search_results:
                # 格式化搜索结果
                # response_message = format_search_results(search_results)
                print(f"Search results: {search_results}")
                carousel_message = create_carousel_message(search_results)
                line_bot_api.reply_message(event.reply_token, carousel_message)
            else:
                response_message = "很抱歉，沒有找到相關訊息。"
                # 回复用户搜索结果
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_message)
                )

            
            # # 處理關鍵字查詢
            # keyword_patents = Patent.objects.filter(description__icontains=user_message)
            # # fuzzy_patents = fuzzy_search(user_message)

            # # Convert QuerySet to a list and combine with fuzzy search results
            # keyword_patents_list = list(keyword_patents)
            # combined_patents = list(set(keyword_patents_list + fuzzy_patents))

            # # Sort the combined list if needed
            # combined_patents = sorted(combined_patents, key=lambda patent: patent.created_at, reverse=True)


            # # if patents.exists():
            # if len(combined_patents)>0:
            #     carousel_message = create_carousel_message(combined_patents)
            #     line_bot_api.reply_message(event.reply_token, carousel_message)
            # else:
            #     line_bot_api.reply_message(
            #         event.reply_token,
            #         TextSendMessage(text="未找到與您的搜尋相關的資料。")
            #     )
            
            ###### 使用 Flex Message 顯示 ######
            # if patents.exists():
            #     flex_messages = [create_flex_message(patent) for patent in patents]
            #     line_bot_api.reply_message(event.reply_token, flex_messages)
            # else:
            #     line_bot_api.reply_message(
            #         event.reply_token,
            #         TextSendMessage(text="未找到與您的搜尋相關的資料。")
            #     )
            
            
            # 处理其他选择或重新显示类别选择
            # send_category_selection(user_id)  # 使用 push_message 发送
            # assign_rich_menu(user_id)
    else:
        # 处理其他状态和逻辑
        pass
    

