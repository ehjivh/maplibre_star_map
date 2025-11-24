# MapLibre GL JS 星図ビューア - 実装仕様書

## プロジェクト概要

ヒッパルコス星表データ（`hip.csv`）を用いて、ブラウザ上で動作するインタラクティブな星図ビューアを開発する。MapLibre GL JSを用いて天球を地図投影し、星の明るさと色温度を視覚的に表現する。

---

## 1. 入力データ仕様

### 1.1 ファイル形式
- **ファイル名**: `hip.csv`
- **形式**: ヘッダーなしCSV（カンマ区切り）
- **エンコーディング**: UTF-8
- **総行数**: 約118,000行

### 1.2 カラム構成

| Index | カラム名   | 説明                     | 例      |
| ----- | ---------- | ------------------------ | ------- |
| 0     | `HIP_ID`   | ヒッパルコスカタログID   | `1`     |
| 1     | `RA_h`     | 赤経（時）               | `00`    |
| 2     | `RA_m`     | 赤経（分）               | `00`    |
| 3     | `RA_s`     | 赤経（秒）               | `00.22` |
| 4     | `Dec_sign` | 赤緯符号（`+1` or `-1`） | `+1`    |
| 5     | `Dec_d`    | 赤緯（度）               | `01`    |
| 6     | `Dec_m`    | 赤緯（分）               | `05`    |
| 7     | `Dec_s`    | 赤緯（秒）               | `20.4`  |
| 8     | `Vmag`     | 実視等級                 | `9.10`  |
| 9     | `SpType`   | スペクトル型             | `F5`    |
| 10-11 | (未使用)   | -                        | -       |
| 12    | `B-V`      | 色指数（B-V）            | `0.482` |
| 13    | (未使用)   | -                        | -       |

### 1.3 データサンプル

```csv
1,00,00,00.22,+1,01,05,20.4,9.10,F5,3.54,1.39,0.482,0.025
2,00,00,00.91,-1,19,29,55.8,9.27,K3V,21.90,3.10,0.999,0.002
3,00,00,01.20,+1,38,51,33.4,6.61,B9,2.81,0.63,-0.019,0.004
```

---

## 2. データ処理ロジック（Python実装）

### 2.1 スクリプト仕様

**ファイル名**: `convert_stars.py`

**目的**: ヒッパルコス星表CSVをMapLibre用GeoJSONに変換する

**依存ライブラリ**:
```python
pandas
json
```

### 2.2 座標変換アルゴリズム

#### 2.2.1 赤経の10進法変換

```
RA_deg = (RA_h + RA_m/60 + RA_s/3600) × 15
```

- **理由**: 赤経は24時間系で360度を表現するため、15倍（360÷24）して度数法に変換
- **範囲**: 0° ～ 360°

**実装例**:
```python
ra_deg = (row[1] + row[2]/60 + row[3]/3600) * 15
```

#### 2.2.2 赤緯の10進法変換

```
Dec_deg = Dec_sign × (Dec_d + Dec_m/60 + Dec_s/3600)
```

- **注意**: `Dec_sign`（Col 4）は数値 `+1` または `-1` として格納されている
- **範囲**: -90° ～ +90°

**実装例**:
```python
dec_deg = row[4] * (row[5] + row[6]/60 + row[7]/3600)
```

#### 2.2.3 地図投影用の座標変換（重要）

天球は「見上げる」投影であり、通常の地図「見下ろす」投影とは東西が反転する。この補正を行う。

**経度（Longitude）変換**:
```
Longitude = -RA_deg
```

その後、-180° ～ +180° に正規化:
```python
if lon > 180:
    lon = lon - 360
```

**緯度（Latitude）変換**:
```
Latitude = Dec_deg
```
（符号はそのまま）

### 2.3 データフィルタリング

**条件**: 実視等級（Vmag）が **6.0以下** の星のみ抽出

**理由**: 
- 肉眼で見える星の限界が約6等級
- データ量削減（118,000行 → 約5,000～10,000行）
- ブラウザでのレンダリング性能向上

