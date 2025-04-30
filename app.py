from flask import Flask, request
from flask_cors import CORS
from openpyxl import Workbook
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
CORS(app, origins=["https://alaawf2.github.io"])

SENDER_EMAIL = "orangebed.order@gmail.com"
SENDER_PASS = "qnop rqzl zuhy aceg"

mall_to_email = {
    "Warehouse": "alaa.wafae@orangebedbath.com",
    "warehouse riyadh": "alaa.wafae@orangebedbath.com"
}

mallMap = {
    "Warehouse": [
        "04-Andalos Mall", "05-Haifa Mall", "06-Red Sea Mall", "07-Arab Mall",
        "08-Makkah Mall", "09-Al-Salam Mall", "11-Jouri Mall", "13-Al-Yasmin Mall",
        "14-Al Kamal Mall", "17-Arar Othaim Mall", "18-Al_Khayyat Center",
        "20-Sitten Street Makkah", "21-Abha Al_Rashid Mall New", "22-Tabuk Park",
        "23-Alia Mall Madinah", "24-Yanbu Dana Mall", "26-Al-Noor Mall Madinah",
        "41-Khamis Avenue", "43-Mujan Park", "44-Al-Jouf Center", "48 - Jeddah Park",
        "52-Al_Baha Mall", "53-Al Basateen Mall", "54-THE VILLAGE", "55- Jabl Omar",
        "56- Aziz Mall 2", "57-Sauq7"
    ],
    "warehouse riyadh": [
        "12-Al_Hamra Mall", "15-Riyadh Othaim Mall", "16-Ehsa Othaim Mall",
        "19-Hail Othaim Mall", "25-Rabwa Othaim Mall", "27-Dhahran Mall khobar",
        "28-Al Nakheel Mall Dammam", "29-Al Nakheel Mall Riyadh",
        "30-Tala Mall Riyadh", "32-Atyaf Mall Riyadh", "36-Al jubail Mall",
        "38-Al_Riyadh Park", "39-Salam Mall Riyadh", "40-Hayat Mall Riyad",
        "42-Dareen Mall Dammam", "45- Riyadh Gallery Mall", "46-Khaleej Mall Riyadh",
        "47-Al-Nakheel Plaza", "49-AlAhsa Mall", "50-Meem Plaza Riyadh",
        "51-Park Avenue Riyadh"
    ]
}

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/")
def home():
    return "✅ Flask Email API is live."

@app.route("/submit-order", methods=["POST"])
def submit_order():
    data = request.json
    mall = data["mall"]
    orders = data["orders"]
    has_extras = data.get("hasExtras", False)

    warehouse = "Warehouse" if mall in mallMap["Warehouse"] else "warehouse riyadh"
    recipient = mall_to_email.get(warehouse, mall_to_email["Warehouse"])

    date = datetime.now().strftime("%Y-%m-%d")
    filename = f"طلبية {mall} - {date}.xlsx"
    folder = "orders"
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    # إنشاء ملف Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "طلبية"
    ws.append(["اسم المعرض:", mall])
    ws.append([])
    ws.append(["الكود", "الاسم", "Alias", "الكمية المطلوبة"])

    for item in orders:
        ws.append([
            item.get("code", ""),
            item.get("name", ""),
            item.get("alias", ""),  # إدراج alias
            item.get("qty", "")
        ])

    if has_extras:
        ws.append([])
        ws.append(["⚠️ يوجد مستلزمات إضافية مرافقة لهذه الطلبية."])

    wb.save(filepath)

    # تخزين في Firestore
    try:
        db.collection("orders").add({
            "date": date,
            "mall": mall,
            "warehouse": warehouse,
            "hasExtras": has_extras,
            "orders": orders,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
    except Exception as firestore_error:
        return {"status": "error", "message": f"Firestore Error: {str(firestore_error)}"}

    # إرسال بالبريد
    try:
        msg = EmailMessage()
        msg["Subject"] = f"طلبية جديدة من معرض {mall}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient
        msg.set_content(f"تم استلام طلبية جديدة من {mall}.\n\nمرفق ملف الطلبية بصيغة Excel.")

        with open(filepath, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(filepath)
            msg.add_attachment(file_data, maintype="application",
                               subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               filename=file_name)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASS)
            smtp.send_message(msg)

        return {"status": "success", "message": f"📩 تم إرسال الطلبية إلى {recipient}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
