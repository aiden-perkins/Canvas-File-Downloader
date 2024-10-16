import os
import re
import requests
from dotenv import load_dotenv, dotenv_values
from canvasapi import Canvas
import pdfkit
load_dotenv()
access_token = os.getenv("access_token")
print(access_token)
API_URL = "https://csulb.instructure.com/"
API_KEY = access_token
headers = {'Authorization': f'Bearer {API_KEY}'}

def convert_html_to_pdf(html_content : str, pdf_path):
    try:
        pdfkit.from_string(html_content, pdf_path)
    except:
        print("failed")
    
canvas = Canvas(API_URL, API_KEY)
user = canvas.get_current_user()
terms = set()
c = user.get_courses(enrollment_type = 'student', enrollment_status = 'active')
courses = []
for i in c:
    if hasattr(i, 'course_code'):
        courses.append(i)

for course in courses:
    dirname = re.sub(r'[/\:*?<>|]', "", course.name)
    # try:
    #     os.mkdir(f"{dirname}")
    # except:
    #     print("diorectory made already!!")
    #     continue
    # os.chdir(f"./{dirname}")
    print(course.name)
    for i in course.get_modules():
        moddirname = re.sub(r'[/\:*?<>|]', "", i.name)
        print(i)
        # os.mkdir(f"{moddirname}")
        # os.chdir(f"./{moddirname}")

        for j in i.get_module_items():
            if j.type == "Page":
                print(j)
                print(f"html_url: {j.html_url}\npage_url: {j.page_url}\nurl: {j.url}\n")

                break
        # for j in i.get_module_items():
        #     if j.type == "File":
        #         try:
        #             response = requests.get(j.url, headers=headers)
        #         except:
        #             print("no link to item")
        #             continue
        #         if response.status_code == 200:
        #             try:
        #                 file_url = response.json()["url"]
        #                 with open(j.title, "wb") as file:
        #                     file.write(requests.get(file_url, headers=headers).content)
        #             except:
        #                 print("error downloading")
        #                 continue
            

    break
        # os.chdir("..")
        # os.chdir("..")
