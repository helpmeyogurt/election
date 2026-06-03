import json
import os
import time
import requests
import random

URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

# ==========================================
# [설정 변수] 원하시는 옵션을 상단에서 편하게 수정하세요.
# ==========================================
MIN_DELAY = 10.0    # 최소 대기 시간
MAX_DELAY = 15.0    # 최대 대기 시간
MAX_RETRIES = 3     # 💡 최대 재시도 횟수 (실패 시 총 3번 더 시도)

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

def main():
    output_dir = os.path.join("data", "jibang", "9")
    os.makedirs(output_dir, exist_ok=True)

    print(f"국회의원 선거 원본 데이터 수집을 시작합니다.", flush=True)
    print(f"설정 옵션 - 대기 범위: {MIN_DELAY}초 ~ {MAX_DELAY}초 | 최대 재시도: {MAX_RETRIES}회", flush=True)

    # 🛠️ 들여쓰기 정상화 완료
    code_str = "0000"
    name_str = "국회의원보궐"

    payload = {
        "electionId": "0020260603",
        "secondMenuId": "VCCP09",
        "electionCode": "2",
        "cityCode": "0",
        "statementId": "VCCP09_#2",
    }

    success = False
        
    # 재시도 루프 구성 (0번째 시도가 최초 시도이며, 이후 MAX_RETRIES까지 회차 증가)
    for attempt in range(MAX_RETRIES + 1):
        if attempt == 0:
            print(f"\n[{name_str}] 데이터 요청 중 (코드: {code_str})...", flush=True)
        else:
            print(f"🔄 [{name_str}] 네트워크 지연/실패로 인해 재시도 중... ({attempt}/{MAX_RETRIES}회차)", flush=True)

        try:
            # 네트워크 일시 먹통 방지 타임아웃 10초 설정
            response = requests.post(URL, headers=HEADERS, data=payload, timeout=10)
            response.raise_for_status()
            raw_json = response.json()

            if "jsonResult" in raw_json and raw_json["jsonResult"].get("success") == "false":
                print(f"⚠️ [{name_str}] API 내부 오류 메시지: {raw_json['jsonResult'].get('message')}", flush=True)

            file_path = os.path.join(output_dir, f"ori_2_{code_str}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(raw_json, f, ensure_ascii=False, indent=4)

            print(f"🟢 [{name_str}] 원본 파일 저장 완료 -> {file_path}", flush=True)
            success = True
            break # 요청 성공 시 재시도 루프 탈출
                
        except requests.exceptions.Timeout:
            print(f"🟡 [{name_str}] 요청 타임아웃 제한 시간(10초) 초과", flush=True)
        except Exception as e:
            print(f"🔴 [{name_str}] 에러 발생: {e}", flush=True)

        # 실패했고, 아직 재시도 기회가 남아있다면 잠시 쉬었다가 다음 회차로 진행
        if attempt < MAX_RETRIES:
            retry_delay = round(random.uniform(MIN_DELAY, MAX_DELAY), 2)
            print(f"⏳ {retry_delay}초 동안 랜덤 대기 후 다음 재시도를 수행합니다...", flush=True)
            time.sleep(retry_delay)

    if not success:
        print(f"❌ [{name_str}] 최종 수집 실패 (총 {MAX_RETRIES + 1}회 시도 모두 실패)", flush=True)

    print("\n모든 작업이 완료되었습니다.", flush=True)

if __name__ == "__main__":
    main()
