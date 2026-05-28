import json
import os

SOURCE_DIR = os.path.join("data", "jibang", "8")
OUTPUT_FILE = "all_sgg_data_2022.json"
PARTY_COLORS = {
    "더불어민주당": "#152484", "국민의힘": "#E61E2B", "더불어민주연합": "#152484", "국민의미래": "#E61E2B",
    "녹색정의당": "#007C36", "새로운미래": "#46bbbd", "개혁신당": "#FF7920", "진보당": "#D6001C",
    "자유통일당": "#E24A49", "조국혁신당": "#004099", "기본소득당": "#00D2C3", "무소속": "#8b8b8b",
    "국민의당": "#EA5504", "미래통합당": "#EF426F", "미래한국당": "#EF426F", "더불어시민당": "#006CB7",
    "정의당": "#ffca05", "열린민주당": "#003E98", "소나무당": "#1A246B", "우리공화당": "#009944",
    "한국국민당": "#013588", "새진보연합": "#00d2c3", "없음": "#8b8b8b"
}

def merge_all_sgg_data():
    all_merged_data = []
    
    # 🟢 [합산용 누적 변수 초기화]
    total_sunsu_sum = 0
    total_tusu_sum = 0
    win_party_counter = {}

    sido_codes = ["1100","2600","2700","2800","2900","3000","3100","5100","4100","4200","4300","4400","4500","4600","4700","4800","4900"]

    print("🚀 전국 시군구 데이터 병합을 시작합니다.")

    for code in sido_codes:
        file_path = os.path.join(SOURCE_DIR, f"4_{code}.json")
        if not os.path.exists(file_path): continue

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            for city_name, sgg_list in data.items():
                for entry in sgg_list:
                    # '합계' 행은 전국 합계 계산용 누적 데이터로 활용
                    if entry.get("SGGNAME") == "합계":
                        total_sunsu_sum += int(str(entry.get("SUNSU", "0")).replace(",", ""))
                        total_tusu_sum += int(str(entry.get("TUSU", "0")).replace(",", ""))
                        # 정당별 당선 횟수 합산 (해당 데이터 구조에 맞게)
                        for p in entry.get("data", []):
                            win_party_counter[p["name"]] = win_party_counter.get(p["name"], 0) + p["value"]
                        continue
                    
                    # 지도용 데이터 병합
                    all_merged_data.append({
                        "name": entry.get("name"),
                        "value": entry.get("value"),
                        "nametxt": entry.get("nametxt"),
                        "SDNAME": entry.get("SDNAME")
                    })
    
    # 🟢 [전국 합계 노드 생성 및 추가]
    summary_pie_data = [{"name": p, "value": c, "itemStyle": {"color": PARTY_COLORS.get(p, "#8b8b8b")}} 
                        for p, c in win_party_counter.items()]
    
    summary_node = {
        "name": 0,
        "nametxt": "전국 합계",
        "SUNSU": total_sunsu_sum,
        "TUSU": total_tusu_sum,
        "data": summary_pie_data
    }
    
    # 🟢 [중요]: all_merged_data의 맨 앞에 전국 합계 노드를 삽입
    all_merged_data.insert(0, summary_node)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_merged_data, f, ensure_ascii=False, indent=4)
    
    print(f"✨ 완료! 전국 데이터 저장됨: {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_all_sgg_data()
