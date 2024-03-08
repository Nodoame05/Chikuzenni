import os
import re
import uuid
from datetime import datetime, timedelta

import bcrypt
import firebase_admin
import pyrebase
import requests
from firebase_admin import credentials, firestore
from flask import Flask, jsonify, request

import invitation

app = Flask(__name__)

fs_dict = {
    "type": os.environ["FB_TYPE"],
    "project_id": os.environ["FB_PROJECt_ID"],
    "private_key": os.environ["FB_PRIVATE_KEY"].replace(r"\n", "\n"),
    "client_email": os.environ["FB_CLIENT_EMAIL"],
    "token_uri": os.environ["FB_TOKEN_URI"],
}
fa_dict = {
    "apiKey": os.environ["FB_APIKEY"],
    "authDomain": os.environ["FB_AUTH_DOMAIN"],
    "projectId": os.environ["FB_PROJECt_ID"],
    "storageBucket": os.environ["FB_STORAGE_BUCKET"],
    "messagingSenderId": os.environ["FB_MESSAGING_SENDER_ID"],
    "appId": os.environ["FB_APP_ID"],
    "databaseURL": os.environ["FB_DATABASE_URL"],
}
# firebase_Auth認証
firebase = pyrebase.initialize_app(fa_dict)
# firestore認証
cred = credentials.Certificate(fs_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()
app.config["SECRET_KEY"] = "3782c00aae1e468f9809d8d34011a84d"


# teacher側GET
@app.route("/teacher/<string:uuid>/status/", methods=["GET"])
def teacher_status(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    status = teacher_data.get("status")
    status_list = teacher_data.get("status_list")
    now_status = status_list[status]
    return jsonify({"status": now_status}), 200


@app.route("/teacher/<string:uuid>/statuses/", methods=["GET"])
def teacher_statuses(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401
    return jsonify({"statuses": teacher_data.get("status_list")}), 200


@app.route("/teacher/<string:uuid>/subjects/", methods=["GET"])
def teacher_subjects(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(uuid).get()
    all_subject_data = db.collection("subject").stream()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    uuid_list = []
    response = []
    teacher_subject_list = teacher_data.get("subject")
    for teacher_subject_uuid in teacher_subject_list:
        uuid_list.append(teacher_subject_uuid.get("uuid"))
    for subject_data in all_subject_data:
        for uuid in uuid_list:
            if subject_data.get("uuid") == uuid:
                response.append(
                    {
                        "name": subject_data.get("name"),
                        "uuid": subject_data.get("uuid"),
                        "invitation": subject_data.get("invitation"),
                    }
                )
    return response, 200


@app.route("/teacher/<string:uuid>/names/", methods=["GET"])
def teacher_all(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401
    return (
        jsonify({"name": teacher_data.get("name"), "email": teacher_data.get("email")}),
        200,
    )


@app.route("/Machine/<string:uuid>/", methods=["GET"])
def machine_id(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401
    return jsonify({"id": teacher_data.get("machine_id")}), 200


# student側GET
@app.route("/student/<string:uuid>/teacherlist/", methods=["GET"])
def teacher_list(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    student_data = db.collection("student").document(uuid).get()
    if token != student_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    student_subject = student_data.get("subject")
    response = []
    student_uuid_list = []
    for student_subject_map in student_subject:
        student_uuid_list.append(student_subject_map.get("uuid"))
    for student_uuid in student_uuid_list:
        all_teacher_data = db.collection("teacher").stream()
        for teacher_data in all_teacher_data:
            teacher_subject = teacher_data.get("subject")
            for teacher_subject_map in teacher_subject:
                if teacher_subject_map.get("uuid") == student_uuid:
                    status = teacher_data.get("status")
                    status_list = teacher_data.get("status_list")
                    now_status = status_list[status]
                    response.append(
                        {
                            "name": teacher_data.get("name"),
                            "uuid": teacher_data.get("uuid"),
                            "status": now_status,
                        }
                    )
    return response, 200


@app.route("/student/<string:uuid>/", methods=["GET"])
def student_all(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    student_data = db.collection("student").document(uuid).get()
    if token != student_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401
    return (
        jsonify({"name": student_data.get("name"), "email": student_data.get("email")}),
        200,
    )


# subject GET
@app.route("/subject/<string:uuid>/students/", methods=["GET"])
def student_list(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    # teacher&student document取得
    all_student_data = db.collection("student").stream()
    all_teacher_data = db.collection("teacher").stream()
    student_token_list = []
    teacher_token_list = []
    # studentのtoken取り出し
    for student_token_data in all_student_data:
        try:
            # ISSUE tokenがない(認証されていない)アカウントでerrorが出る
            student_token_list.append(student_token_data.get("token"))
        except:
            pass
    # teacherのtoken取り出し
    for teacher_token_data in all_teacher_data:
        try:
            # ISSUE tokenがない(認証されていない)アカウントでerrorが出る
            teacher_token_list.append(teacher_token_data.get("token"))
        except:
            pass
    all_token_list = student_token_list + teacher_token_list
    if token not in all_token_list:
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    response = []
    all_student_data = db.collection("student").stream()
    for student_data in all_student_data:
        subject_list = student_data.get("subject")
        for subject_map in subject_list:
            if uuid == subject_map.get("uuid"):
                response.append(
                    {
                        "doc_id": student_data.id,
                        "name": student_data.get("name"),
                        "uuid": student_data.get("uuid"),
                    }
                )
    return response, 200


# machine側GET
@app.route("/machine", methods=["GET"])
def now_status():
    machine_id = request.headers.get("machine_ID")
    if machine_id == None:
        return jsonify({"message": "machine_IDがありません。"}), 400

    all_teacher_data = db.collection("teacher").stream()
    for teacher_data in all_teacher_data:
        if teacher_data.get("machine_id") == machine_id:
            return jsonify({"status": teacher_data.get("status")}), 200
    return jsonify({"message": "間違ったid"}), 401


# teacher側POST
@app.route("/teacher/signup/", methods=["POST"])
def teacher_signup():
    teacher = request.get_json()
    teacher_name = teacher.get("name")
    machine_id = teacher.get("machine")
    teacher_email = teacher.get("email")
    if teacher_name == None:
        return jsonify({"message": "nameがありません。"}), 400
    elif machine_id == None:
        return jsonify({"message": "machineがありません。"}), 400
    elif teacher_email == None:
        return jsonify({"message": "emailがありません。"}), 400

    # 正規表現
    pattern = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.fullmatch(pattern, teacher_email):
        return jsonify({"message": "間違ったメールアドレス形式"}), 406

    teacher_uuid = str(uuid.uuid4())
    teacher_password = teacher.get("password")
    if teacher_password == None:
        return jsonify({"message": "passwordがありません。"}), 400

    b_password = bytes(teacher_password, "utf-8")
    salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
    hash_password = bcrypt.hashpw(b_password, salt)
    db.collection("teacher").document(teacher_uuid).set(
        {
            "available": False,
            "email": teacher_email,
            "machine_id": machine_id,
            "name": teacher_name,
            "password_hash": hash_password,
            "status": 1,
            "status_list": ["在室", "不在", "初期値1", "初期値2", "初期値3"],
            "subject": [],
            "uuid": teacher_uuid,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )
    # requests.post("https://script.google.com/macros/s/AKfycby4a8UMh_gJZuO2I10zAK2_q2AUoAfuhGJxJS8ZrD_8AkAbd9TarFjd9jqsL1geryk/exec",headers="Content-Type: application/json",json={"body":"ボディ","email":teacher_email,"subject":"メールアドレス認証"})
    return jsonify({"message": "success", "email": teacher_email}), 200


@app.route("/teacher/login/", methods=["POST"])
def teacher_login():
    # データの読み込み
    teacher = request.get_json()
    teacher_email = teacher.get("email")
    if teacher_email == None:
        return jsonify({"message": "emailがありません。"}), 400

    teacher_password = teacher.get("password")
    if teacher_password == None:
        return jsonify({"message": "passwordがありません。"}), 400

    teacher_password = bytes(teacher_password, "UTF-8")
    all_teacher_data = db.collection("teacher").stream()

    # アカウント検索
    for teacher_data in all_teacher_data:
        if teacher_data.get("email") == teacher_email:
            break
    else:
        return jsonify({"message": "間違ったメールアドレス"}), 400

    # アカウントデータの整理
    hash_password = teacher_data.get("password_hash")
    teacher_available = teacher_data.get("available")

    # 有効アカウントでなかったらエラー
    if not (teacher_available):
        return jsonify({"message": "認証の通っていないメールアドレス"}), 401

    # パスワードが間違っていたらエラー
    if not (bcrypt.checkpw(teacher_password, hash_password)):
        return jsonify({"message": "間違ったパスワード"}), 400

    # 全認証クリア時：トークン発行
    teacher_token = str(uuid.uuid4())
    db.collection("teacher").document(teacher_data.get("uuid")).update(
        {
            "token": teacher_token,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return (
        jsonify(
            {
                "message": "success",
                "token": teacher_token,
                "uuid": teacher_data.get("uuid"),
            }
        ),
        200,
    )


@app.route("/teacher/forget/", methods=["POST"])
def teacher_forget():
    request_json = request.get_json()
    teacher_email = request_json.get("email")
    if teacher_email == None:
        return jsonify({"message": "emailがありません。"}), 400

    all_teacher_data = db.collection("teacher").stream()
    for teacher_data in all_teacher_data:
        if teacher_data.get("email") == teacher_email:
            break
    else:
        return jsonify({"message": "間違ったメールアドレス"}), 400

    secret = str(uuid.uuid4())
    db.collection("teacher").document(teacher_data.get("uuid")).update(
        {"updated_at": firestore.SERVER_TIMESTAMP}
    )
    expired = (
        db.collection("teacher")
        .document(teacher_data.get("uuid"))
        .get()
        .get("updated_at")
        .replace(tzinfo=None)
    )
    expired = expired + timedelta(minutes=10)
    db.collection("teacher").document(teacher_data.get("uuid")).update(
        {
            "secret": {"secret": secret, "expired_at": expired},
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    url = "https://teacher/forget/:uuid?secret=" + secret
    # requests.post(url,headers="Content-Type: application/json",json={"body":"ボディ","email":teacher_email,"subject":"パスワード変更"})
    return jsonify({"message": "success"}), 200


@app.route("/teacher/<string:uuid>/status/current/", methods=["POST"])
def change_current_status(uuid):
    request_json = request.get_json()
    status = request_json.get("status")
    if status == None:
        return jsonify({"message": "statusがありません。"}), 400

    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    db.collection("teacher").document(uuid).update(
        {"status": status, "updated_at": firestore.SERVER_TIMESTAMP}
    )
    return jsonify({"message": "success"}), 200


@app.route("/teacher/<string:uuid>/status/names/", methods=["POST"])
def change_status_names(uuid):
    teacher_status_list = request.get_json()
    if (
        teacher_status_list.get("3") == None
        or teacher_status_list.get("4") == None
        or teacher_status_list.get("5") == None
    ):
        return jsonify({"message": "変更するstatus_listの中身が不足しています。"}), 400

    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    db.collection("teacher").document(uuid).update(
        {"status_list": firestore.DELETE_FIELD}
    )
    db.collection("teacher").document(uuid).update(
        {
            "status_list": firestore.ArrayUnion(
                [
                    "在室",
                    "不在",
                    teacher_status_list.get("3"),
                    teacher_status_list.get("4"),
                    teacher_status_list.get("5"),
                ]
            ),
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return jsonify({"message": "success"}), 200


@app.route("/teacher/<string:t_uuid>/create_subject/", methods=["POST"])
def create_subject(t_uuid):
    request_json = request.get_json()
    subject_name = request_json.get("name")
    if subject_name == None:
        return jsonify({"message": "nameがありません。"}), 400

    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(t_uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    subject_uuid = str(uuid.uuid4())
    new_subject = {
        "name": subject_name,
        "invitation": invitation.create_inv(1),
        "uuid": subject_uuid,
    }
    db.collection("subject").document(subject_uuid).set(new_subject)
    db.collection("teacher").document(t_uuid).update(
        {
            "subject": firestore.ArrayUnion([{"uuid": subject_uuid}]),
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return jsonify({"massage": "success", "item": new_subject}), 200


@app.route("/teacher/<string:uuid>/delete_subject/", methods=["POST"])
def delete_subject(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    subject = request.get_json()
    subject_uuid = subject.get("subject_uuid")
    if subject_uuid == None:
        return jsonify({"message": "subject_uuidがありません。"}), 400

    db.collection("subject").document(subject_uuid).delete()
    db.collection("teacher").document(uuid).update(
        {
            "subject": firestore.ArrayRemove([{"uuid": subject_uuid}]),
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    all_student_data = db.collection("student").stream()
    for student_data in all_student_data:
        student_subject = student_data.get("subject")
        for student_subject_map in student_subject:
            if student_subject_map.get("uuid") == subject_uuid:
                db.collection("student").document(student_data.get("uuid")).update(
                    {
                        "subject": firestore.ArrayRemove([{"uuid": subject_uuid}]),
                        "updated_at": firestore.SERVER_TIMESTAMP,
                    }
                )
    return jsonify({"message": "success"}), 200


@app.route("/teacher/<string:uuid>/setting/name/", methods=["POST"])
def setting_teacher_name(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    teacher = request.get_json()
    teacher_name = teacher.get("name")
    if teacher_name == None:
        return jsonify({"message": "nameがありません。"}), 400

    db.collection("teacher").document(uuid).update(
        {
            "name": teacher_name,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return jsonify({"message": "success"}), 200


@app.route("/teacher/<string:uuid>/setting/machine/", methods=["POST"])
def setting_machine(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    teacher = request.get_json()
    machine_id = teacher.get("machine")
    if machine_id == None:
        return jsonify({"message": "machineがありません。"}), 400

    db.collection("teacher").document(uuid).update(
        {
            "machine_id": machine_id,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return jsonify({"message": "success"}), 200


@app.route("/teacher/<string:uuid>/setting/password/", methods=["POST"])
def setting_teacher_password(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    teacher = request.get_json()
    teacher_pre_password = teacher.get("pre_password")
    if teacher_pre_password == None:
        return jsonify({"message": "pre_passwordがありません。"}), 400

    get_pre_password = bytes(teacher_pre_password, "UTF-8")
    teacher_data = db.collection("teacher").document(uuid).get()
    teacher_pre_password = teacher_data.get("password_hash")
    if not (bcrypt.checkpw(get_pre_password, teacher_pre_password)):
        return jsonify({"message": "間違ったパスワード"}), 400

    new_password = teacher.get("new_password")
    if new_password == None:
        return jsonify({"message": "new_passwordがありません。"}), 400

    b_password = bytes(new_password, "utf-8")
    salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
    hash_password = bcrypt.hashpw(b_password, salt)
    db.collection("teacher").document(uuid).update(
        {
            "password_hash": hash_password,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return jsonify({"message": "success"}), 200


@app.route("/teacher/<string:uuid>/forget_password/", methods=["POST"])
def teacher_forget_password(uuid):
    request_json = request.get_json()
    request_secret = request_json.get("secret")
    if request_secret == None:
        return jsonify({"message": "secretがありません。"}), 400

    teacher_secret = db.collection("teacher").document(uuid).get().get("secret")
    secret_secret = teacher_secret.get("secret")
    if request_secret != secret_secret:
        return jsonify({"message": "間違ったsecret"}), 400

    now = datetime.now()
    teacher_expired = teacher_secret.get("expired_at")
    expired_datetime = datetime.fromtimestamp(teacher_expired.timestamp())
    sub_time = expired_datetime - now
    if sub_time.total_seconds() < 0:
        return jsonify({"message": "期限切れのsecret"}), 400

    request_password = request_json.get("password")
    if request_password == None:
        return jsonify({"message": "passwordがありません。"}), 400

    b_password = bytes(request_password, "utf-8")
    salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
    hash_password = bcrypt.hashpw(b_password, salt)
    db.collection("teacher").document(uuid).update(
        {
            "password_hash": hash_password,
            "updated_at": firestore.SERVER_TIMESTAMP,
            "token": firestore.DELETE_FIELD,
            "secret": firestore.DELETE_FIELD,
        }
    )
    return jsonify({"message": "success"}), 200


# #student側POST
@app.route("/student/signup/", methods=["POST"])
def student_signup():
    student = request.get_json()
    student_name = student.get("name")
    student_email = student.get("email")
    if student_name == None:
        return jsonify({"message": "nameがありません。"}), 400
    elif student_email == None:
        return jsonify({"message": "emailがありません。"}), 400

    # 正規表現
    pattern = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.fullmatch(pattern, student_email):
        return jsonify({"message": "間違ったメールアドレス形式"}), 406

    student_uuid = str(uuid.uuid4())
    teacher_password = student.get("password")
    if teacher_password == None:
        return jsonify({"message": "passwordがありません。"}), 400

    b_password = bytes(teacher_password, "utf-8")
    salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
    hash_password = bcrypt.hashpw(b_password, salt)
    db.collection("student").document(student_uuid).set(
        {
            "available": False,
            "email": student_email,
            "name": student_name,
            "password_hash": hash_password,
            "subject": [],
            "uuid": student_uuid,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )
    # requests.post("https://script.google.com/macros/s/AKfycby4a8UMh_gJZuO2I10zAK2_q2AUoAfuhGJxJS8ZrD_8AkAbd9TarFjd9jqsL1geryk/exec",headers="Content-Type: application/json",json={"body":"ボディ","email":student_email,"subject":"メールアドレス認証"})
    return jsonify({"message": "success", "email": student_email}), 200


@app.route("/student/login/", methods=["POST"])
def student_login():
    # データの読み込み
    student = request.get_json()
    student_email = student.get("email")
    if student_email == None:
        return jsonify({"message": "emailがありません。"}), 400

    student_password = student.get("password")
    if student_password == None:
        return jsonify({"message": "passwordがありません。"}), 400

    student_b_password = bytes(student.get("password"), "UTF-8")
    all_student_data = db.collection("student").stream()

    # アカウント検索
    for student_data in all_student_data:
        if student_data.get("email") == student_email:
            break
    else:
        return jsonify({"message": "間違ったメールアドレス"}), 400

    # アカウントデータの整理
    hash_password = student_data.get("password_hash")
    student_available = student_data.get("available")

    # 有効アカウントでなかったらエラー
    if not (student_available):
        return jsonify({"message": "認証の通っていないメールアドレス"}), 401

    # パスワードが間違っていたらエラー
    if not (bcrypt.checkpw(student_b_password, hash_password)):
        return jsonify({"message": "間違ったパスワード"}), 400

    # 全認証クリア時：トークン発行
    student_token = str(uuid.uuid4())
    db.collection("student").document(student_data.get("uuid")).update(
        {
            "token": student_token,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )

    return (
        jsonify(
            {
                "message": "success",
                "token": student_token,
                "uuid": student_data.get("uuid"),
            }
        ),
        200,
    )


@app.route("/student/<string:uuid>/setting/name/", methods=["POST"])
def setting_student_name(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    student_data = db.collection("student").document(uuid).get()
    if token != student_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    student = request.get_json()
    student_name = student.get("name")
    if student_name == None:
        return jsonify({"message": "nameがありません。"}), 400

    db.collection("student").document(uuid).update(
        {
            "name": student_name,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return jsonify({"message": "success"}), 200


@app.route("/student/<string:uuid>/setting/password/", methods=["POST"])
def setting_student_password(uuid):
    token = request.headers.get("token")
    if token == None:
        return jsonify({"message": "tokenがありません。"}), 400

    student_data = db.collection("teacher").document(uuid).get()
    if token != student_data.get("token"):
        return jsonify({"message": "アクセスが拒否されました。"}), 401

    student = request.get_json()
    get_pre_password = student.get("pre_password")
    if get_pre_password == None:
        return jsonify({"message": "pre_passwordがありません。"}), 400

    get_b_pre_password = bytes(get_pre_password, "UTF-8")
    student_data = db.collection("student").document(uuid).get()
    student_pre_password = student_data.get("password_hash")
    if not (bcrypt.checkpw(get_b_pre_password, student_pre_password)):
        return jsonify({"message": "間違ったパスワード"}), 400

    new_password = student.get("new_password")
    if new_password == None:
        return jsonify({"message": "new_passwordがありません。"}), 400

    b_password = bytes(new_password, "utf-8")
    salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
    hash_password = bcrypt.hashpw(b_password, salt)
    db.collection("student").document(uuid).update(
        {
            "password_hash": hash_password,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return jsonify({"message": "success"}), 200


@app.route("/student/forget/", methods=["POST"])
def student_forget():
    request_json = request.get_json()
    student_email = request_json.get("email")
    if student_email == None:
        return jsonify({"message": "emailがありません。"}), 400

    all_student_data = db.collection("student").stream()
    for student_data in all_student_data:
        if student_data.get("email") == student_email:
            break
    else:
        return jsonify({"message": "間違ったメールアドレス"}), 400

    secret = str(uuid.uuid4())
    db.collection("student").document(student_data.get("uuid")).update(
        {"updated_at": firestore.SERVER_TIMESTAMP}
    )
    expired = (
        db.collection("student")
        .document(student_data.get("uuid"))
        .get()
        .get("updated_at")
        .replace(tzinfo=None)
    )
    expired = expired + timedelta(minutes=10)
    db.collection("student").document(student_data.get("uuid")).update(
        {
            "secret": {"secret": secret, "expired_at": expired},
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    url = "https://student/forget/:uuid?secret=" + secret
    # requests.post(url,headers="Content-Type: application/json",json={"body":"ボディ","email":student_email,"subject":"パスワード変更"})
    return jsonify({"message": "success"}), 200


@app.route("/student/<string:uuid>/forget_password/", methods=["POST"])
def student_forget_password(uuid):
    request_json = request.get_json()
    request_secret = request_json.get("secret")
    if request_secret == None:
        return jsonify({"message": "secretがありません。"}), 400

    student_secret = db.collection("student").document(uuid).get().get("secret")
    secret_secret = student_secret.get("secret")
    if request_secret != secret_secret:
        return jsonify({"message": "間違ったsecret"}), 400

    now = datetime.now()
    teacher_expired = student_secret.get("expired_at")
    expired_datetime = datetime.fromtimestamp(teacher_expired.timestamp())
    sub_time = expired_datetime - now
    if sub_time.total_seconds() < 0:
        return jsonify({"message": "期限切れのsecret"}), 400

    request_password = request_json.get("password")
    if request_password == None:
        return jsonify({"message": "passwordがありません。"}), 400

    b_password = bytes(request_password, "utf-8")
    salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
    hash_password = bcrypt.hashpw(b_password, salt)
    db.collection("student").document(uuid).update(
        {
            "password_hash": hash_password,
            "updated_at": firestore.SERVER_TIMESTAMP,
            "token": firestore.DELETE_FIELD,
            "secret": firestore.DELETE_FIELD,
        }
    )
    return jsonify({"message": "success"}), 200


# subject側POST
@app.route("/subject/<string:uuid>/add_student/", methods=["POST"])
def add_student(uuid):
    request_json = request.get_json()
    student_uuid = request_json.get("student")
    if student_uuid == None:
        return jsonify({"message": "studentがありません。"}), 400

    db.collection("student").document(student_uuid).update(
        {
            "subject": firestore.ArrayUnion([{"uuid": uuid}]),
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return jsonify({"message": "success"}), 200


@app.route("/subject/<string:uuid>/delete_students/", methods=["POST"])
def delete_students(uuid):
    request_json = request.get_json()
    student_uuid_list = request_json.get("student")
    if student_uuid_list == None:
        return jsonify({"message": "studentがありません。"}), 400

    for student_uuid in student_uuid_list:
        db.collection("student").document(student_uuid).update(
            {
                "subject": firestore.ArrayRemove([{"uuid": uuid}]),
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
        )
    return jsonify({"message": "success"}), 200


@app.route("/subject/<string:uuid>/change_invitation/", methods=["POST"])
def change_invitation(uuid):
    request_json = request.get_json()
    pre_invitation = request_json.get("pre_invitation")
    if pre_invitation == None:
        return jsonify({"message": "pre_invitationがありません。"}), 400

    subject_data = db.collection("subject").document(uuid).get()
    if subject_data.get("invitation") != pre_invitation:
        return jsonify({"message": "間違ったinvitation"}), 400

    new_invitation = invitation.create_inv(1)
    db.collection("subject").document(uuid).update({"invitation": new_invitation})
    return jsonify({"message": "success", "new_invitation": new_invitation}), 200


# machine側POST
@app.route("/machine/", methods=["POST"])
def change_status():
    machine_id = request.headers.get("machine_ID")
    if machine_id == None:
        return jsonify({"message": "machine_IDがありません。"}), 400

    all_teacher_data = db.collection("teacher").stream()
    for teacher_data in all_teacher_data:
        if teacher_data.get("machine_id") == machine_id:
            break
    else:
        return jsonify({"message": "間違ったid"}), 400

    json_data = request.get_json()
    now_status = json_data.get("status")
    if now_status == None:
        return jsonify({"message": "statusがありません。"}), 400

    teacher_id = teacher_data.get("uuid")
    db.collection("teacher").document(teacher_id).update(
        {
            "status": now_status,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return jsonify({"message": "success"}), 200


# run the app.
if __name__ == "__main__":
    app.debug = True
    app.run(port=5000)
