from flask import Flask, request, jsonify
import pyrebase, os, firebase_admin, uuid, bcrypt, re, invitation
from firebase_admin import credentials, firestore
app = Flask(__name__)

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
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    status = teacher_data.get("status")
    status_list = teacher_data.get("status_list")
    now_status = status_list[status]
    return jsonify({"status":now_status})

@app.route("/teacher/<string:uuid>/statuses", methods=["GET"])
def teacher_statuses(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    return jsonify({"statuses":teacher_data.get("status_list")})


@app.route("/teacher/<string:uuid>/subjects", methods=["GET"])
def teacher_subjects(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    all_subject_data = db.collection("subject").stream()
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    uuid_list = []
    response = []
    teacher_subject_list = teacher_data.get("subject")
    for teacher_subject_uuid in teacher_subject_list:
        uuid_list.append(teacher_subject_uuid.get("uuid"))
    for subject_data in all_subject_data:
        for uuid in uuid_list:
            if subject_data.get("uuid") == uuid:
                response.append({"name":subject_data.get("name"),"uuid":subject_data.get("uuid"),"invitation":subject_data.get("invitation")})
    return response


@app.route("/teacher/<string:uuid>/names", methods=["GET"])
def teacher_all(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    return jsonify({"name":teacher_data.get("name"),"email":teacher_data.get("email")})


@app.route("/Machine/<string:uuid>", methods=["GET"])
def machine_id(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    return jsonify({"id":teacher_data.get("machine_id")})


#student側GET
@app.route("/student/<string:uuid>/teacherlist/", methods=["GET"])
def teacher_list(uuid):
    token = request.headers.get("token")
    student_data = db.collection("student").document(uuid).get()
    if token != student_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
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
                    response.append({"name":teacher_data.get("name"),"uuid":teacher_data.get("uuid"),"status":now_status})
    return response


@app.route("/student/<string:uuid>", methods=["GET"])
def student_all(uuid):
    token = request.headers.get("token")
    student_data = db.collection("student").document(uuid).get()
    if token != student_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    return jsonify({"name":student_data.get("name"),"email":student_data.get("email")})


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
            break
        else:
            return jsonify({"message":"アクセスが拒否されました。"}),403
    response = []
    all_student_data = db.collection("student").stream()
    for student_data in all_student_data:
        subject_list = student_data.get("subject")
        for subject_map in subject_list:
                if uuid == subject_map.get("uuid"):
                    response.append({"doc_id":student_data.id,"name":student_data.get("name"),"uuid":student_data.get("uuid")})
    return response
    

#machine側GET
@app.route("/machine", methods=["GET"])
def now_status():
    machine_id = request.headers.get("machine_ID")
    all_teacher_data = db.collection("teacher").stream()
    for teacher_data in all_teacher_data:
        if teacher_data.get("machine_id") == machine_id:
            return jsonify({"status":teacher_data.get("status")})
    return jsonify({"message":"間違ったid"})


#teacher側POST
@app.route("/teacher/signup", methods=["POST"])
def teacher_signup():
    teacher = request.get_json()
    teacher_name = teacher.get("name")
    machine_id = teacher.get("machine")
    teacher_email = teacher.get("email")
    #正規表現
    pattern = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.fullmatch(pattern,teacher_email):
        return  jsonify({"message":"間違ったメールアドレス形式"}),406
    teacher_uuid = str(uuid.uuid4())
    teacher_password = teacher.get("password")
    b_password = bytes(teacher_password,"utf-8")
    salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
    hash_password = bcrypt.hashpw(b_password,salt)
    db.collection("teacher").document(teacher_uuid).set({
        "available":False,
        "email":teacher_email,
        "machine_id":machine_id,
        "name":teacher_name,
        "password_hash":hash_password,
        "status":1,
        "status_list":["在室","不在"],
        "subject":[],
        "uuid":teacher_uuid,
        "created_at":firestore.SERVER_TIMESTAMP,
    })
    #requests.post("https://script.google.com/macros/s/AKfycby4a8UMh_gJZuO2I10zAK2_q2AUoAfuhGJxJS8ZrD_8AkAbd9TarFjd9jqsL1geryk/exec",headers="Content-Type: application/json",json={"body":"ボディ","email":teacher_email,"subject":"メールアドレス認証"})
    return jsonify({"message":"success","email":teacher_email}),200
    
    
@app.route("/teacher/login", methods=["POST"])
def teacher_login():
    #データの読み込み
    teacher = request.get_json()
    teacher_email = teacher.get("email")
    teacher_password = bytes(teacher.get("password"),'UTF-8')
    all_teacher_data = db.collection("teacher").stream()

    #アカウント検索
    for teacher_data in all_teacher_data:
        if teacher_data.get("email") == teacher_email:
            break
    else:
        return jsonify({"message":"間違ったメールアドレス"})
    
    #アカウントデータの整理
    hash_password = teacher_data.get("password_hash")
    teacher_available = teacher_data.get("available")

    #有効アカウントでなかったらエラー
    if not(teacher_available):
        return jsonify({"message":"認証の通っていないメールアドレス"})

    #パスワードが間違っていたらエラー
    if not(bcrypt.checkpw(teacher_password,hash_password)):
        return jsonify({"message":"間違ったパスワード"})

    #全認証クリア時：トークン発行
    teacher_token = str(uuid.uuid4())
    db.collection("teacher").document(teacher_data.get("uuid")).update({
        "token":teacher_token,
        "updated_at":firestore.SERVER_TIMESTAMP,
    })

    return jsonify({"message":"success","token":teacher_token,"uuid":teacher_data.get("uuid")})


# @app.route("teacher/forget", methods=["POST"])



@app.route("/teacher/<string:uuid>/status/current", methods=["POST"])
def change_current_status(uuid):
    status = request.get_json()
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    db.collection("teacher").document(uuid).update({
        "status":status.get("status"),
        "updated_at":firestore.SERVER_TIMESTAMP
    })
    return jsonify({"message":"success"})
    
    
@app.route("/teacher/<string:uuid>/status/names", methods=["POST"])
def change_status_names(uuid):
    teacher_status_list = request.get_json()
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    db.collection("teacher").document(uuid).update({
        "status_list":firestore.DELETE_FIELD
    })
    db.collection("teacher").document(uuid).update({
        "status_list":firestore.ArrayUnion([
            "在室",
            "不在",
            teacher_status_list.get("3"),
            teacher_status_list.get("4"),
            teacher_status_list.get("5"),
        ]),
        "updated_at":firestore.SERVER_TIMESTAMP,
    })
    return jsonify({"message":"success"})


@app.route("/teacher/<string:t_uuid>/create_subject", methods=["POST"])
def create_subject(t_uuid):
    subject_name =  request.get_json()
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(t_uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    subject_uuid = str(uuid.uuid4())
    db.collection("subject").document(subject_uuid).set({
        "name":subject_name.get("name"),
        "invitation":invitation.create_inv(1),
        "uuid":subject_uuid
    })
    db.collection("teacher").document(t_uuid).update({
        "subject":firestore.ArrayUnion([{
           "uuid":subject_uuid 
        }]),
        "updated_at":firestore.SERVER_TIMESTAMP,
    })
    return jsonify({"massage":"success"})
    
    
@app.route("/teacher/<string:uuid>/delete_subject", methods=["POST"])
def delete_subject(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    subject = request.get_json()
    subject_uuid = subject.get("subject_uuid")
    db.collection("subject").document(subject_uuid).delete()
    db.collection("teacher").document(uuid).update({
        "subject":firestore.ArrayRemove([{
            "uuid":subject_uuid
        }])
    })
    all_student_data = db.collection("student").stream()
    for student_data in all_student_data:
        student_subject = student_data.get("subject")
        for student_subject_map in  student_subject:
            if student_subject_map.get("uuid") == subject_uuid:
                db.collection("student").document(student_data.get("uuid")).update({
                    "subject":firestore.ArrayRemove([{
                        "uuid":subject_uuid
                    }])
                })
    return jsonify({"message":"success"})


@app.route("/teacher/<string:uuid>/setting/name/", methods=["POST"])
def setting_teacher_name(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    teacher = request.get_json()
    teacher_name = teacher.get("name")
    db.collection("teacher").document(uuid).update({
        "name":teacher_name,
        "updated_at":firestore.SERVER_TIMESTAMP,
    })
    return jsonify({"message":"success"})


@app.route("/teacher/<string:uuid>/setting/machine/", methods=["POST"])
def setting_machine(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    teacher = request.get_json()
    machine_id = teacher.get("machine")
    db.collection("teacher").document(uuid).update({
        "machine_id":machine_id,
        "updated_at":firestore.SERVER_TIMESTAMP,
    })
    return jsonify({"message":"success"})


@app.route("/teacher/<string:uuid>/setting/password/", methods=["POST"])
def setting_teacher_password(uuid):
    token = request.headers.get("token")
    teacher_data = db.collection("teacher").document(uuid).get()
    if token != teacher_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    teacher = request.get_json()
    get_pre_password = bytes(teacher.get("pre_password"),'UTF-8')
    teacher_data = db.collection("teacher").document(uuid).get()
    teacher_pre_password = teacher_data.get("password_hash")
    if not(bcrypt.checkpw(get_pre_password,teacher_pre_password)):
        return jsonify({"message":"間違ったパスワード"})
    new_password = teacher.get("new_password")
    b_password = bytes(new_password,"utf-8")
    salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
    hash_password = bcrypt.hashpw(b_password,salt)
    db.collection("teacher").document(uuid).update({
        "password_hash":hash_password,
        "updated_at":firestore.SERVER_TIMESTAMP,
    })
    return jsonify({"message":"success"})


# @app.route("/teacher/<string:uuid>/forget_password", methods=["POST"])

 
# #student側POST
@app.route("/student/<string:uuid>/setting/name/", methods=["POST"])
def setting_student_name(uuid):
    token = request.headers.get("token")
    student_data = db.collection("student").document(uuid).get()
    if token != student_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    student = request.get_json()
    student_name = student.get("name")
    db.collection("student").document(uuid).update({
        "name":student_name,
        "updated_at":firestore.SERVER_TIMESTAMP,
    })
    return jsonify({"message":"success"})


@app.route("/student/<string:uuid>/setting/password/", methods=["POST"])
def setting_student_password(uuid):
    token = request.headers.get("token")
    student_data = db.collection("teacher").document(uuid).get()
    if token != student_data.get("token"):
        return jsonify({"message":"アクセスが拒否されました。"}),403
    student = request.get_json()
    get_pre_password = bytes(student.get("pre_password"),'UTF-8')
    student_data = db.collection("student").document(uuid).get()
    student_pre_password = student_data.get("password_hash")
    if not(bcrypt.checkpw(get_pre_password,student_pre_password)):
        return jsonify({"message":"間違ったパスワード"})
    new_password = student.get("new_password")
    b_password = bytes(new_password,"utf-8")
    salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
    hash_password = bcrypt.hashpw(b_password,salt)
    db.collection("student").document(uuid).update({
        "password_hash":hash_password,
        "updated_at":firestore.SERVER_TIMESTAMP,
    })
    return jsonify({"message":"success"})


# @app.route("/student/<string:uuid>/forget_password", methods=["POST"])

# @app.route("student/forget", methods=["POST"])


# subject側POST
# @app.route("/subject/<string:uuid>/add_student", methods=["POST"])

# @app.route("/subject/<string:uuid>/delete_student", methods=["POST"])

# @app.route("/subject/<string:uuid>/change_invitation", methods=["POST"])


#machine側POST
@app.route("/machine/", methods=["POST"])
def change_status():
    machine_id = request.headers.get("machine_ID")
    all_teacher_data = db.collection("teacher").stream()
    for teacher_data in all_teacher_data:
        if teacher_data.get("machine_id") == machine_id:
            json_data = request.get_json()
            now_status = json_data.get("status")
            teacher_id = teacher_data.get("uuid")
            db.collection("teacher").document(teacher_id).update({
                "status":now_status
            })
            return jsonify({"message":"success"})
    return jsonify({"message":"間違ったid"})   



# run the app.
if __name__ == "__main__":
    app.debug = True
    app.run(port=5000)
