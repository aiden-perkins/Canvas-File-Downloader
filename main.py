import os
import re
import requests
from dotenv import load_dotenv, dotenv_values
from canvasapi import Canvas
from xhtml2pdf import pisa
load_dotenv()
access_token = os.getenv("access_token")
API_URL = "https://csulb.instructure.com/"
API_KEY = access_token
headers = {'Authorization': f'Bearer {API_KEY}'}

def convert_html_to_pdf(html_string, pdf_path):
    with open(pdf_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(html_string, dest=pdf_file)
    return not pisa_status.err


canvas = Canvas(API_URL, API_KEY)
user = canvas.get_current_user()
c = user.get_courses(enrollment_type = 'student', enrollment_status = 'active')
courses = []
for i in c:
    if hasattr(i, 'course_code') and i.enrollment_term_id == 219: #219 for fall 2024
        courses.append(i)
        print(i)

for course in courses:
    dirname = re.sub(r'[/\:*?<>|]', "", course.name)
    try:
        os.mkdir(f"{dirname}")
    except:
        print("diorectory made already!!")
        continue
    os.chdir(f"./{dirname}")
    print(course.name)
    for i in course.get_modules():
        moddirname = re.sub(r'[/\:*?<>|]', "", i.name)
        os.mkdir(f"{moddirname}")
        os.chdir(f"./{moddirname}")

        for j in i.get_module_items():
            if j.type == "Page":
                response = requests.get(j.url, headers=headers)
                html_content = response.json()["body"]
                pdf_filename = f"{j.title}.pdf"  
                try:
                    convert_html_to_pdf(html_content, pdf_filename)
                except Exception as e:
                    print(f"ERROR {e}")
            if j.type == "File":
                print(dir(j))
                print(j.url)
                try:
                    response = requests.get(j.url, headers=headers)
                except:
                    print("no link to item")
                    continue
                if response.status_code == 200:
                    try:
                        file_url = response.json()["url"]
                        file_mime_class = response.json()["mime_class"]
                        filename = j.title
                        if file_mime_class not in filename:
                            filename = filename + f".{file_mime_class}"
                        with open(filename, "wb") as file:
                            file.write(requests.get(file_url, headers=headers).content)
                    except:
                        print("error downloading")
                        continue
        os.chdir("..")  
    os.chdir("..")