import streamlit as st

# Judul aplikasi
st.title("🔍 Website Verifikasi Casemix")

# Upload file txt
uploaded_file = st.file_uploader("Upload file hasil Casemix (.txt)", type="txt")

# Aturan penggantian/verifikasi
rules = {
    "JKN": "BPJS",
    "T83.1": "Infeksi Alat Urologi",
    "N13.1": "Obstruksi Ureter dengan Hidronefrosis"
    # Tambahkan aturan lain di sini
}

if uploaded_file:
    # Baca isi file
    text = uploaded_file.read().decode("utf-8")

    # Simpan versi asli
    st.subheader("Isi Asli")
    st.text_area("Teks asli dari file", text, height=200)

    # Proses verifikasi (replace sesuai aturan)
    verified_text = text
    for old, new in rules.items():
        verified_text = verified_text.replace(old, new)

    # Tampilkan hasil
    st.subheader("Hasil Verifikasi")
    st.text_area("Teks setelah verifikasi", verified_text, height=200)

    # Tombol download
    st.download_button(
        label="💾 Download Hasil",
        data=verified_text,
        file_name="hasil_verifikasi.txt",
        mime="text/plain"
    )
