import sqlite3
import pandas as pd
from typing import Tuple
from contextlib import contextmanager

# ===== KONEKSI DATABASE =====
DB_PATH = 'selada_keuangan.db'

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

# ===== INISIALISASI =====
def init_db():
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS penjualan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanggal TEXT,
                kg REAL,
                total REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pembelian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanggal TEXT,
                kategori TEXT,
                jumlah REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jurnal_umum (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanggal TEXT,
                keterangan TEXT,
                debit REAL,
                kredit REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laba_rugi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                periode TEXT,
                pendapatan REAL,
                beban REAL,
                laba REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS neraca (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                periode TEXT,
                aset REAL,
                kewajiban REAL,
                ekuitas REAL
            )
        ''')
        conn.commit()

# ===== CRUD & AMBIL DATA =====
def get_dataframes() -> Tuple[
    pd.DataFrame,  # penjualan
    pd.DataFrame,  # pembelian
    pd.DataFrame,  # jurnal_umum
    pd.DataFrame,  # laba_rugi
    pd.DataFrame   # neraca
]:
    with get_conn() as conn:
        df_penjualan = pd.read_sql_query("SELECT * FROM penjualan", conn)
        df_pembelian = pd.read_sql_query("SELECT * FROM pembelian", conn)
        df_jurnal    = pd.read_sql_query("SELECT * FROM jurnal_umum", conn)
        df_lr        = pd.read_sql_query("SELECT * FROM laba_rugi", conn)
        df_nr        = pd.read_sql_query("SELECT * FROM neraca", conn)
    return df_penjualan, df_pembelian, df_jurnal, df_lr, df_nr



def simpan_penjualan(tanggal: str, kg: float, total: float) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO penjualan (tanggal, kg, total) VALUES (?, ?, ?)" ,
            (tanggal, kg, total)
        )
        conn.commit()


def simpan_pembelian(tanggal: str, kategori: str, jumlah: float) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO pembelian (tanggal, kategori, jumlah) VALUES (?, ?, ?)",
            (tanggal, kategori, jumlah)
        )
        conn.commit()


def reset_data() -> None:
    with get_conn() as conn:
        # Hapus semua baris dari setiap tabel
        conn.execute("DELETE FROM penjualan")
        conn.execute("DELETE FROM pembelian")
        conn.execute("DELETE FROM jurnal_umum")
        conn.execute("DELETE FROM laba_rugi")
        conn.execute("DELETE FROM neraca")
        conn.commit()
