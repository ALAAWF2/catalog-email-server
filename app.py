from flask import Flask, request
from openpyxl import Workbook
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

app = Flask(__name__)

SENDER_EMAIL = "wafaiealaa@orangebedbath.com"
SENDER_PASS = "hgvz vubs ireq umza"
RECIPIENT_EMAIL = "alaa.wafae@orangebedbath.com"

@app.route("/")
def home():
    return "✅ Flask Email API is live."

@app.route("/submit-order", methods=["POST"])
def submit_order():
    data = request.json
    mall = data["mall"]
    orders = data["orders"]

    # حفظ الطلبية كـ Excel
    date = datetime.now().strftime("%Y-%m-%d")
    filename = f"طلبية {mall} - {date}.xlsx"
    folder = "orders"
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    wb = Workbook()
    ws = wb.active
    ws.title = "طلبية"
    ws.append(["اسم المعرض:", mall])
    ws.append([])
    ws.append(["الكود", "الاسم", "الكمية المطلوبة"])
    for item in orders:
        ws.append([item["code"], item["name"], item["qty"]])
    wb.save(filepath)

    # إرسال الإيميل
    try:
        msg = EmailMessage()
        msg["Subject"] = f"طلبية جديدة من معرض {mall}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECIPIENT_EMAIL
        msg.set_content(f"تم استلام طلبية جديدة من {mall}.\n\nمرفق ملف الطلبية بصيغة Excel.")


        with open(filepath, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(filepath)
            msg.add_attachment(file_data, maintype="application", subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=file_name)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASS)
            smtp.send_message(msg)

        return {"status": "success", "message": f"📩 تم إرسال الطلبية إلى {RECIPIENT_EMAIL}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    app.run(debug=True)
