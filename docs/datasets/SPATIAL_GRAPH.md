# Province Spatial Graph

## File repository

```text
data/processed/province_knn_graph.csv
```

## Tujuan

Graph digunakan untuk menambahkan konteks harga regional. Hipotesisnya: perubahan harga pada provinsi yang secara geografis dekat dapat membantu memprediksi level dan arah harga provinsi target.

Graph ini adalah **engineered modality**, bukan dataset distribusi logistik resmi.

## Node

```text
node = adm1_name
```

Setiap node merepresentasikan satu provinsi yang memiliki koordinat centroid pasar pada `province_market_centroids.csv`.

## Koordinat node

Centroid dihitung sebagai:

```text
lat_province = median(lat seluruh market di provinsi)
lon_province = median(lon seluruh market di provinsi)
```

Median digunakan untuk mengurangi sensitivitas terhadap satu titik pasar yang ekstrem.

## Edge construction

Untuk setiap provinsi `i`, pipeline menghitung jarak haversine ke seluruh provinsi lain dan memilih tiga yang terdekat:

```text
k = 3
edge i -> j apabila j termasuk 3 provinsi terdekat i
```

Graph bersifat directed karena `j` dapat menjadi tetangga terdekat `i`, tetapi `i` belum tentu masuk tiga tetangga terdekat `j`.

## Schema

| Kolom | Tipe | Penjelasan |
|---|---|---|
| `adm1_name` | string | source node |
| `neighbor` | string | destination/neighbor node |
| `rank` | integer | urutan kedekatan 1–3 |
| `distance_km` | float | jarak haversine antar-centroid dalam kilometer |

Jumlah edge yang diharapkan kira-kira `3 × jumlah provinsi`, selama setiap node memiliki setidaknya tiga kandidat lain.

## Haversine distance

Pipeline menggunakan radius bumi 6.371 km dan koordinat decimal degrees. Jarak ini merupakan great-circle distance, bukan jarak jalan atau waktu tempuh distribusi.

## Spatial feature pada master table

Untuk setiap row province–commodity–month, `neighbor_price` dihitung sebagai weighted mean harga komoditas yang sama pada bulan yang sama di tetangga yang tersedia:

```text
weight_ij = 1 / max(distance_km_ij, 1)
neighbor_price_i = weighted_mean(price_j)
```

Turunan:

```text
neighbor_price_ratio = neighbor_price / price
neighbor_gap         = neighbor_price / price - 1
```

Jika seluruh tetangga tidak memiliki harga pada bulan tersebut, `neighbor_price` menjadi missing.

## Potensi leakage

`neighbor_price` memakai harga bulan `t` untuk memprediksi harga bulan `t+1`. Ini aman untuk evaluasi batch apabila seluruh harga bulan `t` tersedia pada waktu inference.

Namun, untuk deployment harian atau ketika publikasi harga antarwilayah terlambat, fitur ini dapat menimbulkan availability leakage. Production system harus menyimpan timestamp publikasi dan hanya memakai harga tetangga yang telah tersedia pada waktu prediksi.

## Keterbatasan

1. Kedekatan geografis bukan bukti hubungan pasokan.
2. Graph tidak memasukkan jalan, pelabuhan, ongkos angkut, arus komoditas, atau market hierarchy.
3. Provinsi kepulauan dapat dianggap dekat secara garis lurus tetapi sulit terhubung secara logistik.
4. Konstruksi graph bersifat statis, sementara hubungan pasar dapat berubah menurut musim dan komoditas.
5. Centroid pasar dapat bergeser jika coverage sumber berubah.
6. `k=3` adalah pilihan pilot, bukan nilai optimal yang telah divalidasi.

## Validasi minimum

```text
no self-loop
rank in {1,2,3}
distance_km > 0
unique(adm1_name, neighbor)
all source and neighbor nodes exist in centroid table
```

## Peningkatan berikutnya

- bandingkan k=2, 3, 5, dan radius graph;
- gunakan road/travel-time graph;
- tambahkan pelabuhan dan konektivitas antarpulau;
- pelajari adaptive adjacency dari lead-lag harga;
- bangun commodity-specific graph;
- lakukan ablation geographic-only vs learned-only vs hybrid graph.