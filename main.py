import os
import re
import glob
import requests
import json
from dotenv import load_dotenv
from canvasapi import Canvas
from xhtml2pdf import pisa
import logging

load_dotenv()

logger = logging.getLogger('main')
logging.basicConfig(level=logging.WARNING)

API_URL = 'https://csulb.instructure.com/'
API_KEY = os.getenv('access_token')
HEADERS = {'Authorization': f'Bearer {API_KEY}'}
FILE_CLEANER_PATTERN = r'[/:*?<>|[\]!"]'


def check_for_files(filepath_pattern):
    for filepath in glob.glob(filepath_pattern):
        if os.path.isfile(filepath):
            return True
    return False

def save_api_json_content(module_item_title, url):
    if not os.path.exists(re.sub(FILE_CLEANER_PATTERN, '', f'{module_item_title}.json')):
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            rsp_json = response.json()
                
            with open(re.sub(FILE_CLEANER_PATTERN, '', f'{module_item_title}.json'), 'w') as file:
                file.write(json.dumps(rsp_json, indent=4))
        
            return rsp_json
        else:
            logger.error(f'Bad response code: {response.status_code}, text: {response.text}')
            return False
            
    return False

def convert_html_to_pdf(html_string, pdf_path):
    with open(re.sub(FILE_CLEANER_PATTERN, '', pdf_path), 'wb') as pdf_file:
        pisa_status = pisa.CreatePDF(html_string, dest=pdf_file)
    return pisa_status.err

def main():
    canvas = Canvas(API_URL, API_KEY)
    user = canvas.get_current_user()
    c = user.get_courses(enrollment_type = 'student', enrollment_status = 'active')
    courses = []

    # 219 for fall 2024
    # 222 for spring 2025
    enrollment_term_ids = [219, 222]

    # grab the intended courses
    for i in c:
        if hasattr(i, 'course_code') and i.enrollment_term_id in enrollment_term_ids:
            courses.append(i)
            logger.info(i)

    # make courses folder to not clog the git project
    try:
        os.mkdir(f'Courses')
    except FileExistsError:
        pass
    os.chdir(f'./Courses')

    for course in courses:
        
        # make a folder for the course
        dirname = re.sub(FILE_CLEANER_PATTERN, '', course.name)
        try:
            os.mkdir(f'{dirname}')
        except FileExistsError:
            pass
        os.chdir(f'./{dirname}')
        logger.info(f'Course: {course.name}')
        
        external_links = []
        
        for module in course.get_modules():
            
            # make a folder for the module
            moddirname = re.sub(FILE_CLEANER_PATTERN, '', module.name)
            logger.info(f'Module: {moddirname}')
            try:
                os.mkdir(f'./{moddirname}')
            except FileExistsError:
                pass
            os.chdir(f'./{moddirname}')

            for module_item in module.get_module_items():
                
                if module_item.type == 'Page':
                    new_data = save_api_json_content(module_item.title, module_item.url)

                    if new_data:
                        pdf_filename = f'{module_item.title}.pdf'
                        
                        if 'body' not in new_data and 'locked_for_user' in new_data and new_data['locked_for_user']:
                            logger.warning(f'Skipping {pdf_filename} because the page is locked for the user.')
                            continue
                        cnv = convert_html_to_pdf(new_data['body'], pdf_filename)
                        if cnv:
                            logger.error(f'Conversion from html to pdf error: {cnv}')
                
                elif module_item.type == 'File':
                    new_data = save_api_json_content(module_item.title, module_item.url)

                    if new_data:
                        filename = module_item.title
                        
                        file_mime_class = new_data['mime_class']
                        
                        if file_mime_class not in filename:
                            filename = filename + f'.{file_mime_class}'
                        
                        if not os.path.exists(re.sub(FILE_CLEANER_PATTERN, '', filename)):
                            with open(re.sub(FILE_CLEANER_PATTERN, '', filename), 'wb') as file:
                                file.write(requests.get(new_data['url'], headers=HEADERS).content)
                
                elif module_item.type == 'SubHeader':
                    # just a sub header title, no content, can be skipped
                    continue
                
                elif module_item.type == 'Assignment':
                    new_data = save_api_json_content(module_item.title, module_item.url)
                    
                    if new_data:
                        pdf_filename = f'{module_item.title}.pdf'
                    
                        if 'description' not in new_data and 'locked_for_user' in new_data and new_data['locked_for_user']:
                            logger.warning(f'Skipping {pdf_filename} because the page is locked for the user.')
                            continue
                        cnv = convert_html_to_pdf(new_data['description'], pdf_filename)
                        if cnv:
                            logger.error(f'Conversion from html to pdf error: {cnv}')
                
                elif module_item.type == 'Discussion':
                    save_api_json_content(module_item.title, module_item.url)
                
                elif module_item.type == 'ExternalUrl':
                    external_links.append((module_item.title, module_item.external_url))
                
                elif module_item.type == 'Quiz':
                    save_api_json_content(module_item.title, module_item.url)
                
                elif module_item.type == 'ExternalTool':
                    # not much to be done here except save them as external links
                    external_links.append((module_item.title, module_item.external_url))
                
                else:
                    logger.error(f'Unrecognized module item type: {module_item.type}')
            
            os.chdir('..')  
        
        # TODO check:
        # home page
        # syllabus tab
        # discussions
        # quizzes
        # assignments - covers module type Assignments
        # files
        # grades
        # pages - covers module type Page
        # people
        
        if external_links:
            
            # if not os.path.exists('external-urls.txt'):
                with open(re.sub(FILE_CLEANER_PATTERN, '', 'external-urls.txt'), 'w') as file:
                    file.write('\n'.join([f'{a}: {b}' for a, b in external_links]))
        
        os.chdir('..')

if __name__ == '__main__':
    main()