**実装例**:
```python
df = df[df['Vmag'] <= 6.0]
```

### 2.4 色指数（B-V）の処理

**使用カラム**: Col 12

**データ品質チェック**:
- 欠損値（空文字列、NaN）の場合は中間値（例: 0.6）で補完
- 異常値（-1.0 ～ 3.0 の範囲外）は中間値で補完

**実装例**:
```python
bv = row[12] if pd.notna(row[12]) and row[12] != '' else 0.6
bv = max(-0.5, min(2.5, float(bv)))  # クリッピング
```

### 2.5 出力GeoJSON仕様

**ファイル名**: `stars.geojson`

**構造**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [longitude, latitude]
      },
      "properties": {
        "id": 1,
        "mag": 2.5,
        "bv": 0.482
      }
    }
  ]
}
```

**プロパティ説明**:
- `id`: ヒッパルコスID（整数）
- `mag`: 実視等級（浮動小数点）
- `bv`: B-V色指数（浮動小数点）

### 2.6 完全な実装コード

```python
import pandas as pd
import json

# CSVの読み込み（ヘッダーなし）
df = pd.read_csv('hip.csv', header=None)

# カラム名を割り当て
df.columns = ['HIP_ID', 'RA_h', 'RA_m', 'RA_s', 'Dec_sign', 'Dec_d', 
              'Dec_m', 'Dec_s', 'Vmag', 'SpType', 'Col10', 'Col11', 
              'BV', 'Col13']

# 等級6.0以下でフィルタリング
df = df[df['Vmag'] <= 6.0].copy()

# 座標変換関数
def convert_coordinates(row):
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
for idx, row in df.iterrows():
    lon, lat = convert_coordinates(row)
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

# GeoJSON作成
geojson = {
    "type": "FeatureCollection",
    "features": features
}

# ファイル出力
with open('stars.geojson', 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

print(f"変換完了: {len(features)}個の星を出力しました")
```

---

## 3. フロントエンド実装仕様（MapLibre GL JS）

### 3.1 技術スタック

- **MapLibre GL JS**: v4.x以上
- **HTML/CSS/JavaScript**: バニラJS（フレームワーク不使用）

### 3.2 ファイル構成

```
maplibre_star_map/
├── hip.csv                 # 元データ
├── convert_stars.py        # 変換スクリプト
├── stars.geojson          # 変換後データ
├── index.html             # メインHTML
├── style.css              # スタイルシート
└── app.js                 # MapLibre初期化・スタイリング
```

### 3.3 MapLibre初期設定

#### 3.3.1 基本設定

```javascript
const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    sources: {},
    layers: []
  },
  center: [0, 0],
  zoom: 1.5,
  projection: 'mercator',  // または 'globe'
  maxZoom: 10,
  minZoom: 0
});
```

#### 3.3.2 背景色設定

完全な黒背景を実現:

```javascript
style: {
  version: 8,
  sources: {},
  layers: [
    {
      id: 'background',
      type: 'background',
      paint: {
        'background-color': '#000000'
      }
    }
  ]
}
```

**CSS補助**:
```css
body {
  margin: 0;
  padding: 0;
  background-color: #000000;
}

