import json
import os
import random
import time
import requests
import sys

URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

# 🚨 가공하고자 하는 선거 종류 코드 (3: 시도지사, 4: 시군구청장)
ELEC_CODE = "3"

MAX_RETRIES = 3
MIN_DELAY = 30.0
MAX_DELAY = 50.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://info.nec.go.kr",
    "Referer": "https://info.nec.go.kr/m/main.xhtml",
    "Connection": "keep-alive"
}

CITIES = [
    {"CODE": 1100, "NAME": "서울특별시"}, {"CODE": 2600, "NAME": "부산광역시"},
    {"CODE": 2700, "NAME": "대구광역시"}, {"CODE": 2800, "NAME": "인천광역시"},
    {"CODE": 2900, "NAME": "광주광역시"}, {"CODE": 3000, "NAME": "대전광역시"},
    {"CODE": 3100, "NAME": "울산광역시"}, {"CODE": 5100, "NAME": "세종특별자치시"},
    {"CODE": 4100, "NAME": "경기도"},    {"CODE": 4200, "NAME": "강원도"},
    {"CODE": 4300, "NAME": "충청북도"},  {"CODE": 4400, "NAME": "충청남도"},
    {"CODE": 4500, "NAME": "전라북도"},  {"CODE": 4600, "NAME": "전라남도"},
    {"CODE": 4700, "NAME": "경상북도"},  {"CODE": 4800, "NAME": "경상남도"},
    {"CODE": 4900, "NAME": "제주특별자치도"}
]

def main():
    elec_code = ELEC_CODE
    # 🚨 [경로 반영] 8번 폴더에서 9번 폴더로 명확히 수정했습니다.
    output_dir = os.path.join("data", "jibang", "9")
    os.makedirs(output_dir, exist_ok=True)

    elec_name = "시도지사" if elec_code == "3" else "시군구청장"
    print(f"🔄 총 {len(CITIES)}개 시도의 제9회 지선 [{elec_name}(코드:{elec_code})] 후보자 원본 크롤링을 시작합니다.")

    for city in CITIES:
        code_str = str(city["CODE"])
        name_str = city["NAME"]

        payload = {
            "electionId": "0020260603",       
            "secondMenuId": "CPRI03",         
            "electionCode": elec_code,         
            "cityCode": code_str,             
            "statementId": f"CPRI03_#{elec_code}", 
            "dateCode": "0"
        }

        success = False
        attempt = 1

        while not success and attempt <= MAX_RETRIES:
            print(f"📡 [{name_str} 후보자] API 요청 중... (시도 {attempt}/{MAX_RETRIES}회차)")

            try:
                response = requests.post(URL, headers=HEADERS, data=payload, timeout=15)
                response.raise_for_status()
                raw_json = response.json()

                file_name = f"candidate_ori_{elec_code}_{code_str}.json"
                file_path = os.path.join(output_dir, file_name)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(raw_json, f, ensure_ascii=False, indent=4)

                print(f"🟢 [{name_str}] 다운로드 성공 -> {file_name}")
                success = True 

            except Exception as e:
                print(f"⚠️ [{name_str}] 에러 발생: {e}. 20초 대기 후 다시 시도합니다.")
                attempt += 1
                time.sleep(20)

        if not success:
            print(f"🔴 [{name_str}] 최종 실패.")

        random_delay = random.uniform(MIN_DELAY, MAX_DELAY)
        print(f"⏱️ 보호 대기 ({random_delay:.2f}초): ", end="")
        sys.stdout.flush()

        seconds_to_sleep = int(random_delay)
        for _ in range(seconds_to_sleep):
            time.sleep(1)
            print(".", end="")
            sys.stdout.flush()
        print(" [대기 종료]\n")

    print(f"✨ 모든 {elec_name} 후보자 원본 다운로드 프로세스가 종료되었습니다.")

if __name__ == "__main__":
    main()
