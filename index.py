from flask import Flask, render_template, request, redirect, session
from models import db, cursor
import pandas as pd
from flask import send_file

app = Flask(__name__)
app.secret_key = "flask_qarz_daftar"

#--------------------------------------------------------------------------------------#
@app.route("/")
def index():
    return render_template("index.html")
#--------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------#
@app.route("/register", methods=["POST", "GET"])
def register():
    if session.get("user"):
        return redirect("/")
    else:
        message = ""
        if request.method == "POST":
            fullname = request.form.get("fullname")
            phone = request.form.get("phone")
            address = request.form.get("address")
            password = request.form.get("password")

            cursor.execute(f"SELECT * FROM foydalanuvchilar WHERE phone = '{phone}'")
            user = cursor.fetchone()

            if user:
                message = "Bu telefon raqamli foydalanuvchi mavjud."
            else:
                cursor.execute(f"INSERT INTO foydalanuvchilar (fullname, phone, address, password, total_debt) VALUES ('{fullname}', '{phone}', '{address}', '{password}', 0)")
                db.commit()

                # CREATE NEW USER #
                cursor.execute(f"""CREATE TABLE IF NOT EXISTS user_{phone.replace('+', '').replace('-', '').replace(' ', '')} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            message TEXT,
                            amount DECIMAL DEFAULT 0,
                            date DATETIME DEFAULT CURRENT_TIMESTAMP,
                            mode TEXT)
                            """)
                db.commit()
                return redirect("/login")

        return render_template("register.html", message=message)
#--------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------#
@app.route("/login", methods=["POST", "GET"])
def login():
    if session.get("user"):
        return redirect("/")
    else:
        message = ""
        if request.method == "POST":
            phone = request.form.get("phone")
            password = request.form.get("password")

            cursor.execute(f"SELECT * FROM foydalanuvchilar WHERE phone = '{phone}' AND password = '{password}'")
            user = cursor.fetchone()

            if user:
                session["user"] = ""
                session["user"] = user
                return redirect("/")
            else:
                message = "Bunday foydalanuvchi topilmadi"
        return render_template("login.html", message=message)
#--------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------#
@app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/")
#--------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------#
@app.route("/base", methods=["POST", "GET"])
def base():
    if not session.get("user"):
        return redirect("/")
    else:
        if request.method == "POST":
            if request.form.get("product") and request.form.get("amount"):
                product = request.form.get("product")
                amount = request.form.get("amount")
                user_id = request.form.get("user_id")

                cursor.execute(f"UPDATE foydalanuvchilar SET total_debt = total_debt + {amount} WHERE phone = {user_id}")
                db.commit()

                cursor.execute(f"INSERT INTO user_{user_id.replace('+', '').replace('-', '').replace(' ', '')} (amount, message, mode) VALUES ('{amount}', '{product}', 'Qarz oldi!')")
                db.commit()

            return redirect("/debtors")

        if session.get("user"):
            cursor.execute("SELECT * FROM foydalanuvchilar")
            users = cursor.fetchall()
            return render_template("base.html", users=users)
#--------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------#
@app.route("/get_history_as_excel", methods=["POST"])
def get_history_as_excel():
    if not session.get("user"):
        return redirect("/")
    else:
        if request.method == "POST":
            user_id = request.form.get("user_id")

            cursor.execute(f"SELECT * FROM user_{user_id.replace('+', '').replace('-', '').replace(' ', '')}")
            data = cursor.fetchall()

            try:
                df = pd.DataFrame(data)
                filepath = f"user_{user_id.replace('+', '').replace('-', '').replace(' ', '')}.xlsx"
                df.to_excel(filepath, index=False, header=["ID", "Izoh", "Qiymati", "Sanasi", "Qarz oldi/Qaytardi?"])
                return send_file(filepath, as_attachment=True)
            except:
                return redirect("/base")
        return redirect("/base")
#--------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------#
@app.route("/debtors", methods=["POST", "GET"])
def debtors():
    if not session.get("user"):
        return redirect("/")
    else:
        if request.method == "GET":
            cursor.execute("SELECT * FROM foydalanuvchilar")
            users = cursor.fetchall()

            cursor.execute("SELECT * FROM foydalanuvchilar WHERE total_debt > 0")
            debtors = cursor.fetchall()

            return render_template("debtors.html", users=users, debtors=debtors)
        elif request.method == "POST":
            product = request.form.get("product")
            amount = request.form.get("amount")
            user_id = request.form.get("user_id")
            type = request.form.get("type")

            if type == "increment":
                cursor.execute(f"UPDATE foydalanuvchilar SET total_debt = total_debt + {amount} WHERE phone = {user_id}")
                db.commit()

                cursor.execute(f"INSERT INTO user_{user_id.replace('+', '').replace('-', '').replace(' ', '')} (amount, message, mode) VALUES ('{amount}', '{product}', 'Qarz oldi!')")
                db.commit()
            elif type == "decrement":
                cursor.execute(f"UPDATE foydalanuvchilar SET total_debt = total_debt - {amount} WHERE phone = {user_id}")
                db.commit()

                cursor.execute(f"INSERT INTO user_{user_id.replace('+', '').replace('-', '').replace(' ', '')} (amount, message, mode) VALUES ('{amount}', '{product}', 'Qarzni topshirdi!')")
                db.commit()

            return redirect("/debtors")
#--------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------#
@app.route("/users_base", methods=["GET"])
def users_base():
    if not session.get("user"):
        return redirect("/")
    else:
        if request.method == "GET":
            cursor.execute("SELECT * FROM foydalanuvchilar")
            users = cursor.fetchall()

            df = pd.DataFrame(users)
            filepath = "users.xlsx"

            df.to_excel(filepath, index=False, header=["ID", "Familiyasi va ismi", "Telefon raqami", "Paroli", "Manzili", "Qachondan mavjud?", "Umumiy qarz summasi", "Adminmi?"])
            return send_file(filepath, as_attachment=True)

        return redirect("/base")
#--------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------#
@app.route("/my_debts")
def my_debts():
    if not session.get("user"):
        return redirect("/")
    else:
        if session.get("user"):
            cursor.execute(f"SELECT * FROM foydalanuvchilar WHERE phone = '{session.get('user')['phone']}'")
            user = cursor.fetchone()

            cursor.execute(f"SELECT * FROM user_{user['phone'].replace('+', '').replace('-', '').replace(' ', '')}")
            data = cursor.fetchall()

            return render_template("base.html", user=user, data=data)
#--------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------#
@app.route("/search", methods=["POST", "GET"])
def search():
    if not session.get("user"):
        return redirect("/")
    else:
        if request.method == "POST":
            search = request.form.get("search")
            type = request.form.get("type")

            if type == "phone":
                cursor.execute(f"SELECT * FROM foydalanuvchilar WHERE phone LIKE '%{search}%'")
            elif type == "fullname":
                cursor.execute(f"SELECT * FROM foydalanuvchilar WHERE fullname LIKE '%{search}%'")
            elif type == "address":
                cursor.execute(f"SELECT * FROM foydalanuvchilar WHERE address LIKE '%{search}%'")
            elif type == "date":
                cursor.execute(f"SELECT * FROM foydalanuvchilar WHERE registered_date LIKE '%{search}%'")

            users = cursor.fetchall()
            return render_template("search.html", users=users)
        else:
            return render_template("search.html")
#--------------------------------------------------------------------------------------#
