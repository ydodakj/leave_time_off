# YDOD Leave & Holiday Integrations

Kumpulan modul Odoo 19 untuk integrasi Leave Management dengan Discord dan data hari libur nasional Indonesia.

---

## Modul yang tersedia

| Modul | Deskripsi |
|---|---|
| `ydod_leave_discord` | Notifikasi Discord saat karyawan mengajukan, menyetujui, menolak cuti |
| `ydod_indonesian_public_holiday` | Import hari libur nasional Indonesia dari API ke kalender kerja Odoo |

---

## 1. `ydod_leave_discord` — Leave Discord Integration

### Fitur
- Kirim embed Discord saat leave **diajukan (submit)**, **disetujui (approve)**, **ditolak (refuse)**, atau **direset ke draft**
- Support **multiple webhook** — kirim ke beberapa channel sekaligus
- Filter per **jenis cuti** atau **global** (semua jenis cuti)
- **Mention karyawan** via Discord User ID di profil karyawan
- Tombol **Test Webhook** untuk cek koneksi langsung dari form
- Avatar dan username bot dapat dikustomisasi

### Screenshot embed Discord

```
┌─────────────────────────────────────────────────┐
│  Leave Request Submitted — Budi Santoso         │
├─────────────┬──────────────┬────────────────────┤
│ Employee    │ Leave Type   │ Duration           │
│ Budi Santoso│ Annual Leave │ 3 day(s)           │
├─────────────┴──────────────┴────────────────────┤
│ From: 2025-07-14    To: 2025-07-16              │
│ Manager: Siti Rahayu                            │
└─────────────────────────────────────────────────┘
  Odoo HR • YDOD Leave Discord Integration
```

### Cara Instalasi

1. Copy folder `ydod_leave_discord` ke addons path Odoo
2. Update Apps list di Odoo
3. Install module **YDOD Leave Discord Integration**

### Konfigurasi

1. Buka **Time Off → Configuration → Discord Integration → Webhook Configurations**
2. Buat konfigurasi baru:
   - **Webhook URL**: URL webhook dari Discord (Settings → Integrations → Webhooks)
   - **Global**: centang agar berlaku untuk semua jenis cuti, atau pilih jenis cuti spesifik
   - **Trigger**: pilih event yang ingin dikirim notifikasinya
3. Klik **Test Webhook** untuk memastikan koneksi berhasil
4. Aktifkan konfigurasi

### Cara Mendapatkan Discord Webhook URL

1. Buka Discord server → channel tujuan
2. Edit Channel → Integrations → Webhooks → New Webhook
3. Copy Webhook URL
4. Paste ke field **Webhook URL** di konfigurasi

### Mention Karyawan (Opsional)

1. Buka profil karyawan → tab **Private Information**
2. Isi field **Discord User ID** dengan ID numerik Discord karyawan
   (cara cek: Discord Settings → Advanced → Developer Mode aktif → klik kanan user → Copy User ID)
3. Aktifkan **Mention Employee** di konfigurasi webhook

### Dependensi
- `hr_holidays` (built-in Odoo)
- Library Python `requests` (sudah tersedia di Odoo standard)

---

## 2. `ydod_indonesian_public_holiday` — Indonesian Public Holiday

### Fitur
- Import hari libur nasional Indonesia ke **Work Schedule** (resource.calendar.leaves)
- Import ke **Global Time Off** (tanpa kalender spesifik)
- Pilih tahun yang ingin diimport
- Pilih work schedule tertentu atau semua schedule sekaligus
- **Skip duplikat** — tidak membuat entry ganda
- **Preview / Dry Run** sebelum import betulan
- **Fallback offline** jika API tidak tersedia (data 2025 & 2026 built-in)

### Sumber Data API

| Prioritas | API | URL |
|---|---|---|
| 1 (Primary) | API Hari Libur Indonesia | `https://api-hari-libur.vercel.app/api?year=YYYY` |
| 2 (Fallback) | Day Off API | `https://dayoffapi.vercel.app/api` |
| 3 (Offline) | Data built-in | Tersedia untuk 2025 & 2026 |

### Cara Instalasi

1. Copy folder `ydod_indonesian_public_holiday` ke addons path Odoo
2. Update Apps list di Odoo
3. Install module **YDOD Indonesian Public Holiday**

### Cara Penggunaan

1. Buka **Time Off → Configuration → Indonesian Public Holidays → Import Holidays**
2. Isi wizard:
   - **Year**: tahun yang ingin diimport (default: tahun ini)
   - **Work Schedules**: pilih kalender kerja, atau kosongkan untuk semua
   - **Create Global Time Off**: centang untuk buat entry global
   - **Skip Existing Entries**: centang agar tidak duplikat
   - **Preview Only**: centang untuk lihat data tanpa import
3. Klik **Preview Holidays** untuk melihat daftar hari libur
4. Klik **Import Holidays** untuk melakukan import

### Data Offline yang Tersedia

| Tahun | Jumlah Hari Libur | Keterangan |
|---|---|---|
| 2025 | 26 | Termasuk cuti bersama |
| 2026 | 14 | Estimasi berdasarkan kalender Islam |

### Dependensi
- `hr_holidays` (built-in Odoo)
- `resource` (built-in Odoo)
- Library Python `requests` (sudah tersedia di Odoo standard)

---

## Kompatibilitas

| Versi Odoo | Status |
|---|---|
| 19.0 | ✓ Didukung |
| 18.0 | Gunakan modul lain (lihat catatan) |

> Untuk Odoo 18, tersedia modul serupa di Odoo Apps:
> https://apps.odoo.com/apps/modules/18.0/get_indonesian_public_holiday_data

---

## Struktur Folder

```
intergrasi_leave_to_discord/
├── README.md                              ← Dokumentasi ini
├── ydod_leave_discord/                    ← Modul Discord Leave Integration
│   ├── __manifest__.py
│   ├── __init__.py
│   ├── models/
│   │   ├── discord_config.py              ← Model config webhook & logic send
│   │   └── hr_leave.py                    ← Override hr.leave & hr.employee
│   ├── views/
│   │   ├── discord_config_views.xml
│   │   ├── hr_leave_views.xml
│   │   └── menu_views.xml
│   ├── data/
│   │   └── discord_config_data.xml        ← Default config (inactive)
│   └── security/
│       └── ir.model.access.csv
└── ydod_indonesian_public_holiday/        ← Modul Indonesian Public Holiday
    ├── __manifest__.py
    ├── __init__.py
    ├── models/
    │   └── holiday_provider.py            ← Fetcher API + offline fallback
    ├── wizard/
    │   ├── import_holiday_wizard.py       ← Wizard import
    │   └── import_holiday_wizard_views.xml
    ├── views/
    │   └── menu_views.xml
    └── security/
        └── ir.model.access.csv
```

---

## Lisensi

LGPL-3 — bebas digunakan dan dimodifikasi dengan menyertakan kredit.

## Author

**YDoD** — https://github.com/dodyakj
