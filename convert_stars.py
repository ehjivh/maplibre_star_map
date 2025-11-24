import pandas as pd
import json

print("CSVファイルを読み込み中...")

# CSVの読み込み（ヘッダーなし、エラー行をスキップ）
df = pd.read_csv('hip.csv', header=None, on_bad_lines='skip', engine='python')

print(f"読み込んだ行数: {len(df)}")
print(f"カラム数: {df.shape[1]}")

# カラム名を割り当て（最初の14カラムのみ使用）
expected_cols = ['HIP_ID', 'RA_h', 'RA_m', 'RA_s', 'Dec_sign', 'Dec_d', 
                 'Dec_m', 'Dec_s', 'Vmag', 'SpType', 'Col10', 'Col11', 
                 'BV', 'Col13']

# カラム数が14を超える場合は最初の14カラムのみ使用
if df.shape[1] > 14:
    df = df.iloc[:, :14]
elif df.shape[1] < 14:
    print(f"警告: カラム数が不足しています ({df.shape[1]} < 14)")

df.columns = expected_cols

# 等級6.0以下でフィルタリング
df = df[df['Vmag'] <= 6.0].copy()

# 座標変換関数
def convert_coordinates(row):
    try:
        # 赤経を度数法に変換
        ra_deg = (float(row['RA_h']) + float(row['RA_m'])/60 + 
                  float(row['RA_s'])/3600) * 15
        
        # 赤緯を度数法に変換（符号を適用）
        dec_deg = float(row['Dec_sign']) * (float(row['Dec_d']) + 
                  float(row['Dec_m'])/60 + float(row['Dec_s'])/3600)
        
        # 地図投影用に経度を反転
        lon = -ra_deg
        if lon < -180:
            lon = lon + 360
        
        lat = dec_deg
        
        return lon, lat
    except (ValueError, TypeError):
        return None, None

# B-V色指数のクリーニング
def clean_bv(value):
    try:
        bv = float(value)
        # 異常値のクリッピング
        return max(-0.5, min(2.5, bv))
    except (ValueError, TypeError):
        return 0.6  # デフォルト値（白色星）

# GeoJSON Features生成
features = []
skipped = 0
for idx, row in df.iterrows():
    try:
        lon, lat = convert_coordinates(row)
        
        # 座標変換に失敗した場合はスキップ
        if lon is None or lat is None:
            skipped += 1
            continue
        
        bv = clean_bv(row['BV'])
        
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "id": int(row['HIP_ID']),
                "mag": float(row['Vmag']),
                "bv": bv
            }
        }
        features.append(feature)
    except (ValueError, TypeError, KeyError) as e:
        skipped += 1
        continue

# GeoJSON作成
geojson = {
    "type": "FeatureCollection",
    "features": features
}

# ファイル出力
with open('stars.geojson', 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

print(f"変換完了: {len(features)}個の星を出力しました")
if skipped > 0:
    print(f"スキップした行: {skipped}行")
