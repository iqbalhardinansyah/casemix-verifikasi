import streamlit as st
import pandas as pd
import plotly.express as px
import json

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard | E-Klaim Verif",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.title("E-Klaim Verif")
    menu = st.radio("Navigasi", [
        "Dashboard",
        "Upload File",
        "Eklaim Data",
        "Rules",
        "Hasil Verifikasi"
    ])

# Session State untuk data & rules
if "data" not in st.session_state:
    st.session_state["data"] = None
if "rules" not in st.session_state:
    st.session_state["rules"] = []
if "hasil_verifikasi" not in st.session_state:
    st.session_state["hasil_verifikasi"] = None


# ================== MENU UPLOAD ==================
if menu == "Upload File":
    st.header("📂 Upload File Klaim")
    uploaded_file = st.file_uploader("Pilih file TXT/CSV", type=["txt", "csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, sep="\t", dtype=str, low_memory=False)
            df = df.fillna("")
            st.session_state["data"] = df
            st.success(f"File `{uploaded_file.name}` berhasil diupload dan dibaca!")
        except Exception as e:
            st.error(f"Format file tidak didukung! Error: {e}")


# ================== MENU EKLAIM DATA ==================
elif menu == "Eklaim Data":
    st.header("📊 Data Eklaim")
    if st.session_state["data"] is not None:
        df = st.session_state["data"].copy()

        # Tambahan kolom parsing INACBG
        if "INACBG" in df.columns:
            df["CMG"] = df["INACBG"].str.split("-").str[0]
            df["CASETYPE"] = df["INACBG"].str.split("-").str[1]
            df["CBG"] = df["INACBG"].str.split("-").str[2]
            df["SL"] = df["INACBG"].str.split("-").str[3]

        # Tambahan kolom selisih
        if "TOTAL_TARIF" in df.columns and "TARIF_RS" in df.columns:
            df["TOTAL_TARIF"] = pd.to_numeric(df["TOTAL_TARIF"], errors="coerce").fillna(0)
            df["TARIF_RS"] = pd.to_numeric(df["TARIF_RS"], errors="coerce").fillna(0)
            df["Selisih"] = df["TOTAL_TARIF"] - df["TARIF_RS"]

        def highlight_minus(val):
            if isinstance(val, (int, float)) and val < 0:
                return "color: red;"
            return ""

        st.dataframe(df.style.applymap(highlight_minus, subset=["Selisih"]))
    else:
        st.warning("Silakan upload file terlebih dahulu di menu Upload File.")


# ================== MENU RULES ==================
elif menu == "Rules":
    st.header("⚖️ Rules")

    with st.form("form_rule"):
        nama_rule = st.text_input("Nama Rule")
        kolom_pilihan = None
        if st.session_state["data"] is not None:
            kolom_pilihan = st.selectbox("Pilih Kolom", st.session_state["data"].columns)
        isi_rule = st.text_input("Isi Rule (contoh: Z09.8;I10)")
        pesan = st.text_input("Pesan")
        submitted = st.form_submit_button("Simpan Rule")

        if submitted and nama_rule and kolom_pilihan and isi_rule and pesan:
            st.session_state["rules"].append({
                "nama": nama_rule,
                "kolom": kolom_pilihan,
                "isi": isi_rule,
                "pesan": pesan
            })
            st.success(f"Rule '{nama_rule}' berhasil disimpan!")

    if st.session_state["rules"]:
        st.subheader("📋 Daftar Rules")
        for i, rule in enumerate(st.session_state["rules"]):
            st.write(f"**{i+1}. {rule['nama']}** ({rule['kolom']} contains '{rule['isi']}') → Pesan: {rule['pesan']}")
            if st.button(f"Hapus Rule {i+1}", key=f"hapus_{i}"):
                st.session_state["rules"].pop(i)
                st.success("Rule berhasil dihapus!")
                st.experimental_rerun()


# ================== MENU HASIL VERIFIKASI ==================
elif menu == "Hasil Verifikasi":
    st.header("✅ Hasil Verifikasi")
    if st.session_state["data"] is not None and st.session_state["rules"]:
        df = st.session_state["data"].copy()
        df["Note"] = ""

        # Jalankan rules
        for rule in st.session_state["rules"]:
            mask = df[rule["kolom"]].astype(str).str.contains(rule["isi"], na=False)
            df.loc[mask, "Note"] = rule["pesan"]

        hasil_verifikasi = df[df["Note"] != ""]
        st.session_state["hasil_verifikasi"] = hasil_verifikasi

        if not hasil_verifikasi.empty:
            st.dataframe(hasil_verifikasi[["Note"] + [col for col in hasil_verifikasi.columns if col != "Note"]])
        else:
            st.info("Tidak ada data yang sesuai dengan rules.")
    else:
        st.warning("Belum ada data atau rules yang ditambahkan.")


# ================== MENU DASHBOARD ==================
elif menu == "Dashboard":
    st.header("📊 Dashboard - Analysis")

    if st.session_state["data"] is not None:
        df = st.session_state["data"].copy()

        # Pastikan numerik
        df["TOTAL_TARIF"] = pd.to_numeric(df.get("TOTAL_TARIF", 0), errors="coerce").fillna(0)
        df["TARIF_RS"] = pd.to_numeric(df.get("TARIF_RS", 0), errors="coerce").fillna(0)

        total_klaim = len(df)
        total_tarif = df["TOTAL_TARIF"].sum()
        total_tarif_rs = df["TARIF_RS"].sum()
        selisih_tarif = total_tarif - total_tarif_rs
        total_ranap = len(df[df["PTD"] == "1"]) if "PTD" in df.columns else 0
        total_rajal = len(df[df["PTD"] == "2"]) if "PTD" in df.columns else 0
        total_pending = len(st.session_state["hasil_verifikasi"]) if st.session_state["hasil_verifikasi"] is not None else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Klaim", total_klaim)
        col2.metric("Total Tarif", f"Rp {total_tarif:,.0f}")
        col3.metric("Total Tarif RS", f"Rp {total_tarif_rs:,.0f}")
        col4.markdown("⚖️ **Selisih Tarif**")
        if selisih_tarif < 0:
            col4.markdown(f"<span style='color:red;'>Rp {selisih_tarif:,.0f}</span>", unsafe_allow_html=True)
        else:
            col4.markdown(f"Rp {selisih_tarif:,.0f}")

        col5, col6, col7 = st.columns(3)
        col5.metric("Total Ranap", total_ranap)
        col6.metric("Total Rajal", total_rajal)
        col7.metric("Total Pending (Hasil Verifikasi)", total_pending)

        # ===== Grafik Diagnosa =====
        if "DIAGLIST" in df.columns:
            diag_series = df["DIAGLIST"].dropna().astype(str).str.split(";")
            diag_exploded = diag_series.explode().str.strip()
            diag_counts = diag_exploded.value_counts().nlargest(20).sort_values(ascending=True)

            fig = px.bar(
                diag_counts,
                x=diag_counts.values,
                y=diag_counts.index,
                orientation="h",
                text=diag_counts.values,
                title="📊 20 Diagnosa Terbanyak"
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(height=700, xaxis_title="Jumlah", yaxis_title="Diagnosa", font=dict(size=14))
            st.plotly_chart(fig, use_container_width=True)

        # ===== Grafik Tindakan =====
        if "PROCLIST" in df.columns:
            proc_series = df["PROCLIST"].dropna().astype(str).str.split(";")
            proc_exploded = proc_series.explode().str.strip()
            proc_counts = proc_exploded.value_counts().nlargest(20).sort_values(ascending=True)

            fig2 = px.bar(
                proc_counts,
                x=proc_counts.values,
                y=proc_counts.index,
                orientation="h",
                text=proc_counts.values,
                title="📊 20 Tindakan Terbanyak"
            )
            fig2.update_traces(textposition="outside")
            fig2.update_layout(height=700, xaxis_title="Jumlah", yaxis_title="Tindakan", font=dict(size=14))
            st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("Silakan upload file terlebih dahulu di menu Upload File.")

# Footer
st.markdown("---")
st.caption("© 2025 - Iqbal Hardinansyah, AMd.Kes")