#map {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 100%;
  background-color: #000000;
}
```

### 3.4 データソース設定

```javascript
map.on('load', () => {
  map.addSource('stars', {
    type: 'geojson',
    data: './stars.geojson'
  });
});
```

### 3.5 Data-Driven Styling

#### 3.5.1 星の大きさ（circle-radius）

**要件**: 実視等級（mag）に基づき、明るい星（小さい等級値）を大きく、暗い星を小さく表示

**interpolate式**:
```javascript
'circle-radius': [
  'interpolate',
  ['linear'],
  ['get', 'mag'],
  -1.5,  8,   // -1.5等星 → 半径8px（シリウスなど）
   0.0,  7,   //  0.0等星 → 半径7px
   1.0,  6,   //  1等星   → 半径6px
   2.0,  4.5, //  2等星   → 半径4.5px
   3.0,  3.5, //  3等星   → 半径3.5px
   4.0,  2.5, //  4等星   → 半径2.5px
   5.0,  1.8, //  5等星   → 半径1.8px
   6.0,  1.0  //  6等星   → 半径1px
]
```

**ロジック説明**:
- 等級が1増える（暗くなる）ごとに半径を段階的に縮小
- 視覚的な明るさの差を直感的に表現

#### 3.5.2 星の色（circle-color）

**要件**: B-V色指数に基づき、星の色温度を再現

**色温度対応表**:

| B-V値 | 色   | 星の例       | 色コード  |
| ----- | ---- | ------------ | --------- |
| -0.4  | 青白 | リゲル       | `#9BB2FF` |
| -0.2  | 青   | スピカ       | `#AABfFF` |
| 0.0   | 白青 | ベガ         | `#CAD8FF` |
| 0.3   | 白   | プロキオン   | `#F8F7FF` |
| 0.6   | 黄白 | 太陽         | `#FFF4E8` |
| 0.9   | 黄   | カペラ       | `#FFE4B5` |
| 1.2   | 橙   | アルデバラン | `#FFD2A1` |
| 1.5   | 赤橙 | アンタレス   | `#FFBD6F` |
| 2.0   | 赤   | 超赤色巨星   | `#FF9030` |

**interpolate式**:
```javascript
'circle-color': [
  'interpolate',
  ['linear'],
  ['get', 'bv'],
  -0.4, '#9BB2FF',  // 青白（O型星）
  -0.2, '#AABfFF',  // 青（B型星）
   0.0, '#CAD8FF',  // 白青（A型星）
   0.3, '#F8F7FF',  // 白（F型星）
   0.6, '#FFF4E8',  // 黄白（G型星・太陽）
   0.9, '#FFE4B5',  // 黄（K型星）
   1.2, '#FFD2A1',  // 橙（K型星）
   1.5, '#FFBD6F',  // 赤橙（M型星）
   2.0, '#FF9030'   // 赤（M型星）
]
```

**科学的根拠**:
- B-V色指数は星の表面温度と相関
- 負の値ほど高温（青）、正の値ほど低温（赤）
- カラーコードは天文学的な観測結果に基づく

#### 3.5.3 その他のスタイル

```javascript
'circle-opacity': 0.9,
'circle-blur': 0.15,  // 星のにじみ効果
'circle-stroke-width': 0
```

### 3.6 完全なレイヤー設定

```javascript
map.addLayer({
  id: 'stars-layer',
  type: 'circle',
  source: 'stars',
  paint: {
    'circle-radius': [
      'interpolate',
      ['linear'],
      ['get', 'mag'],
      -1.5, 8,
       0.0, 7,
       1.0, 6,
       2.0, 4.5,
       3.0, 3.5,
       4.0, 2.5,
       5.0, 1.8,
       6.0, 1.0
    ],
    'circle-color': [
      'interpolate',
      ['linear'],
      ['get', 'bv'],
      -0.4, '#9BB2FF',
      -0.2, '#AABfFF',
       0.0, '#CAD8FF',
       0.3, '#F8F7FF',
       0.6, '#FFF4E8',
       0.9, '#FFE4B5',
       1.2, '#FFD2A1',
       1.5, '#FFBD6F',
       2.0, '#FF9030'
    ],
    'circle-opacity': 0.9,
    'circle-blur': 0.15,
    'circle-stroke-width': 0
  }
});
```

### 3.7 インタラクティブ機能（オプション）

#### 3.7.1 星のホバー情報

```javascript
map.on('mouseenter', 'stars-layer', (e) => {
  map.getCanvas().style.cursor = 'pointer';
  
  const properties = e.features[0].properties;
  const popup = new maplibregl.Popup()
    .setLngLat(e.lngLat)
    .setHTML(`
      <strong>HIP ${properties.id}</strong><br>
      等級: ${properties.mag.toFixed(2)}<br>
      B-V: ${properties.bv.toFixed(2)}
    `)
    .addTo(map);
});

map.on('mouseleave', 'stars-layer', () => {
  map.getCanvas().style.cursor = '';
});
```

