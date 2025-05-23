import streamlit as st 
import pandas as pd
from datetime import datetime
from io import BytesIO
from database import (
    init_db, get_dataframes,
    simpan_penjualan, simpan_pembelian, reset_data
)
import plotly.express as px
from streamlit_option_menu import option_menu

# ========== KONFIGURASI HALAMAN ==========
st.set_page_config(
    page_title="Keuangan Selada Pak Joko",
    page_icon="🥬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========== FUNGSI EXCEL MULTI-SHEET ==========
def to_excel_multi(data_dict: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in data_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()

# ========== INISIALISASI & LOAD DATA ==========
init_db()
def load_data():
    raw_penj, raw_pemb, *_ = get_dataframes()
    raw_penj['tanggal'] = pd.to_datetime(raw_penj['tanggal'])
    raw_pemb['tanggal'] = pd.to_datetime(raw_pemb['tanggal'])
    return raw_penj, raw_pemb

raw_penj, raw_pemb = load_data()

# ========== SIDEBAR MENU DENGAN IKON & STYLING ==========
with st.sidebar:
    st.image("bg.png", width=120)
    st.markdown("# ☰ Menu Akuntansi")
    menu = option_menu(
        menu_title=None,
        options=["Dashboard", "Input Penjualan", "Input Pembelian", "Jurnal Umum", "Laba Rugi", "Neraca", "Reset Data"],
        icons=["house", "cart-check", "cash-stack", "journal-text", "bar-chart-line", "file-earmark-spreadsheet", "trash"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#6FB98F"},
            "icon": {"color": "#004445", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#B3C100"},
            "nav-link-selected": {"background-color": "#B3C100", "color": "white"},
        }
    )

# ========== FUNGSI DASHBOARD ==========
def show_dashboard(penj: pd.DataFrame, pemb: pd.DataFrame):
    # Welcome message without HTML
    st.subheader("Selamat Datang di Dashboard Keuangan Selada Pak Joko!")
    st.write("---")

    st.markdown("#### Ringkasan KPI Bulanan")
    bulan_ini = datetime.today().strftime("%Y-%m")

    # Hitung data
    df_pn = (
        penj.groupby(penj['tanggal'].dt.strftime('%Y-%m'))
            .agg(total_penjualan=('total','sum'))
            .reset_index().rename(columns={'tanggal':'bulan'})
    )
    df_pb = (
        pemb.groupby(pemb['tanggal'].dt.strftime('%Y-%m'))
            .agg(jumlah_pembelian=('jumlah','sum'))
            .reset_index().rename(columns={'tanggal':'bulan'})
    )
    df = (
        pd.merge(df_pn, df_pb, on='bulan', how='outer')
          .fillna(0)
          .assign(laba=lambda x: x.total_penjualan - x.jumlah_pembelian)
    )

    pend = int(df.loc[df['bulan']==bulan_ini, 'total_penjualan'].sum())
    beb  = int(df.loc[df['bulan']==bulan_ini, 'jumlah_pembelian'].sum())

    # Tampilkan KPI dengan kolom dan emoji
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Pendapatan", f"Rp {pend:,.0f}")
    c2.metric("📉 Total Beban",     f"Rp {beb:,.0f}")
    c3.metric("💹 Laba Bersih",     f"Rp {pend-beb:,.0f}")

    # Tampilkan tren di dalam expander
    with st.expander("📈 Lihat Tren Keuangan Bulanan"):
        fig = px.line(
            df,
            x='bulan',
            y=['total_penjualan','jumlah_pembelian','laba'],
            labels={'value':'Jumlah (Rp)','variable':'Kategori','bulan':'Bulan'}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Sedikit animasi perayaan jika profit positif
    if pend - beb > 0:
        st.balloons()

# ========== ROUTING MENU ==========
if menu == "Dashboard":
    show_dashboard(raw_penj, raw_pemb)

elif menu == "Input Penjualan":
    st.header("Input Penjualan Selada")
    tgl = st.date_input("Tanggal", datetime.today())
    kg  = st.number_input("Jumlah (kg)", 0.0, step=0.1)
    if st.button("💾 Simpan Penjualan"):
        simpan_penjualan(tgl.strftime("%Y-%m-%d"), kg, kg * 32000)
        st.success("✅ Penjualan disimpan!")
        raw_penj, raw_pemb = load_data()

elif menu == "Input Pembelian":
    st.header("Input Pembelian/Beban")
    tgl = st.date_input("Tanggal", datetime.today(), key="pemb")
    ket = st.selectbox("Kategori Beban", ["Air","Listrik","Bibit","Plastik","Lainnya"])
    biaya = st.number_input("Jumlah (Rp)", 0, step=1_000, format="%d")
    st.markdown(f"**Nominal:** Rp {biaya:,.0f}")
    if st.button("💾 Simpan Pembelian"):
        simpan_pembelian(tgl.strftime("%Y-%m-%d"), ket.lower(), biaya)
        st.success(f"✅ Pembelian {ket} disimpan: Rp {biaya:,.0f}")
        raw_penj, raw_pemb = load_data()

elif menu == "Jurnal Umum":
    st.header("Jurnal Umum")
    df_j = pd.concat([
        raw_penj.assign(keterangan='Penjualan', debit=0, kredit=raw_penj['total']),
        raw_pemb.assign(keterangan='Pembelian', debit=raw_pemb['jumlah'], kredit=0)
    ], ignore_index=True).sort_values('tanggal')
    df_j['Tanggal']    = df_j['tanggal'].dt.strftime('%Y-%m-%d')
    df_j['Keterangan'] = df_j['keterangan']
    df_j['Debit (Rp)'] = df_j['debit']
    df_j['Kredit (Rp)']= df_j['kredit']
    df_j = df_j[['Tanggal','Keterangan','Debit (Rp)','Kredit (Rp)']]

    st.dataframe(
        df_j.style.format({
            "Debit (Rp)":  "{:,.0f}",
            "Kredit (Rp)": "{:,.0f}"
        }), use_container_width=True
    )

    sales = raw_penj['total'].sum()
    costs = raw_pemb['jumlah'].sum()
    df_lr = pd.DataFrame({
        'Kategori': ['Pendapatan','Beban','Laba Bersih'],
        'Total (Rp)': [sales, costs, sales - costs]
    })
    kas = sales - costs
    df_nr = pd.DataFrame({
        'Aset': ['Kas'],
        'Nilai (Rp)': [kas],
        'Ekuitas': ['Laba Ditahan'],
        'Nilai Ekuitas (Rp)': [kas]
    })

    st.download_button(
        "⬇️ Download Semua Laporan (Excel)",
        data=to_excel_multi({
            "Jurnal Umum": df_j,
            "Laba Rugi":   df_lr,
            "Neraca":      df_nr
        }),
        file_name="laporan_selada_pak_joko.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

elif menu == "Laba Rugi":
    st.header("Laporan Laba Rugi")
    sales = raw_penj['total'].sum()
    costs = raw_pemb['jumlah'].sum()
    df_lr = pd.DataFrame({
        'Kategori': ['Pendapatan','Beban','Laba Bersih'],
        'Total (Rp)': [sales, costs, sales - costs]
    })
    st.dataframe(df_lr.style.format({"Total (Rp)": "{:,.0f}"}), use_container_width=True)
    st.download_button(
        "⬇️ Download Laporan Laba Rugi (Excel)",
        data=to_excel_multi({"Laba Rugi": df_lr}),
        file_name="laporan_laba_rugi.xlsx",
        mime="application/vnd.openxmlformats-officedocument-spreadsheetml.sheet"
    )

elif menu == "Neraca":
    st.header("Neraca")
    kas = raw_penj['total'].sum() - raw_pemb['jumlah'].sum()
    df_nr = pd.DataFrame({
        'Aset': ['Kas'],
        'Nilai (Rp)': [kas],
        'Ekuitas': ['Laba Ditahan'],
        'Nilai Ekuitas (Rp)': [kas]
    })
    st.dataframe(
        df_nr.style.format({
            "Nilai (Rp)": "{:,.0f}",
            "Nilai Ekuitas (Rp)": "{:,.0f}"
        }), use_container_width=True
    )
    st.download_button(
        "⬇️ Download Neraca (Excel)",
        data=to_excel_multi({"Neraca": df_nr}),
        file_name="neraca.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

elif menu == "Reset Data":
    st.header("⚠️ Reset Data")
    if st.button("Hapus Semua Transaksi"):
        reset_data()
        st.success("✅ Data berhasil di-reset!")
        raw_penj, raw_pemb = load_data()