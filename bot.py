import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import pytz

# --- 설정 ---
CAFE_URL = "https://m.cafe.naver.com/ca-fe/web/cafes/31113195/menus/55"
TELE_TOKEN = os.environ.get("TELE_TOKEN")
TELE_ID = os.environ.get("TELE_ID")
COUNT_FILE = "total_count.txt"     # 리셋 이후 누적 글 개수 저장
LAST_ID_FILE = "last_id.txt"      # 마지막으로 확인한 글 번호 저장
LAST_RESET_FILE = "last_reset_week.txt"

def get_latest_post_ids():
    headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15'}
    try:
        res = requests.get(CAFE_URL, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('a.txt_area')
        ids = []
        for item in items:
            href = item.get('href', '')
            if '/articles/' in href:
                post_id = int(href.split('/articles/')[1].split('?')[0])
                ids.append(post_id)
        return sorted(ids) # 과거 글부터 확인하기 위해 오름차순 정렬
    except:
        return []

def run():
    # 1. 한국 시간 설정
    korea_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea_tz)
    
    # [시간 판별] 일요일 22시 ~ 월요일 22시 사이인가?
    current_week = now.isocalendar()[1]
    is_after_sun_22 = (now.weekday() == 6 and now.hour >= 22)
    is_before_mon_22 = (now.weekday() == 0 and now.hour < 22)
    is_active_time = is_after_sun_22 or is_before_mon_22

    # 2. 리셋 로직 (매주 일요일 22시가 되면 카운트 0으로 초기화)
    try:
        with open(LAST_RESET_FILE, "r") as f: last_reset_week = int(f.read().strip())
    except: last_reset_week = -1

    if is_after_sun_22 and last_reset_week != current_week:
        with open(COUNT_FILE, "w") as f: f.write("0")
        with open(LAST_ID_FILE, "w") as f: f.write("0") # 리셋 직후엔 이전 글 무시
        with open(LAST_RESET_FILE, "w") as f: f.write(str(current_week))
        total_count = 0
        last_id = 0
        print("일요일 22시: 이번 주 카운팅을 리셋합니다.")
    else:
        try:
            with open(COUNT_FILE, "r") as f: total_count = int(f.read().strip())
            with open(LAST_ID_FILE, "r") as f: last_id = int(f.read().strip())
        except: total_count, last_id = 0, 0

    # 3. 가동 시간 확인
    if not is_active_time:
        print("현재는 가동 시간이 아닙니다. (일요일 22시 ~ 월요일 22시만 작동)")
        return

    # 4. 새 글 확인 및 알림
    current_ids = get_latest_post_ids()
    if not current_ids: return

    # 리셋 후 첫 실행일 때, 현재 가장 최신 글 번호를 last_id로 설정 (이전 글은 안 침)
    if last_id == 0:
        last_id = max(current_ids)
        with open(LAST_ID_FILE, "w") as f: f.write(str(last_id))
        print(f"모니터링 시작. 기준 글 번호: {last_id}")
        return

    new_posts = [pid for pid in current_ids if pid > last_id]
    
    for pid in new_posts:
        total_count += 1
        # ⭐ [핵심 조건] 리셋 후 1번째, 7번째, 13번째 글인지 확인
        # 숫자를 6으로 나누었을 때 나머지가 1이면 1, 7, 13... 입니다.
        if total_count % 6 == 1:
            msg = f"🔔 [국어 카페] {total_count}번째 게시글이 올라왔습니다! (번호: {pid})"
            requests.get(f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage?chat_id={TELE_ID}&text={msg}")
            print(f"알림 전송 완료: {total_count}번째 글")

        last_id = pid # 확인한 글 번호 업데이트

    # 5. 최종 장부 저장
    with open(COUNT_FILE, "w") as f: f.write(str(total_count))
    with open(LAST_ID_FILE, "w") as f: f.write(str(last_id))

if __name__ == "__main__":
    run()
