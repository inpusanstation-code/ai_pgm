#naver.com news crawler
import requests

url = "https://news.naver.com"
response = requests.get(url)
print(response.status_code)

#if requests module is not installed, install it using pip:
# pip install requests


if response.status_code == 200:
    print("Successfully accessed the website.")
    print(response.text)  # Print the HTML content of the page






