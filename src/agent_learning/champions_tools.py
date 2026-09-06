from calendar import c
import json
from pathlib import Path


DATA_file_path_champions = Path(__file__).parent / "data" / "champions.json"
DATA_file_path_regions = Path(__file__).parent / "data" / "regions.json"


def get_champion_info(champion_name: str) -> dict:
    """读取英雄信息。"""
    with open(DATA_file_path_champions, "r") as f:
        champions = json.load(f)

    query = champion_name.strip().lower()

    for champion_id, champion_data in champions.items():
        searchable_names = {
            champion_id.lower(),
            champion_data.get("name_cn", "").lower(),
            champion_data.get("name_i8n", "").lower(),
            champion_data.get("title", "").lower(),
        }

        if query in searchable_names:
            return {
                "success": True,
                "champion_Id": champion_id,
                "champion_data": champion_data
            }

    return {
        "success": False,
        "message": "未找到该英雄"
    }


def list_champions(region: str = "") -> dict:
    """列出资料库中的英雄；传入 region 时，只返回该地区的英雄。"""
    with open(DATA_file_path_regions, "r") as f:
        regions = json.load(f)

    if not region:
        all_champions = []

        for region_data in regions.values():
            all_champions.extend(region_data.get("champions", []))

        return {
            "success": True,
            "region": "全部",
            "champion_count": len(all_champions),
            "champions": all_champions,
        }
    elif region not in regions:
        return {
            "success": False,
            "message": f"未找到该地区: {region}"
        }
    else:
        return {
            "success": True,
            "region": region,
            "champion_count": regions.get(region).get("champion_count", 0),
            "champions": regions.get(region).get("champions", [])
        }

if __name__ == "__main__":
    # 测试示例
    #print(get_champion_info("阿狸"))
    print(get_champion_info("狂暴之心"))
    print(get_champion_info("狼人"))
