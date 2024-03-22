import requests
import os


env = os.environ.get("ENV")
def send_email(user_email, task_name, body):
    if env == 'local' or 'dev':
        logic_app_url = "https://prod-96.westeurope.logic.azure.com:443/workflows/2ed57eb41e314fb88d70715a5a1ca3d2/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=UmhjQG2PzV7_ZFyg1Hn2ZvKhVyY7Nk5bo_gSqCT0p0Q"

    if env == 'prod':
        logic_app_url = "https://prod-37.westeurope.logic.azure.com:443/workflows/b4c1f7b7d17846789f2430735c50cf8e/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Cb58TQchm_7oN10tCewYXEt8T-XAJsnNhSK8lmQHlMw"

    payload = {
        "body": body,
        "subject": task_name,
        "email": user_email
    }

    try:
        response = requests.post(logic_app_url, json=payload)

        # Check the response status code to verify if the request was successful
        if response.status_code == 202:
            print(f"Completion email sent to {user_email} for task {task_name}.")
            return True
        else:
            print("Error sending completion email.")
            return False

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending the completion email: {e}")
        return False


# user_email = session["okta_attributes"]["email"]
# user_email = 'aniketc@sigmoidanalytics.com'
# task_name = "Campaign READY TO DELIVER"
# body = "THIS IS EMAIL BODY"


# if send_completion_email(user_email, task_name, body):
#     print("Email sent successfully.")
# else:
#     print("Email sending failed.")