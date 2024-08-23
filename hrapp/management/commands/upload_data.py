from django.core.management.base import BaseCommand
from hrapp.models import Patent, UploadedPPT  # 导入你的模型
import os
from django.core.files import File
from hrapp.management.data.readppt import PptExtractor
from django.conf import settings

import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Upload data from uploaded PPT files to the database'
    
    def handle(self, *args, **kwargs):
        ppt_files = UploadedPPT.objects.all()
        logger.info(f"Found {len(ppt_files)} uploaded PPT files")

        for ppt in ppt_files:
            file_path = ppt.file.path
            output_dir = settings.MEDIA_ROOT

            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}, skipping...")
                
            

            logger.info(f"Processing {file_path}")

            ppt_extractor = PptExtractor(file_path, output_dir)
            titles, extracted_content = ppt_extractor.extract_sections_and_images()

            for slide_num, (title, content) in enumerate(zip(titles, extracted_content), start=1):
                logger.info(f"Processing slide {slide_num}: Title: {title}, Content: {content}")

                image_path = os.path.join(output_dir, f"slide_{slide_num}_image_1.png")
                
                if os.path.exists(image_path):
                    relative_image_path = os.path.relpath(image_path, settings.MEDIA_ROOT)

                    with open(image_path, 'rb') as img_file:
                        patent = Patent(
                            ppt=ppt,  # 将每个Patent与对应的UploadedPPT关联
                            title=title if title else f"Slide {slide_num}",
                            description=content,
                            image=File(img_file, name=relative_image_path),
                            slide_number=slide_num,
                        )
                        patent.save()
                        logger.info(f"Saved image from slide {slide_num} to {relative_image_path} with ID: {patent.id}")
                else:
                    patent = Patent(
                        ppt=ppt,  # 将每个Patent与对应的UploadedPPT关联
                        title=title if title else f"Slide {slide_num}",
                        description=content,
                        image=None,
                        slide_number=slide_num,
                    )
                    patent.save()
                    logger.info(f"No image found for slide {slide_num}, saved patent with ID: {patent.id}")
        
        logger.info('Successfully uploaded extracted content from all uploaded PPT files to the database')