---

## 4. プロジェクション選択ガイド

### 4.1 Mercatorプロジェクション

**特徴**:
- 標準的な2D地図投影
- 東西のパンが無限にループ
- 極域の歪みが大きい

**推奨用途**: 全天を平面的に閲覧したい場合

**設定**:
```javascript
projection: 'mercator'
```

### 4.2 Globeプロジェクション

**特徴**:
- 3D地球儀表示
- 回転・ズームで天球を直感的に操作
- より天文学的な視点に近い

**推奨用途**: 没入感のある星図体験

**設定**:
```javascript
projection: 'globe'
```

**注意**: MapLibre GL JS v3.0以降で利用可能

---

## 5. 実装手順

### 5.1 開発フロー

1. **データ変換**
   ```bash
   python convert_stars.py
   ```
   → `stars.geojson` が生成される

2. **HTMLファイル作成**
   - MapLibre GL JSのCDNを読み込み
   - `<div id="map"></div>` を配置

3. **JavaScriptでMapLibre初期化**
   - 黒背景を設定
   - GeoJSONをロード
   - Data-Driven Stylingを適用

4. **ブラウザで確認**
   - ローカルサーバーで起動（例: `python -m http.server`）
   - `http://localhost:8000` でアクセス

### 5.2 デバッグポイント

- **星が表示されない**: ブラウザの開発者ツールでGeoJSONのロードエラーを確認
- **色がおかしい**: B-V値の範囲を確認（-0.5～2.5に収まっているか）
- **大きさが不自然**: 等級フィルタリング（6.0以下）が正しく機能しているか

---

## 6. パフォーマンス最適化

### 6.1 データ量削減

- Vmag 6.0以下のフィルタリングで約10分の1に削減
- 必要に応じて4等級以下に変更可能（より明るい星のみ）

### 6.2 レンダリング最適化

```javascript
map.addSource('stars', {
  type: 'geojson',
  data: './stars.geojson',
  cluster: false,  // クラスタリング無効
  tolerance: 0     // 座標精度維持
});
```

---

## 7. 拡張機能案

### 7.1 星座線の追加

別途星座線データ（LineStringのGeoJSON）を追加し、`line`レイヤーで描画

### 7.2 検索機能

特定のヒッパルコスIDで星を検索し、フライトアニメーション

### 7.3 等級スライダー

UIで表示する等級範囲を動的にフィルタリング

```javascript
map.setFilter('stars-layer', ['<=', ['get', 'mag'], selectedMag]);
```

---

## 8. 数式まとめ

### 座標変換

$$
\text{RA}_{\text{deg}} = \left(\text{RA}_h + \frac{\text{RA}_m}{60} + \frac{\text{RA}_s}{3600}\right) \times 15
$$

$$
\text{Dec}_{\text{deg}} = \text{Dec}_{\text{sign}} \times \left(\text{Dec}_d + \frac{\text{Dec}_m}{60} + \frac{\text{Dec}_s}{3600}\right)
$$

### 地図投影変換

$$
\text{Longitude} = -\text{RA}_{\text{deg}} \mod 360 \quad (\text{範囲: } -180° \sim +180°)
$$

$$
\text{Latitude} = \text{Dec}_{\text{deg}}
$$

---

## 9. 参考資料

- [MapLibre GL JS Documentation](https://maplibre.org/maplibre-gl-js-docs/)
- [ヒッパルコス星表](https://www.cosmos.esa.int/web/hipparcos)
- [B-V色指数と恒星の色](https://en.wikipedia.org/wiki/Color_index)

---

**文書バージョン**: 1.0  
**作成日**: 2025年11月24日  
**対象読者**: 天文データ解析とWebGIS開発に精通したエンジニア
