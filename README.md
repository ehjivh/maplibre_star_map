# MapLibre GL JS 星図ビューア

ヒッパルコス星表データを用いた、ブラウザ上で動作するインタラクティブな星図ビューアです。

## 必要な環境

- Python 3.7以上
- pandas ライブラリ
- モダンなWebブラウザ（Chrome, Firefox, Edge, Safari等）

## セットアップ手順

### 1. 依存パッケージのインストール

```powershell
pip install pandas
```

### 2. データ変換

CSVデータをGeoJSON形式に変換します：

```powershell
python convert_stars.py
```

実行すると `stars.geojson` ファイルが生成されます。

### 3. Webサーバーの起動

ローカルサーバーを起動します：

```powershell
python -m http.server 8000
```

### 4. ブラウザで表示

ブラウザで以下のURLにアクセスします：

```
http://localhost:8000
```

## プロジェクト構成

```
maplibre_star_map/
├── hip.csv                 # ヒッパルコス星表データ（元データ）
├── convert_stars.py        # データ変換スクリプト
├── stars.geojson          # 変換後のGeoJSONデータ
├── index.html             # メインHTMLファイル
├── style.css              # スタイルシート
├── app.js                 # MapLibre GL JS設定とロジック
├── SPECIFICATION.md       # 詳細な実装仕様書
└── README.md              # このファイル
```

## 機能

- **星の表示**: 6等級以下の約5,000～10,000個の星を表示
- **大きさの表現**: 実視等級に基づいて星の大きさを変化
- **色の表現**: B-V色指数に基づいて星の色温度を再現
- **インタラクティブ**: 星をクリックすると詳細情報を表示

## 使い方

- **パン**: マウスドラッグまたはタッチスワイプ
- **ズーム**: マウスホイールまたはピンチジェスチャー
- **情報表示**: 星をクリックするとHIP ID、等級、B-V値が表示されます

## カスタマイズ

### 表示する星の等級を変更

`convert_stars.py` の以下の行を編集：

```python
df = df[df['Vmag'] <= 6.0].copy()  # 6.0を他の値に変更
```

### 投影法の変更

`app.js` の以下の行を編集：

```javascript
projection: 'mercator',  // 'globe' に変更すると球体表示
```

### 星の色や大きさの調整

`app.js` の `circle-radius` や `circle-color` のinterpolate式を編集します。

## トラブルシューティング

### 星が表示されない

- `stars.geojson` が生成されているか確認
- ブラウザの開発者ツール（F12）でエラーを確認
- Webサーバーが正しく起動しているか確認

### データ変換でエラーが出る

- pandas がインストールされているか確認: `pip list | grep pandas`
- `hip.csv` が同じディレクトリにあるか確認

## 詳細な技術仕様

詳細な実装仕様については `SPECIFICATION.md` を参照してください。

## ライセンス

このプロジェクトは教育目的で作成されています。
ヒッパルコス星表データは ESA の提供するパブリックデータです。

## 参考資料

- [MapLibre GL JS Documentation](https://maplibre.org/maplibre-gl-js-docs/)
- [ヒッパルコス星表](https://www.cosmos.esa.int/web/hipparcos)
- [B-V色指数](https://en.wikipedia.org/wiki/Color_index)
