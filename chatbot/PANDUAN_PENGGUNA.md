# 📖 Panduan Pengguna
# Regulasi Internasional Meteorologi — AI Chatbot

**Versi:** 1.0.0  
**Bahasa:** Indonesia  
**Platform:** Web (Streamlit)

---

## Daftar Isi

1. [Pengenalan](#1-pengenalan)
2. [Cara Mengakses Chatbot](#2-cara-mengakses-chatbot)
3. [Mengenal Tampilan Antarmuka](#3-mengenal-tampilan-antarmuka)
4. [Cara Menggunakan Chatbot](#4-cara-menggunakan-chatbot)
5. [Fitur Sidebar](#5-fitur-sidebar)
6. [Contoh Pertanyaan yang Efektif](#6-contoh-pertanyaan-yang-efektif)
7. [Memahami Jawaban dan Sumber](#7-memahami-jawaban-dan-sumber)
8. [Pertanyaan Lanjutan (Follow-up)](#8-pertanyaan-lanjutan-follow-up)
9. [Batasan Chatbot](#9-batasan-chatbot)
10. [Tips dan Trik](#10-tips-dan-trik)
11. [Panduan Admin: Membangun Index](#11-panduan-admin-membangun-index)
12. [Panduan Admin: Deploy ke Streamlit Cloud](#12-panduan-admin-deploy-ke-streamlit-cloud)
13. [Pertanyaan yang Sering Diajukan (FAQ)](#13-pertanyaan-yang-sering-diajukan-faq)
14. [Pemecahan Masalah](#14-pemecahan-masalah)

---

## 1. Pengenalan

### Apa itu Regulasi Meteorologi AI Chatbot?

Chatbot ini adalah asisten belajar cerdas yang dirancang khusus untuk membantu
mahasiswa memahami materi **Regulasi Internasional Meteorologi**. Chatbot
menggunakan teknologi **Retrieval-Augmented Generation (RAG)** — artinya
setiap jawaban yang diberikan diambil langsung dari materi kuliah yang telah
diunggah, bukan dari pengetahuan umum internet.

### Apa yang bisa dilakukan chatbot ini?

| Kemampuan | Keterangan |
|-----------|------------|
| ✅ Menjawab pertanyaan materi | Berdasarkan slide kuliah yang tersedia |
| ✅ Menyebutkan sumber | Setiap jawaban dilengkapi nomor Materi dan Slide |
| ✅ Mengingat konteks percakapan | Mendukung pertanyaan lanjutan |
| ✅ Merangkum topik | Merangkum isi beberapa slide sekaligus |
| ✅ Menjelaskan konsep | Menjelaskan istilah atau prosedur teknis |
| ❌ Menjawab di luar materi | Tidak bisa — hanya dari slide yang tersedia |
| ❌ Mengakses internet | Tidak terhubung ke internet saat menjawab |

### Teknologi yang digunakan

- **LLM:** Google Gemini 2.5 Flash-Lite
- **Pencarian:** FAISS Vector Database
- **Framework:** LangChain + Streamlit
- **Bahasa jawaban:** Indonesia

---

## 2. Cara Mengakses Chatbot

### Akses via Streamlit Community Cloud (Online)

1. Buka browser (Chrome, Firefox, Edge, Safari)
2. Kunjungi URL aplikasi yang diberikan oleh instruktur, contoh:
   ```
   https://regulasi-meteorologi.streamlit.app
   ```
3. Tunggu hingga halaman sepenuhnya termuat (biasanya 10–30 detik pada
   akses pertama karena proses cold start)
4. Chatbot siap digunakan — tidak perlu login atau instalasi apapun

### Akses via Jaringan Lokal (Jika dijalankan secara lokal)

1. Pastikan Anda sudah menjalankan perintah `streamlit run app.py` di terminal
2. Buka browser dan kunjungi:
   ```
   http://localhost:8501
   ```
3. Jika mengakses dari perangkat lain dalam jaringan yang sama:
   ```
   http://<IP-komputer-server>:8501
   ```

---

## 3. Mengenal Tampilan Antarmuka

```
┌─────────────────────────────────────────────────────────────┐
│  SIDEBAR (kiri)          │  AREA CHAT UTAMA (kanan)          │
│  ─────────────────────   │  ─────────────────────────────    │
│  🌤️ Nama Aplikasi        │  🌤️ Judul Aplikasi               │
│  v1.0.0                  │  Deskripsi singkat                │
│                          │                                   │
│  📊 Statistik Dokumen    │  ┌─────────────────────────────┐  │
│  [ 6 ] [ 120 ] [ 480 ]   │  │  Riwayat percakapan         │  │
│  File   Slide   Chunk    │  │                             │  │
│                          │  │  👤 Pertanyaan pengguna     │  │
│  🔧 Kelola Index         │  │                             │  │
│  [ ⚡ Bangun Index ]     │  │  🌤️ Jawaban chatbot         │  │
│                          │  │     📚 Sumber: Materi X     │  │
│  💡 Contoh Pertanyaan    │  │                             │  │
│  • Apa itu WMO?          │  └─────────────────────────────┘  │
│  • Jelaskan ICAO...      │                                   │
│  • ...                   │  [ Ketik pertanyaan Anda... ] 📤  │
│                          │                                   │
│  [ 🗑️ Hapus Chat ]       │                                   │
│                          │                                   │
│  ℹ️ Info Deployment      │                                   │
└─────────────────────────────────────────────────────────────┘
```

### Keterangan Elemen Utama

| Elemen | Fungsi |
|--------|--------|
| **Sidebar kiri** | Statistik, kelola index, contoh pertanyaan |
| **Area chat** | Riwayat percakapan dan jawaban AI |
| **Kotak input bawah** | Tempat mengetik pertanyaan |
| **Tombol kirim (↵)** | Mengirim pertanyaan |
| **Statistik (File/Slide/Chunk)** | Menunjukkan berapa banyak materi yang dimuat |
| **Badge ✔ hijau** | Index siap — chatbot bisa menjawab |
| **Badge ✘ merah** | Index belum dibuat — perlu dibangun dulu |

---

## 4. Cara Menggunakan Chatbot

### Langkah-langkah Dasar

**Langkah 1 — Periksa status index**

Sebelum bertanya, pastikan badge di sidebar menunjukkan:
> ✔ Index siap digunakan

Jika badge merah (✘), hubungi admin atau klik **Bangun Index** jika Anda
adalah admin.

---

**Langkah 2 — Ketik pertanyaan**

Klik kotak input di bagian bawah layar, lalu ketik pertanyaan Anda
dalam bahasa Indonesia:

```
Apa itu regulasi internasional meteorologi?
```

Tekan **Enter** atau klik tombol **➤** untuk mengirim.

---

**Langkah 3 — Tunggu jawaban streaming**

Chatbot akan menampilkan:
1. Indikator "mengetik" (tiga titik bergerak) selama memproses
2. Jawaban muncul kata per kata secara real-time
3. Sumber kutipan muncul di bawah jawaban setelah selesai

---

**Langkah 4 — Baca jawaban dan sumber**

Setiap jawaban diakhiri dengan blok sumber seperti:

```
📚 Sumber:
• Materi 09 — Slide 3 — Pengantar Regulasi
  `Regulasi Internasional Met 09_M8C_250526.pptx`
• Materi 10 — Slide 7 — Lembaga Internasional
  `Regulasi Internasional Met 10_M8C_080626.pptx`
```

Ini memberitahu Anda persis dari materi dan slide mana jawaban berasal.

---

**Langkah 5 — Lanjutkan percakapan (opsional)**

Anda bisa langsung bertanya lanjutan tanpa menyebutkan konteks ulang:

```
Jelaskan lebih detail tentang poin pertama.
```

Chatbot akan mengingat konteks pertanyaan sebelumnya.

---

## 5. Fitur Sidebar

### 📊 Statistik Dokumen

Menampilkan ringkasan materi yang telah dimuat ke dalam sistem:

| Kartu | Keterangan |
|-------|------------|
| **File PPT** | Jumlah file PowerPoint yang diproses |
| **Total Slide** | Jumlah slide dari semua file |
| **Chunk** | Jumlah potongan teks yang diindeks untuk pencarian |

Klik **📄 Daftar File** untuk melihat nama file yang tersedia.

---

### 🔧 Kelola Index

Tombol ini hanya relevan untuk **admin/instruktur**:

| Tombol | Fungsi |
|--------|--------|
| **⚡ Bangun Index** | Membangun index pertama kali dari file PPTX |
| **🔄 Rebuild Index** | Membangun ulang setelah file PPTX diperbarui |
| **🗑️ Hapus Index** | Menghapus index (chatbot tidak bisa menjawab sampai dibangun ulang) |

Proses pembangunan index menampilkan progress bar 4 langkah dan
memakan waktu beberapa menit tergantung jumlah slide.

---

### 💡 Contoh Pertanyaan

Klik salah satu tombol contoh untuk langsung mengirim pertanyaan tersebut
ke chatbot — berguna untuk memulai eksplorasi materi tanpa harus mengetik.

---

### 🗑️ Hapus Riwayat Chat

Mengosongkan semua percakapan di sesi saat ini. Gunakan ini jika ingin
memulai topik baru yang tidak berhubungan dengan pertanyaan sebelumnya.

> Catatan: Riwayat chat tidak tersimpan secara permanen — otomatis terhapus
> saat Anda menutup atau me-refresh halaman browser.

---

### ℹ️ Info Deployment

Ringkasan cara menjalankan aplikasi secara lokal maupun di Streamlit Cloud.
Berguna sebagai referensi cepat untuk admin.

---

## 6. Contoh Pertanyaan yang Efektif

### ✅ Pertanyaan yang Baik

Pertanyaan yang spesifik dan relevan dengan materi menghasilkan jawaban
paling akurat:

```
Apa itu WMO dan apa fungsinya dalam regulasi meteorologi internasional?
```
```
Jelaskan prosedur penerbitan SIGMET berdasarkan regulasi ICAO.
```
```
Apa perbedaan antara METAR dan TAF dalam layanan informasi cuaca penerbangan?
```
```
Bagaimana peran VAAC dalam sistem peringatan abu vulkanik untuk penerbangan?
```
```
Sebutkan dan jelaskan isi ICAO Annex 3 tentang meteorologi penerbangan.
```
```
Apa yang dimaksud dengan GCOS dan apa tujuan pembentukannya?
```
```
Jelaskan tentang sistem peringatan dini bencana hidrometeorologi menurut materi.
```

---

### ⚠️ Pertanyaan yang Kurang Efektif

| Pertanyaan Kurang Efektif | Masalah | Perbaikan |
|---------------------------|---------|-----------|
| "Ceritakan tentang cuaca" | Terlalu umum | "Jelaskan jenis layanan informasi cuaca untuk penerbangan" |
| "Apa itu meteorologi?" | Bisa ada di luar materi | "Bagaimana definisi meteorologi menurut materi kuliah ini?" |
| "Ringkas semua materi" | Terlalu luas | "Ringkas materi tentang regulasi ICAO" |
| "ya", "ok", "lanjut" | Terlalu singkat tanpa konteks | Tulis pertanyaan lengkap |

---

### 🔑 Formula Pertanyaan yang Baik

```
[Kata tanya] + [Subjek spesifik] + [Konteks/tujuan]

Contoh:
"Bagaimana" + "prosedur SIGMET" + "diterbitkan menurut regulasi ICAO?"
"Apa" + "perbedaan METAR dan TAF" + "dalam konteks layanan penerbangan?"
"Jelaskan" + "peran WMO" + "dalam koordinasi regulasi meteorologi global"
```

---

## 7. Memahami Jawaban dan Sumber

### Struktur Jawaban

Setiap jawaban chatbot mengikuti struktur ini:

```
┌──────────────────────────────────────────────────────┐
│  RINGKASAN SINGKAT                                    │
│  Penjelasan singkat 1–2 kalimat inti jawaban          │
│                                                       │
│  PENJELASAN DETAIL                                    │
│  Uraian lebih lengkap dengan poin-poin dari materi    │
│  • Poin 1                                             │
│  • Poin 2                                             │
│    ◦ Sub-poin                                         │
│                                                       │
│  ─────────────────────────────────────────────────   │
│  📚 Sumber:                                           │
│  • Materi 09 — Slide 3 — *Judul Slide*                │
│    `nama_file.pptx`                                   │
└──────────────────────────────────────────────────────┘
```

### Membaca Blok Sumber

```
📚 Sumber:
• Materi 09 — Slide 3 — *Pengantar Regulasi Meteorologi*
  `Regulasi Internasional Met 09_M8C_250526.pptx`
```

| Bagian | Keterangan |
|--------|------------|
| `Materi 09` | Nomor materi/pertemuan |
| `Slide 3` | Nomor slide dalam file tersebut |
| `Pengantar...` | Judul slide (jika tersedia) |
| `nama_file.pptx` | Nama file PowerPoint sumbernya |

Gunakan informasi ini untuk **menemukan slide asli** di file PPTX
yang diberikan instruktur jika ingin membaca materi secara langsung.

### Jika Chatbot Tidak Menemukan Jawaban

Chatbot akan menjawab:

> *"Maaf, informasi tersebut tidak ditemukan pada materi yang tersedia."*

Ini berarti topik yang Anda tanyakan **tidak ada dalam slide** yang
telah diunggah. Coba:
- Ubah kata kunci pertanyaan
- Tanyakan topik yang lebih dekat dengan judul slide yang ada
- Periksa apakah file PPTX yang relevan sudah diindeks (lihat Daftar File di sidebar)

---

## 8. Pertanyaan Lanjutan (Follow-up)

Chatbot mengingat hingga **10 pertukaran terakhir** dalam satu sesi.
Artinya Anda bisa bertanya lanjutan tanpa mengulang konteks.

### Contoh Sesi Percakapan

**Pertanyaan pertama:**
```
Apa itu ICAO Annex 3?
```

**Jawaban chatbot:** *(penjelasan lengkap tentang ICAO Annex 3)*

---

**Pertanyaan lanjutan — bisa singkat:**
```
Apa saja isi utamanya?
```
*(Chatbot tahu "isi utamanya" merujuk ke ICAO Annex 3)*

---

**Pertanyaan lanjutan berikutnya:**
```
Bagaimana implementasinya di Indonesia?
```
*(Chatbot mencari konteks implementasi ICAO Annex 3 di materi)*

---

### Kata Kunci Follow-up yang Didukung

Chatbot otomatis mengenali dan memproses frasa lanjutan seperti:

| Frasa | Artinya |
|-------|---------|
| "jelaskan lebih lanjut" | Minta penjelasan lebih detail |
| "berikan contohnya" | Minta contoh konkret |
| "apa bedanya dengan..." | Minta perbandingan |
| "mengapa hal itu terjadi?" | Minta penjelasan kausal |
| "lanjutkan" / "teruskan" | Melanjutkan penjelasan sebelumnya |
| "ringkas kembali" | Minta rangkuman ulang |

### Kapan Harus Menghapus Riwayat Chat

Hapus riwayat (tombol **🗑️ Hapus Riwayat Chat** di sidebar) ketika:
- Anda ingin beralih ke topik yang **sama sekali berbeda**
- Chatbot tampak "bingung" karena konteks yang terlalu panjang
- Anda ingin memulai sesi belajar baru yang bersih

---

## 9. Batasan Chatbot

Penting untuk memahami apa yang **tidak bisa** dilakukan chatbot ini:

| Batasan | Penjelasan |
|---------|------------|
| 🚫 Di luar materi | Tidak bisa menjawab topik yang tidak ada di slide |
| 🚫 Berita terkini | Tidak terhubung internet, tidak tahu perkembangan terbaru |
| 🚫 Soal hitungan | Tidak dirancang untuk menyelesaikan soal matematika/fisika |
| 🚫 Gambar/grafik | Tidak bisa menganalisis gambar dari slide |
| 🚫 Audio/video | Hanya memproses teks dari slide |
| 🚫 Menyimpan histori | Riwayat hilang saat browser di-refresh |
| 🚫 Multi-bahasa | Dioptimalkan untuk bahasa Indonesia |

### Mengapa chatbot tidak menjawab dari pengetahuan umum?

Ini adalah **fitur keamanan**, bukan kekurangan. Dengan membatasi jawaban
hanya pada materi kuliah, chatbot:
- Mencegah informasi yang tidak akurat atau tidak relevan
- Memastikan jawaban sesuai dengan kurikulum yang diajarkan
- Mendorong mahasiswa fokus pada materi yang diberikan instruktur

---

## 10. Tips dan Trik

### 💡 Tips untuk Hasil Terbaik

**1. Gunakan istilah teknis dari materi**
```
❌ "Jelaskan tentang aturan cuaca pesawat"
✅ "Jelaskan regulasi meteorologi penerbangan berdasarkan ICAO Annex 3"
```

**2. Sebutkan nomor materi jika tahu**
```
"Pada Materi 10, apa yang dibahas tentang WMO?"
"Jelaskan konsep yang ada di Materi 11 tentang layanan maritim"
```

**3. Minta format tertentu**
```
"Jelaskan dalam bentuk poin-poin"
"Buat tabel perbandingan antara METAR dan TAF"
"Ringkas dalam 3 kalimat"
```

**4. Bertanya bertahap untuk topik kompleks**
```
Langkah 1: "Apa itu SIGMET?"
Langkah 2: "Kapan SIGMET diterbitkan?"
Langkah 3: "Siapa yang berwenang menerbitkan SIGMET di Indonesia?"
```

**5. Manfaatkan tombol Contoh Pertanyaan**
Klik tombol contoh di sidebar untuk inspirasi topik yang bisa ditanyakan.

### ⚡ Pintasan Keyboard

| Tombol | Fungsi |
|--------|--------|
| `Enter` | Kirim pertanyaan |
| `Shift + Enter` | Baris baru dalam pertanyaan |
| `Ctrl + A` | Pilih semua teks di kotak input |

---

## 11. Panduan Admin: Membangun Index

> Bagian ini untuk instruktur atau admin yang mengelola aplikasi.

### Kapan index perlu dibangun/diperbarui?

- Pertama kali setelah instalasi
- Setiap kali ada penambahan atau perubahan file PPTX
- Jika jawaban chatbot tidak relevan dengan materi terbaru

### Cara Membangun Index via UI Streamlit

1. Buka aplikasi di browser
2. Di sidebar, klik **⚡ Bangun Index** (atau **🔄 Rebuild Index**)
3. Amati progress bar 4 langkah:
   - 📂 Step 1: Membaca file PowerPoint
   - ✂️ Step 2: Membuat chunk semantik
   - 🧠 Step 3: Membuat embedding (paling lama)
   - 💾 Step 4: Menyimpan index ke disk
4. Tunggu hingga muncul: **✅ Index berhasil dibuat!**
5. Statistik di sidebar akan diperbarui otomatis

### Cara Membangun Index via Command Line (lebih cepat)

```powershell
# Aktifkan virtual environment
.venv\Scripts\Activate.ps1

# Build index (skip jika sudah ada)
python build_index.py

# Force rebuild (timpa index yang ada)
python build_index.py --force
```

### Estimasi Waktu Pembangunan Index

| Jumlah Slide | Estimasi Waktu |
|-------------|----------------|
| < 50 slide | 1–2 menit |
| 50–150 slide | 3–7 menit |
| 150–300 slide | 8–15 menit |
| > 300 slide | 15–30 menit |

*Waktu bervariasi tergantung kecepatan koneksi internet (untuk API embedding)*

### Menambah File PPTX Baru

**Lokal:**
1. Salin file `.pptx` baru ke folder `data/`
2. Jalankan `python build_index.py --force`

**Streamlit Cloud:**
1. Salin file `.pptx` ke folder `data/` di repo lokal
2. Jalankan `python build_index.py --force`
3. Commit dan push semua perubahan:
   ```powershell
   git add data/ faiss/
   git commit -m "Update: tambah materi baru"
   git push
   ```
4. Streamlit Cloud akan redeploy otomatis dalam ~1 menit

---

## 12. Panduan Admin: Deploy ke Streamlit Cloud

> Langkah lengkap dari nol hingga aplikasi online dan terhubung GitHub.

### Prasyarat

- [ ] Akun GitHub (gratis): [github.com](https://github.com)
- [ ] Akun Streamlit Community Cloud (gratis): [share.streamlit.io](https://share.streamlit.io)
- [ ] Git terinstal di komputer
- [ ] Python 3.11+ terinstal
- [ ] API Key Gemini tersedia

---

### Langkah 1 — Persiapan Repository GitHub

**1a. Inisialisasi Git di folder project**
```powershell
git init
git add .
git commit -m "Initial commit: Regulasi Meteorologi Chatbot"
```

**1b. Buat repository baru di GitHub**
1. Kunjungi [github.com/new](https://github.com/new)
2. Isi nama repository, contoh: `regulasi-meteorologi-chatbot`
3. Pilih **Private** (agar file PPTX tidak publik)
4. Klik **Create repository** — jangan centang opsi initialize

**1c. Hubungkan dan push ke GitHub**
```powershell
git remote add origin https://github.com/USERNAME/regulasi-meteorologi-chatbot.git
git branch -M main
git push -u origin main
```

---

### Langkah 2 — Siapkan File PPTX di Repo

```powershell
# Salin file PPTX ke folder data/
Copy-Item "d:\Regulasi Internasional Meteorologi\UAS\*.pptx" "data\"

# Build index secara lokal
python build_index.py

# Commit PPTX + index
git add data/ faiss/
git commit -m "Add learning materials and FAISS index"
git push
```

---

### Langkah 3 — Deploy di Streamlit Community Cloud

1. Buka [share.streamlit.io](https://share.streamlit.io)
2. Login dengan akun GitHub
3. Klik **New app**
4. Isi form deployment:
   ```
   Repository  : USERNAME/regulasi-meteorologi-chatbot
   Branch      : main
   Main file   : app.py
   ```
5. Klik **Deploy!**
6. Tunggu proses build selesai (2–5 menit pertama kali)

---

### Langkah 4 — Tambahkan Secrets di Streamlit Cloud

1. Di dashboard Streamlit Cloud, temukan aplikasi Anda
2. Klik **⋮ (tiga titik)** → **Settings** → **Secrets**
3. Paste konfigurasi berikut:

```toml
GEMINI_API_KEY            = "AQ.Ab8RN6KFQMk-qr8o_e1vH7IBznSFyc_cvo9wVDZkYc6jZt0_WA"
GEMINI_MODEL              = "gemini-2.5-flash-lite-preview-06-17"
GEMINI_TEMPERATURE        = "0.2"
GEMINI_MAX_OUTPUT_TOKENS  = "2048"
EMBEDDING_MODEL           = "models/text-embedding-004"
RETRIEVER_TOP_K           = "5"
RETRIEVER_SCORE_THRESHOLD = "0.75"
CHUNK_SIZE                = "400"
CHUNK_OVERLAP             = "80"
LOG_LEVEL                 = "INFO"
```

4. Klik **Save** — aplikasi restart otomatis

---

### Langkah 5 — Update Konten (CD Workflow)

Setiap kali ada perubahan, cukup push ke GitHub:

```powershell
# Contoh: update file PPTX dan rebuild index
python build_index.py --force
git add data/ faiss/
git commit -m "Update: tambah Materi 15"
git push
# → Streamlit Cloud redeploy otomatis dalam ~60 detik
```

---

## 13. Pertanyaan yang Sering Diajukan (FAQ)

**Q: Apakah chatbot ini membutuhkan koneksi internet?**  
A: Ya, untuk memanggil API Gemini saat menjawab. Namun, pencarian
dokumen (FAISS) berjalan secara lokal/server tanpa internet.

---

**Q: Apakah riwayat chat saya tersimpan?**  
A: Tidak. Riwayat chat hanya ada selama sesi browser aktif. Saat Anda
menutup tab atau me-refresh halaman, riwayat terhapus otomatis.

---

**Q: Kenapa jawaban kadang tidak lengkap?**  
A: Kemungkinan topik tersebut tersebar di beberapa slide dan chatbot
hanya mengambil potongan yang paling relevan. Coba pertanyaan lebih
spesifik, atau tanyakan per aspek secara terpisah.

---

**Q: Apakah chatbot bisa mengerjakan soal ujian?**  
A: Chatbot bisa membantu memahami konsep dari materi, tetapi tidak
dirancang untuk "mengerjakan soal" secara langsung. Gunakan sebagai
alat belajar, bukan pengganti belajar mandiri.

---

**Q: Kenapa index perlu dibangun ulang setelah update PPTX?**  
A: Index adalah basis data vektor yang dihasilkan dari teks PPTX.
Setiap kali konten PPTX berubah, index harus diperbarui agar chatbot
membaca versi terbaru.

---

**Q: Berapa banyak pertanyaan yang bisa saya ajukan?**  
A: Tidak ada batas jumlah pertanyaan per sesi. Namun, API Gemini
memiliki batas kuota harian. Jika muncul error rate limit, tunggu
beberapa menit lalu coba lagi.

---

**Q: Apakah chatbot bisa diakses di HP/tablet?**  
A: Ya. Tampilan Streamlit responsif dan dapat digunakan di perangkat
mobile melalui browser. Pengalaman terbaik di layar ≥ 768px.

---

**Q: Bagaimana cara melaporkan jawaban yang salah?**  
A: Catat pertanyaan Anda, jawaban yang diterima, dan slide sumber yang
disebutkan. Hubungi instruktur atau admin dengan informasi tersebut untuk
perbaikan materi atau konfigurasi retriever.

---

## 14. Pemecahan Masalah

### Untuk Pengguna

| Masalah | Kemungkinan Penyebab | Solusi |
|---------|----------------------|--------|
| Halaman tidak termuat | Koneksi internet / server down | Refresh halaman, tunggu 30 detik |
| Kotak input tidak aktif (abu-abu) | Index belum dibuat | Hubungi admin untuk build index |
| Jawaban: "tidak ditemukan dalam materi" | Topik tidak ada di slide | Ubah kata kunci pertanyaan |
| Jawaban terpotong di tengah | Batas token tercapai | Tanyakan per bagian yang lebih kecil |
| Indikator "mengetik" lama sekali | API lambat / rate limit | Tunggu 10–30 detik, atau coba lagi |
| Tampilan berantakan | Browser lama | Gunakan Chrome/Firefox/Edge terbaru |
| Jawaban bahasa Inggris | Pertanyaan dalam bahasa Inggris | Tanyakan dalam bahasa Indonesia |

---

### Untuk Admin

| Error | Penyebab | Solusi |
|-------|----------|--------|
| `GEMINI_API_KEY not set` | Secret belum dikonfigurasi | Tambahkan di Streamlit Secrets atau `.env` |
| `FAISS index not found` | Index belum dibangun | Jalankan `python build_index.py` |
| `No .pptx files found` | Folder `data/` kosong atau path salah | Periksa `DATA_DIR` dan isi folder `data/` |
| `API quota exceeded` | Limit harian tercapai | Tunggu reset kuota (biasanya 24 jam) |
| `Module not found` | Dependency belum terinstal | Jalankan `pip install -r requirements.txt` |
| Index terlalu besar untuk GitHub | File melebihi 100MB | Gunakan [Git LFS](https://git-lfs.com/) |
| `Permission denied` pada `faiss/` | Hak akses folder | Jalankan terminal sebagai administrator |

---

### Melihat Log Aplikasi

**Lokal:**
```powershell
Get-Content logs\chatbot.log -Tail 50
```

**Streamlit Cloud:**
1. Buka dashboard Streamlit Cloud
2. Klik nama aplikasi
3. Klik **Manage app** (pojok kanan bawah)
4. Pilih tab **Logs**

---

### Kontak Dukungan

Jika masalah tidak dapat diselesaikan dengan panduan di atas:

- 📧 Hubungi instruktur mata kuliah
- 🐛 Laporkan bug via GitHub Issues di repository aplikasi
- 📋 Sertakan: deskripsi masalah, pesan error (jika ada), dan langkah yang sudah dicoba

---

## Ringkasan Cepat

```
MULAI CEPAT (Pengguna):
1. Buka URL aplikasi
2. Pastikan badge sidebar: ✔ Index siap digunakan
3. Ketik pertanyaan → tekan Enter
4. Baca jawaban + sumber yang dikutip

MULAI CEPAT (Admin - Lokal):
1. pip install -r requirements.txt
2. Isi .env (salin dari .env.example)
3. python build_index.py
4. streamlit run app.py

MULAI CEPAT (Admin - Cloud):
1. Push repo ke GitHub (termasuk data/ dan faiss/)
2. Hubungkan ke Streamlit Community Cloud
3. Tambahkan GEMINI_API_KEY di Secrets
4. Deploy → selesai!
```

---

*Panduan Pengguna — Regulasi Internasional Meteorologi AI Chatbot v1.0.0*  
*Dokumen ini dapat diperbarui sesuai perkembangan fitur aplikasi.*
