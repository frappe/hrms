<div align="center">
	<a href="https://frappe.io/hr">
		<img src=".github/frappe-hr-logo.png" height="80px" width="80px" alt="Frappe HR Logo">
	</a>
	<h2>Frappe HR</h2>
	<p align="center">
		<p>Perangkat Lunak HR dan Payroll Open Source yang Modern dan Mudah Digunakan</p>
	</p>

[![CI](https://github.com/frappe/hrms/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/frappe/hrms/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/frappe/hrms/branch/develop/graph/badge.svg?token=0TwvyUg3I5)](https://codecov.io/gh/frappe/hrms)

<a href="https://trendshift.io/repositories/10972" target="_blank"><img src="https://trendshift.io/api/badge/repositories/10972" alt="frappe%2Fhrms | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</div>

<div align="center">
	<img src=".github/hrms-hero.png"/>
</div>

<div align="center">
	<a href="https://frappe.io/hr">Website</a>
	-
	<a href="https://docs.frappe.io/hr/introduction">Dokumentasi</a>
</div>

## Frappe HR

Frappe HR memiliki semua yang Anda butuhkan untuk mengelola SDM perusahaan secara profesional. Ini adalah solusi HRMS lengkap dengan lebih dari 13 modul — mulai dari Manajemen Karyawan, Onboarding, Cuti, hingga Payroll, Perpajakan, dan lainnya!

## Latar Belakang
Ketika tim Frappe mulai berkembang, kami membutuhkan perangkat lunak HR dan Payroll yang open source. Kami tidak menemukan software HR yang "benar-benar" open source, sehingga kami memutuskan untuk membangunnya sendiri.

Awalnya, ini adalah kumpulan modul dalam ERPNext. Namun mulai versi 14, seiring dengan kematangan modul-modul tersebut, Frappe HR dipisahkan menjadi produk tersendiri.

## Fitur Utama

- **Siklus Hidup Karyawan**: Mulai dari onboarding karyawan, mengelola promosi dan mutasi, hingga mendokumentasikan feedback melalui exit interview — mempermudah kehidupan karyawan di setiap tahap.
- **Cuti dan Kehadiran**: Konfigurasi kebijakan cuti, tarik hari libur regional dengan satu klik, check-in dan check-out dengan pencatatan geolokasi, lacak saldo cuti dan kehadiran melalui laporan.
- **Klaim Pengajuan Biaya dan Uang Muka**: Kelola uang muka karyawan, ajukan klaim biaya, konfigurasi alur persetujuan bertingkat — semuanya terintegrasi dengan akuntansi ERPNext.
- **Manajemen Kinerja**: Lacak target, selaraskan target dengan Key Result Areas (KRA), aktifkan evaluasi diri karyawan, dan permudah pengelolaan siklus penilaian.
- **Payroll & Perpajakan**: Buat struktur gaji, konfigurasi tarif pajak penghasilan, jalankan payroll standar, tangani tambahan gaji dan pembayaran di luar siklus, lihat rincian penghasilan di slip gaji, dan masih banyak lagi.
- **Aplikasi Mobile Frappe HR**: Ajukan dan setujui cuti dari mana saja, check-in dan check-out, akses profil karyawan langsung dari aplikasi mobile.

<details open>

<summary>Lihat Screenshot</summary>
	<img src=".github/hrms-appraisal.png"/>
	<img src=".github/hrms-requisition.png"/>
	<img src=".github/hrms-attendance.png"/>
	<img src=".github/hrms-salary.png"/>
	<img src=".github/hrms-pwa.png"/>
</details>

### Teknologi yang Digunakan

- [**Frappe Framework**](https://github.com/frappe/frappe): Framework aplikasi web full-stack yang ditulis dalam Python dan JavaScript. Framework ini menyediakan fondasi yang kuat untuk membangun aplikasi web, termasuk lapisan abstraksi database, autentikasi pengguna, dan REST API.

- [**Frappe UI**](https://github.com/frappe/frappe-ui): Pustaka UI berbasis Vue untuk menyediakan antarmuka pengguna modern. Frappe UI menyediakan berbagai komponen yang dapat digunakan untuk membangun single-page application di atas Frappe Framework.

## Instalasi Produksi

### Managed Hosting

Anda dapat mencoba [Frappe Cloud](https://frappecloud.com), platform [open source](https://github.com/frappe/press) yang sederhana, ramah pengguna, dan canggih untuk meng-host aplikasi Frappe dengan tenang.

Frappe Cloud mengurus instalasi, setup, upgrade, monitoring, pemeliharaan, dan dukungan untuk deployment Frappe Anda. Ini adalah platform developer berfitur lengkap dengan kemampuan mengelola dan mengontrol beberapa deployment Frappe sekaligus.

<div>
	<a href="https://frappecloud.com/hrms/signup" target="_blank">
		<picture>
			<source media="(prefers-color-scheme: dark)" srcset="https://frappe.io/files/try-on-fc-white.png">
			<img src="https://frappe.io/files/try-on-fc-black.png" alt="Coba di Frappe Cloud" height="28" />
		</picture>
	</a>
</div>


## Setup Pengembangan
### Docker
Anda membutuhkan Docker, docker-compose, dan git yang sudah terpasang di komputer Anda. Lihat [Dokumentasi Docker](https://docs.docker.com/). Setelah itu, jalankan perintah berikut:
```
git clone https://github.com/frappe/hrms
cd hrms/docker
docker-compose up
```

Tunggu beberapa saat hingga script setup membuat site. Setelah itu, Anda dapat mengakses `http://localhost:8000` di browser dan halaman login HR akan muncul.

Gunakan kredensial berikut untuk login:

- Username: `Administrator`
- Password: `admin`

### Lokal

1. Setup bench dengan mengikuti [Langkah Instalasi](https://frappeframework.com/docs/user/en/installation) lalu jalankan server dan biarkan berjalan
	```sh
	$ bench start
	```
2. Di terminal terpisah, jalankan perintah berikut
	```sh
	$ bench new-site hrms.localhost
	$ bench get-app erpnext
	$ bench get-app hrms
	$ bench --site hrms.localhost install-app hrms
	$ bench --site hrms.localhost add-to-hosts
	```
3. Anda dapat mengakses site di `http://hrms.localhost:8080`

## Belajar dan Komunitas

1. [Frappe School](https://frappe.school) - Pelajari Frappe Framework dan ERPNext dari berbagai kursus oleh maintainer atau dari komunitas.
2. [Dokumentasi](https://docs.frappe.io/hr) - Dokumentasi lengkap untuk Frappe HR.
3. [Forum Pengguna](https://discuss.erpnext.com/) - Berdiskusi dengan komunitas pengguna dan penyedia layanan ERPNext.
4. [Grup Telegram](https://t.me/frappehr) - Dapatkan bantuan langsung dari komunitas pengguna.


## Berkontribusi

1. [Panduan Issue](https://github.com/frappe/erpnext/wiki/Issue-Guidelines)
1. [Laporkan Kerentanan Keamanan](https://erpnext.com/security)
1. [Persyaratan Pull Request](https://github.com/frappe/erpnext/wiki/Contribution-Guidelines)


## Kebijakan Logo dan Trademark

Silakan baca [Kebijakan Logo dan Trademark](TRADEMARK_POLICY.md) kami.

<br />
<br />
<div align="center" style="padding-top: 0.75rem;">
	<a href="https://frappe.io" target="_blank">
		<picture>
			<source media="(prefers-color-scheme: dark)" srcset="https://frappe.io/files/Frappe-white.png">
			<img src="https://frappe.io/files/Frappe-black.png" alt="Frappe Technologies" height="28"/>
		</picture>
	</a>
</div>
