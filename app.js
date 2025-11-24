// MapLibre GL JSの初期化
const map = new maplibregl.Map({
	container: 'map',
	style: {
		version: 8,
		sources: {},
		layers: [{
			id: 'background',
			type: 'background',
			paint: {
				'background-color': '#000000'
			}
		}],
		projection: {
			type: 'mercator'
		}
	},
	center: [0, 0],
	zoom: 1.5,
	maxZoom: 10,
	minZoom: 0,
	renderWorldCopies: true
});

// エラーハンドリング
map.on('error', (e) => {
	console.error('マップエラー:', e);
	if (e.error && e.error.message && e.error.message.includes('stars.geojson')) {
		alert('stars.geojsonが見つかりません。先にconvert_stars.pyを実行してください。');
	}
});

// 星レイヤーのセットアップ関数
function setupStarsLayer() {
	// 星データソースを追加
	map.addSource('stars', {
		type: 'geojson',
		data: './stars.geojson',
		cluster: false,
		tolerance: 0
	});

	// 星レイヤーを追加
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

	// インタラクション設定
	map.on('mouseenter', 'stars-layer', () => {
		map.getCanvas().style.cursor = 'pointer';
	});

	map.on('mouseleave', 'stars-layer', () => {
		map.getCanvas().style.cursor = '';
	});

	map.on('click', 'stars-layer', (e) => {
		const coordinates = e.features[0].geometry.coordinates.slice();
		const properties = e.features[0].properties;

		while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
			coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
		}

		new maplibregl.Popup()
			.setLngLat(coordinates)
			.setHTML(`
                <strong>HIP ${properties.id}</strong><br>
                等級: ${properties.mag.toFixed(2)}<br>
                B-V: ${properties.bv.toFixed(2)}<br>
                色: ${getStarColorName(properties.bv)}
            `)
			.addTo(map);
	});
}

// 初期ロード時の処理
map.on('load', () => {
	setupStarsLayer();
	setupProjectionToggle();
	console.log('星図マップの初期化が完了しました');
});

// プロジェクション切り替え機能のセットアップ
function setupProjectionToggle() {
	const mercatorBtn = document.getElementById('mercator-btn');
	const globeBtn = document.getElementById('globe-btn');

	// Mercatorボタンのクリックイベント
	mercatorBtn.addEventListener('click', () => {
		if (!mercatorBtn.classList.contains('active')) {
			map.setProjection({
				type: 'mercator'
			});
			mercatorBtn.classList.add('active');
			globeBtn.classList.remove('active');
			console.log('プロジェクションをMercatorに変更しました');
		}
	});

	// Globeボタンのクリックイベント
	globeBtn.addEventListener('click', () => {
		if (!globeBtn.classList.contains('active')) {
			map.setProjection({
				type: 'globe'
			});
			globeBtn.classList.add('active');
			mercatorBtn.classList.remove('active');
			console.log('プロジェクションをGlobeに変更しました');
		}
	});
}

// B-V値から星の色名を取得する補助関数
function getStarColorName(bv) {
	if (bv < -0.3) return '青白';
	if (bv < -0.1) return '青';
	if (bv < 0.15) return '白青';
	if (bv < 0.45) return '白';
	if (bv < 0.75) return '黄白';
	if (bv < 1.05) return '黄';
	if (bv < 1.35) return '橙';
	if (bv < 1.75) return '赤橙';
	return '赤';
}