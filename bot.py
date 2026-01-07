from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ================= CONFIG =================
TOKEN = "8599799129:AAGVh_c_z-N9O50R3fMjgP9K4bWXoa_EQFk"
SHEET_NAME = "Keuangan Keluarga"

# Telegram ID kamu & istri
ALLOWED_USERS = [1009390463, 2031339484]
# =========================================

# ===== GOOGLE SHEETS =====
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "service_account.json", scope
)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1
# ========================


def user_allowed(update: Update):
    return update.effective_user.id in ALLOWED_USERS


# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_allowed(update):
        return

    await update.message.reply_text(
        "💰 Bot Keuangan Keluarga Aktif\n\n"
        "Perintah:\n"
        "/masuk jumlah kategori\n"
        "/keluar jumlah kategori\n"
        "/saldo\n"
        "/laporan (bulan ini)\n"
        "/laporan 2026-01"
    )


async def masuk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_allowed(update):
        return

    try:
        jumlah = int(context.args[0])
        kategori = context.args[1]

        sheet.append_row([
            datetime.now().strftime("%Y-%m-%d"),
            update.effective_user.first_name,
            "Masuk",
            jumlah,
            kategori
        ])

        await update.message.reply_text("✅ Pemasukan dicatat")

    except:
        await update.message.reply_text("❗ Format: /masuk 50000 gaji")


async def keluar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_allowed(update):
        return

    try:
        jumlah = int(context.args[0])
        kategori = context.args[1]

        sheet.append_row([
            datetime.now().strftime("%Y-%m-%d"),
            update.effective_user.first_name,
            "Keluar",
            jumlah,
            kategori
        ])

        await update.message.reply_text("❌ Pengeluaran dicatat")

    except:
        await update.message.reply_text("❗ Format: /keluar 20000 makan")


async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_allowed(update):
        return

    data = sheet.get_all_records()

    total_masuk = 0
    total_keluar = 0

    for r in data:
        if r.get("Jenis") == "Masuk":
            total_masuk += r.get("Jumlah", 0)
        elif r.get("Jenis") == "Keluar":
            total_keluar += r.get("Jumlah", 0)

    saldo = total_masuk - total_keluar

    await update.message.reply_text(f"💰 Saldo saat ini: {saldo}")


async def laporan_bulan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_allowed(update):
        return

    data = sheet.get_all_records()

    # Default: bulan ini
    bulan = datetime.now().strftime("%Y-%m")

    # Jika user ketik: /laporan 2026-01
    if context.args:
        bulan = context.args[0]

    data_bulan = [
        r for r in data
        if str(r.get("Tanggal", "")).startswith(bulan)
    ]

    if not data_bulan:
        await update.message.reply_text("📭 Tidak ada data di bulan tersebut.")
        return

    total_masuk = sum(
        r.get("Jumlah", 0) for r in data_bulan if r.get("Jenis") == "Masuk"
    )
    total_keluar = sum(
        r.get("Jumlah", 0) for r in data_bulan if r.get("Jenis") == "Keluar"
    )
    saldo = total_masuk - total_keluar

    filename = f"laporan_{bulan}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"Laporan Keuangan Bulan {bulan}")

    y -= 40
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Total Pemasukan   : {total_masuk}")
    y -= 20
    c.drawString(50, y, f"Total Pengeluaran : {total_keluar}")
    y -= 20
    c.drawString(50, y, f"Saldo             : {saldo}")

    y -= 40
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Tanggal")
    c.drawString(130, y, "User")
    c.drawString(220, y, "Jenis")
    c.drawString(300, y, "Jumlah")
    c.drawString(380, y, "Kategori")

    y -= 15
    c.setFont("Helvetica", 10)

    for r in data_bulan:
        if y < 50:
            c.showPage()
            y = height - 50

        c.drawString(50, y, str(r.get("Tanggal", "")))
        c.drawString(130, y, str(r.get("User", "")))
        c.drawString(220, y, str(r.get("Jenis", "")))
        c.drawString(300, y, str(r.get("Jumlah", "")))
        c.drawString(380, y, str(r.get("Kategori", "")))
        y -= 15

    c.save()

    await update.message.reply_document(open(filename, "rb"))
    os.remove(filename)


# ===== BOT INIT =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("masuk", masuk))
app.add_handler(CommandHandler("keluar", keluar))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("laporan", laporan_bulan))

print("🤖 Bot keuangan berjalan...")
app.run_polling()
