import requests
from bs4 import BeautifulSoup
import os

# 유신 정미영 수능국어 - 문제 질문 게시판
CAFE_URL = "https://m.cafe.naver.com/ca-fe/web/cafes/31113195/menus/55"
TELE_TOKEN = os.environ.get("TELE_TOKEN")
TELE_ID = os.environ.get("TELE_ID")

def get_post_ids():
    headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)'}
    try:
        res = requests.get(CAFE_URL, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('a.txt_area')
        return [int(item.get('href').split('/articles/')[1].split('?')[0]) for item in items if '/articles/' in item.get('href', '')]
    except: return []

def run():
    try:
        with open("last_id.txt", "r") as f: last_id = int(f.read().strip())
        with open("count.txt", "r") as f: count = int(f.read().strip())
    except: last_id, count = 0, 0

    current_ids = sorted(get_post_ids(), reverse=True)
    if not current_ids: return

    if last_id != 0:
        new_posts = [i for i in current_ids if i > last_id]
        count += len(new_posts)

    if count >= 6:
        requests.get(f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage?chat_id={TELE_ID}&text=🔔 새 질문이 {count}개 쌓였습니다!")
        count = 0

    with open("last_id.txt", "w") as f: f.write(str(max(current_ids)))
    with open("count.txt", "w") as f: f.write(str(count))

if __name__ == "__main__":
    run()
