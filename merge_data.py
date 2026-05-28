import json
import os

# 데이터가 저장된 폴더 경로 (기존 8회차 데이터 경로)
SOURCE_DIR = os.path.join("data", "jibang", "8")
OUTPUT_FILE = "all_sgg_data_2022.json"

def merge_all_sgg_data():
    all_merged_data = []

    # 17개 시도 코드 리스트
    sido_codes = ["1100","2600","2700","2800","2900","3000","3100","5100","4100","4200","4300","4400","4500","4600","4700","4800","4900"]

    print("🚀 전국 시군구 데이터 병합을 시작합니다.")

    for code in sido_codes:
        file_path = os.path.join(SOURCE_DIR, f"4_{code}.json")
        
        if not os.path.exists(file_path):
            print(f"⚠️ 파일을 찾을 수 없습니다: {file_path}")
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # 데이터 구조에 따라 키(시도명)를 찾아 리스트로 변환
                # (예: {"서울특별시": [...]})
                for city_name, sgg_list in data.items():
                    for entry in sgg_list:
                        # 🚨 [규칙]: '합계' 행은 제외
                        if entry.get("SGGNAME") == "합계":
                            continue
                        
                        # 🟢 추출: name(시군구코드)과 value(정당인덱스 등)
                        # 필요에 따라 다른 필드를 추가해도 됩니다.
                        merged_item = {
                            "name": entry.get("name"),
                            "value": entry.get("value"),
                            "nametxt": entry.get("nametxt"),
                            "SDNAME": entry.get("SDNAME")
                        }
                        all_merged_data.append(merged_item)
                        
            print(f"✅ [{code}] 병합 완료.")
            
        except Exception as e:
            print(f"🔴 [{code}] 오류 발생: {e}")

    # 결과물 저장
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_merged_data, f, ensure_ascii=False, indent=4)
    
    print(f"✨ 전국 데이터 병합이 완료되었습니다. 저장 위치: {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_all_sgg_data()
