import re 
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB_NAME = "prediksi_diabetes.db"

# Warna label hasil sesuai tingkat risiko
WARNA_RISIKO = {
    "Rendah": "#2e7d32",         # hijau
    "Waspada": "#f9a825",        # kuning
    "Sedang": "#ef6c00",         # oranye
    "Tinggi": "#d32f2f",         # merah
    "Sangat Tinggi": "#7b1fa2",  # ungu
}


#DATABASE
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pasien (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_pasien TEXT NOT NULL,
                usia INTEGER NOT NULL,
                gula_darah REAL NOT NULL,
                bmi REAL NOT NULL,
                riwayat_ortu TEXT NOT NULL,
                hasil_prediksi TEXT NOT NULL
            )
            """
        )


def simpan_pasien(nama, usia, gula, bmi, riwayat, hasil):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO pasien (nama_pasien, usia, gula_darah, bmi, riwayat_ortu, hasil_prediksi) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (nama, usia, gula, bmi, riwayat, hasil),
        )


def ambil_semua_pasien():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute(
            "SELECT id, nama_pasien, usia, gula_darah, bmi, riwayat_ortu, hasil_prediksi "
            "FROM pasien ORDER BY id DESC"
        ).fetchall()


def hapus_pasien(id_pasien):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM pasien WHERE id = ?", (id_pasien,))


#LOGIKA PREDIKSI
def prediksi_risiko(gula, bmi, riwayat):
    """
    Aturan:
    - Gula >= 200           : Tinggi / Sangat Tinggi
        (Sangat Tinggi bila BMI >= 30 atau ada riwayat orang tua)
    - Gula 140 - 199        : Sedang / Tinggi
        (Tinggi bila BMI >= 30 atau ada riwayat orang tua)
    - Gula < 140, BMI >= 30 : Waspada / Sedang
        (Sedang bila ada riwayat orang tua)
    - Gula < 140, BMI < 30, ada riwayat   : Waspada
    - Gula < 140, BMI < 30, tidak riwayat : Rendah
    """
    ada_riwayat = riwayat == "Ya"
    obesitas = bmi >= 30

    if gula >= 200:
        return "Sangat Tinggi" if (obesitas or ada_riwayat) else "Tinggi"
    if gula >= 140:
        return "Tinggi" if (obesitas or ada_riwayat) else "Sedang"
    # gula < 140
    if obesitas:
        return "Sedang" if ada_riwayat else "Waspada"
    return "Waspada" if ada_riwayat else "Rendah"


#APLIKASI
class AplikasiDiabetes(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Prediksi Risiko Diabetes")
        self.geometry("460x470")
        self.resizable(False, False)

        self.var_nama = tk.StringVar()
        self.var_usia = tk.StringVar()
        self.var_gula = tk.StringVar()
        self.var_bmi = tk.StringVar()
        self.var_riwayat = tk.StringVar()

        self.buat_widget()

    def buat_widget(self):
        ttk.Label(
            self, text="Prediksi Risiko Diabetes", font=("Segoe UI", 16, "bold")
        ).pack(pady=(15, 10))

        form = ttk.Frame(self, padding=10)
        form.pack(fill="x", padx=20)

        baris = [
            ("Nama Pasien", self.var_nama),
            ("Usia (tahun)", self.var_usia),
            ("Gula Darah (mg/dL)", self.var_gula),
            ("BMI", self.var_bmi),
        ]
        for i, (teks, var) in enumerate(baris):
            ttk.Label(form, text=teks).grid(row=i, column=0, sticky="w", pady=6)
            ttk.Entry(form, textvariable=var, width=28).grid(row=i, column=1, pady=6, padx=10)

        ttk.Label(form, text="Riwayat Diabetes Ortu").grid(row=4, column=0, sticky="w", pady=6)
        self.cb_riwayat = ttk.Combobox(
            form, textvariable=self.var_riwayat, values=["Ya", "Tidak"],
            state="readonly", width=25,
        )
        self.cb_riwayat.grid(row=4, column=1, pady=6, padx=10)
        self.cb_riwayat.set("Pilih...")

        tombol = ttk.Frame(self)
        tombol.pack(pady=10)
        ttk.Button(tombol, text="Prediksi & Simpan", command=self.proses_prediksi).grid(row=0, column=0, padx=5)
        ttk.Button(tombol, text="Lihat Data", command=self.lihat_data).grid(row=0, column=1, padx=5)
        ttk.Button(tombol, text="Reset", command=self.reset_form).grid(row=0, column=2, padx=5)

        ttk.Label(self, text="Hasil Prediksi:", font=("Segoe UI", 10)).pack(pady=(10, 2))
        self.lbl_hasil = tk.Label(
            self, text="-", font=("Segoe UI", 18, "bold"),
            width=22, height=2, bg="#e0e0e0", fg="black", relief="groove",
        )
        self.lbl_hasil.pack(pady=5)

    #Validasi
    def validasi_input(self):
        nama = self.var_nama.get().strip()
        if not nama:
            return self.error("Nama pasien tidak boleh kosong.")
        if not re.fullmatch(r"[A-Za-z\s.'\-]{2,100}", nama):
            return self.error("Nama pasien hanya boleh berisi huruf (2-100 karakter).")

        try:
            usia = int(self.var_usia.get().strip())
        except ValueError:
            return self.error("Usia harus berupa bilangan bulat.")
        if not 1 <= usia <= 120:
            return self.error("Usia harus antara 1 - 120 tahun.")

        try:
            gula = float(self.var_gula.get().strip().replace(",", "."))
        except ValueError:
            return self.error("Gula darah harus berupa angka.")
        if not 20 <= gula <= 600:
            return self.error("Gula darah harus antara 20 - 600 mg/dL.")

        try:
            bmi = float(self.var_bmi.get().strip().replace(",", "."))
        except ValueError:
            return self.error("BMI harus berupa angka.")
        if not 10 <= bmi <= 70:
            return self.error("BMI harus antara 10 - 70.")

        riwayat = self.var_riwayat.get()
        if riwayat not in ("Ya", "Tidak"):
            return self.error("Pilih riwayat diabetes orang tua (Ya/Tidak).")

        return nama, usia, gula, bmi, riwayat

    def error(self, pesan):
        messagebox.showwarning("Input Tidak Valid", pesan)
        return None

    #Aksi
    def proses_prediksi(self):
        data = self.validasi_input()
        if data is None:
            return
        nama, usia, gula, bmi, riwayat = data

        hasil = prediksi_risiko(gula, bmi, riwayat)
        simpan_pasien(nama, usia, gula, bmi, riwayat, hasil)

        warna = WARNA_RISIKO[hasil]
        fg = "black" if hasil == "Waspada" else "white"
        self.lbl_hasil.config(text=f"Risiko {hasil}", bg=warna, fg=fg)
        messagebox.showinfo("Berhasil", f"Data {nama} tersimpan.\nHasil: Risiko {hasil}")

    def reset_form(self):
        for v in (self.var_nama, self.var_usia, self.var_gula, self.var_bmi):
            v.set("")
        self.cb_riwayat.set("Pilih...")
        self.lbl_hasil.config(text="-", bg="#e0e0e0", fg="black")

    def lihat_data(self):
        win = tk.Toplevel(self)
        win.title("Riwayat Data Pasien")
        win.geometry("760x400")

        kolom = ("id", "nama", "usia", "gula", "bmi", "riwayat", "hasil")
        judul = ("ID", "Nama Pasien", "Usia", "Gula Darah", "BMI", "Riwayat Ortu", "Hasil Prediksi")
        lebar = (40, 190, 60, 90, 70, 100, 120)

        frame = ttk.Frame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tree = ttk.Treeview(frame, columns=kolom, show="headings")
        for k, j, w in zip(kolom, judul, lebar):
            tree.heading(k, text=j)
            tree.column(k, width=w, anchor="center" if k != "nama" else "w")
        for nama_risiko, warna in WARNA_RISIKO.items():
            tree.tag_configure(nama_risiko, foreground=warna)

        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def muat():
            tree.delete(*tree.get_children())
            for row in ambil_semua_pasien():
                tree.insert("", "end", values=row, tags=(row[6],))

        def hapus():
            terpilih = tree.selection()
            if not terpilih:
                messagebox.showinfo("Info", "Pilih data yang ingin dihapus.", parent=win)
                return
            if messagebox.askyesno("Konfirmasi", "Hapus data terpilih?", parent=win):
                for item in terpilih:
                    hapus_pasien(tree.item(item)["values"][0])
                muat()

        ttk.Button(win, text="Hapus Data Terpilih", command=hapus).pack(pady=(0, 10))
        muat()


if __name__ == "__main__":
    init_db()
    AplikasiDiabetes().mainloop()