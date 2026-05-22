import json
import os
import random  # 🚨 랜덤 지연 생성을 위해 추가
import time
import requests

URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

# 🚨 가공하고자 하는 선거 종류 코드 (3: 시도지사, 4: 시군구청장)
ELEC_CODE = "3"

# 🚨 실패 시 최대 재시도 횟수 지정 (무한 루프 방지용)
MAX_RETRIES = 3

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
    {"CODE": 1100, "NAME": "서울특별시"},
    {"CODE": 2600, "NAME": "부산광역시"},
    {"CODE": 2700, "NAME": "대구광역시"},
    {"CODE": 2800, "NAME": "인천광역시"},
    {"CODE": 2900, "NAME": "광주광역시"},
    {"CODE": 3000, "NAME": "대전광역시"},
    {"CODE": 3100, "NAME": "울산광역시"},
    {"CODE": 5100, "NAME": "세종특별자치시"},
    {"CODE": 4100, "NAME": "경기도"},
    {"CODE": 4200, "NAME": "강원도"},
    {"CODE": 4300, "NAME": "충청북도"},
    {"CODE": 4400, "NAME": "충청남도"},
    {"CODE": 4500, "NAME": "전라북도"},
    {"CODE": 4600, "NAME": "전라남도"},
    {"CODE": 4700, "NAME": "경상북도"},
    {"CODE": 4800, "NAME": "경상남도"},
    {"CODE": 4900, "NAME": "제주특별자치도"},
]

def main():
    elec_code = ELEC_CODE
    
    output_dir = os.path.join("data", "jibang", "8")
    os.makedirs(output_dir, exist_ok=True)

    elec_name = "시도지사" if elec_code == "3" else "시군구청장"
    print(f"🔄 총 {len(CITIES)}개 시도의 [{elec_name}(코드:{elec_code})] 원본 크롤링을 시작합니다.")
    print(f"⏱️ 각 시도별 요청 간격 대기 시간: 5초 ~ 10초 무작위(Random) 적용")

    for city in CITIES:
        code_str = str(city["CODE"])
        name_str = city["NAME"]

        payload = {
            "electionId": "0000000000", 
            "electionType": "4", 
            "sgDivMenuId": "VCCP09",
            "electionName": "20220601", 
            "electionCode": elec_code,       
            "electionCodeId": elec_code,     
            "electionNameSgType": "1", 
            "cityCode": code_str, 
            "oldElectionType": "1",
            "statementId": f"VCCP09_#{elec_code}", 
        }

        # 🚨 [재시도 메커니즘 탑재] 성공할 때까지 루프 수행 (최대 3회)
        success = False
        attempt = 1

        while not success and attempt <= MAX_RETRIES:
            print(f"📡 [{name_str}] 원본 요청 중... (시도 {attempt}/{MAX_RETRIES}회 자) [코드: {code_str}]")

            try:
                # 타임아웃을 15초로 설정하여 장시간 대기 차단
                response = requests.post(URL, headers=HEADERS, data=payload, timeout=15)
                response.raise_for_status()
                raw_json = response.json()

                file_name = f"ori_{elec_code}_{code_str}.json"
                file_path = os.path.join(output_dir, file_name)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(raw_json, f, ensure_ascii=False, indent=4)

                print(f"🟢 [{name_str}] 다운로드 성공 -> {file_name}")
                success = True  # 성공 플래그를 True로 바꾸어 while 루프 탈출

            except requests.exceptions.Timeout:
                print(f"⚠️ [{name_str}] 요청 타임아웃 제한 시간 초과. 잠시 후 다시 시도합니다.")
                attempt += 1
                time.sleep(10)  # 서버가 끈끈할 수 있으므로 에러 시에는 10초 고정 대기 후 재시도
            except Exception as e:
                print(f"⚠️ [{name_str}] 데이터 수집 실패 에러: {e}. 잠시 후 다시 시도합니다.")
                attempt += 1
                time.sleep(10)

        # 만약 최대 재시도 횟수를 넘겨서 실패한 경우 로그에 기록
        if not success:
            print(f"🔴 [{name_str}] 총 {MAX_RETRIES}회 재시도했으나 최종 실패했습니다. 다음 시도로 넘어갑니다.")

        # 🚨 [수정 반영] 성공 여부와 상관없이 다음 시도로 넘어가기 전 5~10초 사이의 랜덤 지연시간 부여
        random_delay = random.uniform(30.0, 50.0)
        print(f"⏱️ 보호 대기: {random_delay:.2f}초 동안 다음 요청을 멈춥니다.\n")
        time.sleep(random_delay)

    print(f"✨ 모든 시도의 원본 API JSON 백업 작업 프로세스가 완료되었습니다.")

if __name__ == "__main__":
    main()
