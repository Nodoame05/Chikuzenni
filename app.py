from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import pyrebase, json, os, firebase_admin, uuid, bcrypt
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
# bcrypt = Bcrypt(app) 


#teacher側GET
@app.route("/teacher/<string:uuid>/status", methods=["GET"])
def teacher_status(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token == teacher_data.get("token"):
        status = teacher_data.get("status")
        status_list = teacher_data.get("status_list")
        now_status = status_list[status]
        return jsonify({"status":now_status})
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
            response.append({"name":teacher_data.get("name"),"uuid":teacher_data.get("uuid"),"status":now_status})
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
    #teacher&student document取得
    all_student_data = db.collection("student").stream()
    all_teacher_data = db.collection("teacher").stream()
    student_token_list = []
    teacher_token_list = []
    #studentのtoken取り出し
    for student_token_data in all_student_data:
        student_token_list.append(student_token_data.get("token"))
    #teacherのtoken取り出し
    for teacher_token_data in all_teacher_data:
        teacher_token_list.append(teacher_token_data.get("token"))
    all_token_list = student_token_list + teacher_token_list
    for token_data in all_token_list:
        if token == token_data:
            response = []
            all_student_data = db.collection("student").stream()
            for student_data in all_student_data:
                subject_list = student_data.get("subject")
                for subject_map in subject_list:
                    if uuid == subject_map.get("uuid"):
                        response.append({"doc_id":student_data.id,"name":student_data.get("name"),"uuid":student_data.get("uuid")})
            return response
    return jsonify({"message":"アクセスが拒否されました。"}),403

    
#teacher側POST
@app.route("/teacher/signup", methods=["POST"])
def teacher_signup():
    teacher = request.get_json()
    teacher_name = teacher.get("name")
    teacher_email = teacher.get("email")
    machine_id = teacher.get("machine")
    teacher_uuid = str(uuid.uuid4())
    teacher_password = teacher.get("password")
    b_password = bytes(teacher_password,"utf-8")
    salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
    hash_password = bcrypt.hashpw(b_password,salt)
    db.collection("teacher").document(teacher_uuid).set({
        "verification":False,
        "available":False,
        "email":teacher_email,
        "machine_id":machine_id,
        "name":teacher_name,
        "password_hash":hash_password,
        "status":1,
        "status_list":["在室","不在"],
        "subject":[],
        "uuid":teacher_uuid,
    })
    #requests.post("https://script.google.com/macros/s/AKfycby4a8UMh_gJZuO2I10zAK2_q2AUoAfuhGJxJS8ZrD_8AkAbd9TarFjd9jqsL1geryk/exec",headers="Content-Type: application/json",json={"body":"ボディ","email":teacher_email,"subject":"メールアドレス認証"})
    return jsonify({"message":"success"})
    
@app.route("/teacher/login", methods=["POST"])
def teacher_login():
    teacher = request.get_json()
    teacher_email = teacher.get("email")
    all_teacher_data = db.collection("teacher").stream()
    for teacher_data in all_teacher_data:
        if teacher_data.get("email") == teacher_email:
            if teacher_data.get("verification") == True:
                teacher_password = bytes(teacher.get("password"),'UTF-8')
                hash_password = teacher_data.get("password_hash")
                if bcrypt.checkpw(teacher_password,hash_password):
                    teacher_token = str(uuid.uuid4())
                    db.collection("teacher").document(teacher_data.get("uuid")).update({
                        "token":teacher_token
                    })
                    return jsonify({"token":teacher_token})
                else:
                    return jsonify({"message":"間違ったパスワード"})                
            else:
                return jsonify({"message":"認証の通っていないメールアドレス"})
    return jsonify({"message":"間違ったメールアドレス"})

# @app.route("teacher/<string:uuid>/status", methods=["POST"])

# @app.route("teacher/<string:uuid>/statuses", methods=["POST"])

# @app.route("teacher/<string:uuid>/delete/member", methods=["POST"])

# @app.route("teacher/<string:uuid>/invitation", methods=["POST"])

# @app.route("teacher/<string:uuid>/delete/class", methods=["POST"])

# @app.route("teacher/<string:uuid>/setting", methods=["POST"])

# #student側POST
# @app.route("student/signup", methods=["POST"])

# @app.route("student/login", methods=["POST"])

# @app.route("student/<string:uuid>/")




# run the app.
if __name__ == "__main__":
    app.debug = True
    app.run(port=5000)
