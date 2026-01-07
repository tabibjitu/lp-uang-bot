from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import json
import base64

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ================= CONFIG =================
TOKEN = os.environ["BOT_TOKEN"]
SHEET_NAME = "Keuangan Keluarga"
ALLOWED_USERS = [1009390463, 2031339484]
# =========================================

# ===== GOOGLE SHEETS AUTH (BASE64) =====
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_json = base64.b64decode(
    os.environ["GOOGLE_CREDS_B64"]
).decode("utf-8")

creds_dict = json.loads(creds_json)

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict, scope
)

client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1
# =========================================


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

    total_masuk = sum(r["Jumlah"] for r in data if r["Jenis"] == "Masuk")
    total_keluar = sum(r["Jumlah"] for r in data if r["Jenis"] == "Keluar")

    saldo = total_masuk - total_keluar
    await update.message.reply_text(f"💰 Saldo saat ini: {saldo}")


async def laporan_bulan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_allowed(update):
        return

    data = sheet.get_all_records()
    bulan = context.args[0] if context.args else datetime.now().strftime("%Y-%m")

    data_bulan = [r for r in data if r["Tanggal"].startswith(bulan)]

    if not data_bulan:
        await update.message.reply_text("📭 Tidak ada data di bulan tersebut.")
        return

    total_masuk = sum(r["Jumlah"] for r in data_bulan if r["Jenis"] == "Masuk")
    total_keluar = sum(r["Jumlah"] for r in data_bulan if r["Jenis"] == "Keluar")
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
    c.drawString(50, y-20, f"Total Pengeluaran : {total_keluar}")
    c.drawString(50, y-40, f"Saldo             : {saldo}")

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
