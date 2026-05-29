import os
import json
import requests
from datetime import datetime, timedelta

# 1. 고정 설정 및 경로 지정 (사장님 피드백 반영 경로 교정)
TARGET_URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"
FILE_PATH = "data/jibang/9/jibang_vote_9.js"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://info.nec.go.kr",
    "Referer": "https://info.nec.go.kr/m/main.xhtml"
}

def get_current_time_code():
    """서버 시간에 9시간을 더해 한국 표준시(KST)를 구하고 timeCode 생성"""
    kst_now = datetime.utcnow() + timedelta(hours=9)
    current_hour = kst_now.hour
    
    if current_hour < 6:
        return "06"
    elif current_hour > 18:
        return "18"
    return f"{current_hour:02d}"

def find_data_list(obj):
    """🎯 [핵심 알고리즘] 선관위 응답 트리 구조가 바뀌더라도 WIWID나 TPR_SU를 포함한 실제 데이터 리스트를 자동 탐색"""
    if isinstance(obj, list):
        if len(obj) > 0 and isinstance(obj[0], dict) and ("WIWID" in obj[0] or "TPR_SU" in obj[0]):
            return obj
        for item in obj:
            res = find_data_list(item)
            if res:
                return res
    elif isinstance(obj, dict):
        for key, value in obj.items():
            res = find_data_list(value)
            if res:
                return res
    return None

def fetch_nec_data(time_code):
    payload = {
        "electionId": "0020260603",
        "secondMenuId": "VCAP01",
        "cityCode": "0",
        "dateCode": "1",
        "timeCode": time_code,
        "statementId": "VCAP01_#1",
        "prevoteDate1": "20260529",
        "prevoteDate2": "20260530"
    }
    
    try:
        response = requests.post(TARGET_URL, headers=HEADERS, data=payload, timeout=10)
        response.raise_for_status()
        raw_json = response.json()
        
        # 1차 시도: 기존 예측 기본 구조 파싱
        if isinstance(raw_json, dict) and "jsonResult" in raw_json and "model" in raw_json["jsonResult"]:
            model_data = raw_json["jsonResult"]["model"]
            if isinstance(model_data, list) and len(model_data) > 0:
                return model_data
                
        # 2차 시도: 응답 구조 유동성에 대응하기 위해 자동 리스트 검색 알고리즘 가동
        found = find_data_list(raw_json)
        if found:
            return found
            
        # 둘 다 실패 시 원본 데이터를 그대로 넘겨 디버깅 로그에 출력하도록 함
        return raw_json
    except Exception as e:
        print(f"[{datetime.now()}] 선관위 API 통신 실패 (시간코드: {time_code}): {e}")
        return None

def load_existing_js_file():
    if not os.path.exists(FILE_PATH):
        return [{"0": [], "1": [], "2": []}]
        
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content.startswith("[") or content.startswith("{"):
                return json.loads(content)
            else:
                json_string = content[content.find("["):content.rfind("]")+1]
                return json.loads(json_string)
    except Exception as e:
        print(f"기존 파일 읽기 실패 (새 파일 구조로 대체 시작): {e}")
        return [{"0": [], "1": [], "2": []}]

def save_js_file(data):
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    try:
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json_content = json.dumps(data, ensure_ascii=False, indent=2)
            f.write(json_content)
    except Exception as e:
        print(f"파일 저장 실패: {e}")

def main():
    time_code = get_current_time_code()
    print(f"[{datetime.now()}] 투표율 데이터 수집 프로세스 가동 (타겟 시간: {time_code}시)")
    
    raw_data = fetch_nec_data(time_code)
    
    # 🛑 상세 예외 검증 및 친절한 디버깅 분기문
    if raw_data is None:
        print("선관위 API 서버로부터 응답 데이터를 받지 못했습니다.")
        return
        
    if isinstance(raw_data, list) and len(raw_data) == 0:
        print(f"ℹ️ 선관위 서버에 아직 {time_code}시 데이터가 최종 업데이트되지 않았습니다. (빈 배열 반환 상태)")
        print("잠시 후 다음 정각 스케줄(또는 수동 실행) 시 자동으로 이어서 가져옵니다.")
        return
        
    if not isinstance(raw_data, list):
        print("⚠️ 선관위 응답 결과가 리스트 형식이 아닙니다. 아래 디버깅 리포트를 확인해 주세요.")
        print(f"응답 데이터의 타입: {type(raw_data)}")
        print(f"응답 데이터 내용(일부): {str(raw_data)[:1000]}")
        return

    # 정상적인 지역별 데이터 리스트 확보 성공
    new_hour_data = raw_data
    current_db = load_existing_js_file()
    
    # 중복 체크 공정 (숫자형/문자형 WIWID 완벽 방어)
    try:
        new_seoul_tuyul = next(item["TPR_SU"] for item in new_hour_data if str(item.get("WIWID")) == "1100" or item.get("WIWNAME") == "서울특별시")
    except StopIteration:
        new_seoul_tuyul = None

    is_duplicated = False
    if new_seoul_tuyul:
        for existing_hour_list in current_db[0]["0"]:
            try:
                ex_seoul_tuyul = next(item["TPR_SU"] for item in existing_hour_list if str(item.get("WIWID")) == "1100" or item.get("WIWNAME") == "서울특별시")
                if ex_seoul_tuyul.strip() == new_seoul_tuyul.strip():
                    is_duplicated = True
                    break
            except StopIteration:
                continue

    if is_duplicated:
        print(f"✅ {time_code}시 데이터는 이미 파일에 병합되어 있습니다. 중복 방지를 위해 건너뜁니다.")
        return

    # 데이터 누적 후 저장
    current_db[0]["0"].append(new_hour_data)
    save_js_file(current_db)
    print(f"🚀 [{datetime.now()}] {time_code}시 투표율 데이터 병합 및 '{FILE_PATH}' 업데이트 성공!")

if __name__ == "__main__":
    main()
