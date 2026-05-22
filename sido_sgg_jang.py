import json
import os
import time
import requests

URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

# 🚨 [수정 반영] 크롤링 대기 시간 변수 (초 단위로 자유롭게 조절하세요)
# 예: 1.5 = 1.5초 대기, 0.5 = 0.5초 대기
DELAY_SEC = 50

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
    # 저장할 선거 종류 코드 (3: 시도지사, 4: 시군구청장)
    elec_code = "4"
    
    output_dir = os.path.join("data", "jibang", "8")
    os.makedirs(output_dir, exist_ok=True)

    print(f"🔄 총 {len(CITIES)}개 시도의 [시군구청장(코드:{elec_code})] 원본 크롤링을 시작합니다.")
    print(f"⏱️ 각 시도별 요청 간격 대기 시간: {DELAY_SEC}초")

    for city in CITIES:
        code_str = str(city["CODE"])
        name_str = city["NAME"]

        print(f"📡 [{name_str}] 원본 요청 중 (코드: {code_str})...")

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

        try:
            response = requests.post(URL, headers=HEADERS, data=payload, timeout=15)
            response.raise_for_status()
            raw_json = response.json()

            file_name = f"ori_{elec_code}_{code_str}.json"
            file_path = os.path.join(output_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(raw_json, f, ensure_ascii=False, indent=4)

            print(f"🟢 [{name_str}] 다운로드 완료 -> {file_name}")

        except requests.exceptions.Timeout:
            print(f"🔴 [{name_str}] 요청 타임아웃 제한 시간 초과 (15초)")
        except Exception as e:
            print(f"🔴 [{name_str}] 데이터 수집 실패 에러: {e}")

        # 🚨 상단에 정의한 DELAY_SEC 변수를 적용하여 대기합니다.
        time.sleep(DELAY_SEC)

    print(f"✨ 모든 시도의 원본 API JSON 백업 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()
