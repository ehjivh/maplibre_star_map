import pandas as pd
import json

print("CSVファイルを読み込み中...")

# CSVの読み込み（ヘッダーなし、エラー行をスキップ）
df = pd.read_csv('hip.csv', header=None, on_bad_lines='skip', engine='python')

print(f"読み込んだ行数: {len(df)}")

expected_cols = ['HIP_ID', 'RA_h', 'RA_m', 'RA_s', 'Dec_sign', 'Dec_d', 
                 'Dec_m', 'Dec_s', 'Vmag', 'SpType', 'Col10', 'Col11', 
                 'BV', 'Col13']

if df.shape[1] > 14:
    df = df.iloc[:, :14]
df.columns = expected_cols

# 座標変換関数
def convert_coordinates(row):
    try:
        ra_deg = (float(row['RA_h']) + float(row['RA_m'])/60 + float(row['RA_s'])/3600) * 15
        dec_deg = float(row['Dec_sign']) * (float(row['Dec_d']) + float(row['Dec_m'])/60 + float(row['Dec_s'])/3600)
        
        lon = -ra_deg
        if lon < -180:
            lon = lon + 360
        
        lat = dec_deg
        return lon, lat
    except (ValueError, TypeError):
        return None, None

coords = {}
for idx, row in df.iterrows():
    try:
        hip = int(row['HIP_ID'])
        lon, lat = convert_coordinates(row)
        if lon is not None:
            coords[hip] = (lon, lat)
    except (ValueError, TypeError):
        pass

print(f"座標変換成功: {len(coords)}件")

# 星座線の読み込み
lines_df = pd.read_csv('hip_constellation_line.csv', header=None, names=['Constellation', 'Start', 'End'])

features = []
skipped = 0
for idx, row in lines_df.iterrows():
    start_hip = row['Start']
    end_hip = row['End']
    
    if start_hip in coords and end_hip in coords:
        lon1, lat1 = coords[start_hip]
        lon2, lat2 = coords[end_hip]
        
        # 180度線をまたぐ場合の処理
        if abs(lon1 - lon2) > 180:
            if lon1 > lon2:
                lon2 += 360
            else:
                lon1 += 360
                
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[lon1, lat1], [lon2, lat2]]
            },
            "properties": {
                "constellation": row['Constellation']
            }
        }
        features.append(feature)
    else:
        skipped += 1

geojson = {
    "type": "FeatureCollection",
    "features": features
}

with open('constellation_lines.geojson', 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

print(f"変換完了: {len(features)}本の線を出力しました")
if skipped > 0:
    print(f"スキップした線: {skipped}本")
