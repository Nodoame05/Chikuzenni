from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import pyrebase, json, os, firebase_admin, uuid
from firebase_admin import credentials, firestore, auth
from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout
from datetime import date, datetime

app = Flask(__name__)

#JSONの中身を辞書型に格納
fs_dict = {
    "type":os.environ["FB_TYPE"],
    "project_id":os.environ["FB_PROJECt_ID"],
    "private_key":os.environ["FB_PRIVATE_KEY"],
    "client_email":os.environ["FB_CLIENT_EMAIL"],
    "token_uri":os.environ["FB_TOKEN_URI"]
}
fa_dict = {
    "apiKey":os.environ["FB_APIKEY"],
    "authDomain":os.environ["FB_AUTH_DOMAIN"],
    "projectId":os.environ["FB_PROJECt_ID"],
    "storageBucket":os.environ["FB_STORAGE_BUCKET"],
    "messagingSenderId":os.environ["FB_MESSAGING_SENDER_ID"],
    "appId":os.environ["FB_APP_ID"],
    "databaseURL":os.environ["FB_DATABASE_URL"]
}
#firebase_Auth認証
firebase = pyrebase.initialize_app(fa_dict)
auth = firebase.auth()
#firestore認証
cred = credentials.Certificate(fs_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()
app.config['SECRET_KEY'] ="3782c00aae1e468f9809d8d34011a84d"


#teacher側GET
@app.route("/teacher/<string:uuid>/status", methods=["GET"])
def teacher_status(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token == teacher_data.get("token"):
        return jsonify({"status":teacher_data.get("status")})
    return jsonify({"message":"アクセスが拒否されました。"}),403 


@app.route("/teacher/<string:uuid>/statuses", methods=["GET"])
def teacher_statuses(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token == teacher_data.get("token"):
        return jsonify({"statuses":teacher_data.get("status_list")})
    return jsonify({"message":"アクセスが拒否されました。"}),403 


@app.route("/teacher/<string:uuid>/subjects", methods=["GET"])
def teacher_subjects(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token == teacher_data.get("token"):
        return teacher_data.get("subject")
    return jsonify({"message":"アクセスが拒否されました。"}),403


@app.route("/teacher/<string:uuid>/names", methods=["GET"])
def teacher_all(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token == teacher_data.get("token"):
        return jsonify({"name":teacher_data.get("name"),"email":teacher_data.get("email")})
    return jsonify({"message":"アクセスが拒否されました。"}),403


@app.route("/Machine/<string:uuid>", methods=["GET"])
def machine_id(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token == teacher_data.get("token"):
        return jsonify({"id":teacher_data.get("machine_id")})
    return jsonify({"message":"アクセスが拒否されました。"}),403


#student側GET
@app.route("/student/<string:uuid>/teacherlist", methods=["GET"])
def teacher_list(uuid):
    token = request.headers.get("token")
    student_data = db.collection("student").document(uuid).get()
    if token == student_data.get("token"):
        all_teacher_data = db.collection("teacher").stream()
        response = []
        for teacher_data in all_teacher_data:
            status = teacher_data.get("status")
            status_list = teacher_data.get("status_list")
            now_status = status_list[status]
            response.append({"doc_id":teacher_data.id,"name":teacher_data.get("name"),"uuid":teacher_data.get("uuid"),"status":now_status})
        return response
    return jsonify({"message":"アクセスが拒否されました。"}),403


@app.route("/student/<string:uuid>", methods=["GET"])
def student_all(uuid):
    token = request.headers.get("token")
    student_data = db.collection("student").document(uuid).get()
    if token == student_data.get("token"):
        return jsonify({"name":student_data.get("name"),"email":student_data.get("email")})
    return jsonify({"message":"アクセスが拒否されました。"}),403


#subject GET
@app.route("/subject/<string:uuid>/students", methods=["GET"])
def student_list(uuid):
    token = request.headers.get("token")
    all_student_data = db.collection("student").stream()
    all_teacher_data = db.collection("teacher").stream()
    student_token_list = []
    teacher_token_list = []
    for student_token_data in all_student_data:
        student_token_list.append(student_token_data.get("token"))
    for teacher_token_data in all_teacher_data:
        teacher_token_list.append(teacher_token_data.get("token"))
    all_token_list = student_token_list + teacher_token_list
    for token_data in all_token_list:
        if token == token_data:
            response = []
            for student_data in all_student_data:
                subject_list = student_data.get("subject")
                for subject_map in subject_list:
                    if uuid == subject_map["uuid"]:
                        response.append({"doc_id":student_data.id,"name":student_data.get("name"),"uuid":student_data.get("uuid")})
            return response
    return jsonify({"message":"アクセスが拒否されました。"}),403

    
#teacher側POST

#student側POST




# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "GET":
#         return render_template("login.html",msg="")

#     email = request.form.get("email")
#     password = request.form.get("password")
#     print(f"email:{email},password:{password}")
#     user = auth.sign_in_with_email_and_password(email, password)
#     session["usr"] = email
#     users = db.collection("users").document()
#     users.set({
#         "email": email,
#         "password": password
#     })
#     user_id = users.get()
#     session["id"] = user_id.id
#     return redirect(url_for("index"))
    

# @app.route("/", methods=["GET"])
# def index():
#    usr = session.get("usr")
#    if usr == None:
#        return redirect(url_for("login"))
#    return render_template("index.html", usr=usr)

# @app.route("/logout")
# def logout():
#    del session["usr"]
#    user_id = session["id"]
#    db.collection("users").document(user_id).delete()
#    return redirect(url_for("login"))


# run the app.
if __name__ == "__main__":
    app.debug = True
    app.run(port=5000)
