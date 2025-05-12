
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Batch Generative Feedback", layout="wide")

st.title("🧠 Batch Generative Feedback Assistant")
st.markdown("Upload file KPI dan dapatkan umpan balik otomatis untuk seluruh pekerja berdasarkan skor dan kategori talent.")

# Upload file
uploaded_file = st.file_uploader("📤 Upload file KPI (CSV/XLSX)", type=["csv", "xlsx"])

if not uploaded_file:
    st.stop()

# Load file
if uploaded_file.name.endswith(".csv"):
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_excel(uploaded_file)

# Pastikan kolom minimum ada
required_cols = ['NIPP PEKERJA', 'POSISI PEKERJA', 'PERUSAHAAN', 'BOBOT',
                 'REALISASI TW TERKAIT', 'TARGET TW TERKAIT', 'POLARITAS']
if not all(col in df.columns for col in required_cols):
    st.error("❌ Kolom wajib tidak ditemukan di file. Pastikan file sesuai dengan struktur kpi_cleaned.csv.")
    st.stop()

# Preprocessing
df['REALISASI TW TERKAIT'] = pd.to_numeric(df['REALISASI TW TERKAIT'], errors='coerce')
df['TARGET TW TERKAIT'] = pd.to_numeric(df['TARGET TW TERKAIT'], errors='coerce')
df['BOBOT'] = pd.to_numeric(df['BOBOT'], errors='coerce')
df['POLARITAS'] = df['POLARITAS'].str.strip().str.lower()

def calculate_capaian(row):
    realisasi = row['REALISASI TW TERKAIT']
    target = row['TARGET TW TERKAIT']
    polaritas = row['POLARITAS']
    if pd.isna(realisasi) or pd.isna(target) or target == 0 or realisasi == 0:
        return None
    if polaritas == 'positif':
        return (realisasi / target) * 100
    elif polaritas == 'negatif':
        return (target / realisasi) * 100
    else:
        return None

df['CAPAIAN (%)'] = df.apply(calculate_capaian, axis=1)
df['SKOR KPI'] = df['CAPAIAN (%)'] * df['BOBOT'] / 100

# Hitung skor akhir per pekerja
summary = df.groupby(['NIPP PEKERJA', 'POSISI PEKERJA', 'PERUSAHAAN'], as_index=False).agg(
    TOTAL_SKOR=('SKOR KPI', 'sum'),
    TOTAL_BOBOT=('BOBOT', 'sum')
)
summary = summary[summary['TOTAL_BOBOT'] != 0]
summary['SKOR AKHIR'] = (summary['TOTAL_SKOR'] / summary['TOTAL_BOBOT']) * 100

def classify_performance(score):
    if score > 110:
        return "Istimewa"
    elif score > 105:
        return "Sangat Baik"
    elif score >= 90:
        return "Baik"
    elif score >= 80:
        return "Cukup"
    else:
        return "Kurang"

summary['KATEGORI TALENT'] = summary['SKOR AKHIR'].apply(classify_performance)

# Simulasi feedback berdasarkan kategori
feedback_templates = {
    "Istimewa": "Kinerja Anda luar biasa dan menunjukkan dedikasi tinggi terhadap target strategis perusahaan. Kami menyarankan Anda untuk mengambil peran kepemimpinan yang lebih besar dalam proyek lintas unit.",
    "Sangat Baik": "Anda telah menunjukkan performa yang sangat baik sepanjang periode ini. Pertahankan momentum ini dan eksplorasi peluang pengembangan diri untuk posisi berikutnya.",
    "Baik": "Pencapaian Anda berada dalam kategori baik. Dengan sedikit peningkatan pada kompetensi spesifik dan perilaku kerja, Anda dapat mencapai level yang lebih tinggi.",
    "Cukup": "Ada potensi besar dalam kinerja Anda. Kami menyarankan untuk mengikuti pelatihan atau coaching guna meningkatkan hasil kerja ke depan.",
    "Kurang": "Kami mendorong Anda untuk mengevaluasi kembali prioritas dan metode kerja Anda. Silakan berdiskusi dengan atasan untuk menyusun action plan ke depan."
}

summary['UMPAN BALIK'] = summary['KATEGORI TALENT'].map(feedback_templates)

st.subheader("📄 Hasil Umpan Balik Per Pekerja")
st.dataframe(summary[['NIPP PEKERJA', 'POSISI PEKERJA', 'PERUSAHAAN', 'SKOR AKHIR', 'KATEGORI TALENT', 'UMPAN BALIK']])

# Download button
st.download_button("📥 Download Hasil Umpan Balik (CSV)", data=summary.to_csv(index=False), file_name="feedback_pekerja.csv", mime="text/csv")
