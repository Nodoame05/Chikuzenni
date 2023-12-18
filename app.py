from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import pyrebase, json, os, firebase_admin, uuid
from firebase_admin import credentials, firestore, auth
from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout
from datetime import date, datetime

app = Flask(__name__)

os.environ["FB_TYPE"] = "service_account"
os.environ["FB_PROJECt_ID"] = "tikuzenni-abec3"
os.environ["FB_PRIVATE_KEY"] = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDP9/Oa4qoZNqDS\njaymO998rWktLki6ryhnNHGHVcqEladEfVtEEnGYghhJBwMb/vIfIhnYr1iGm8F1\n9aT0dqmhPC25ZluYceYuXVBg6k8da7uUTP3P2rTPOKRjZlXkYq/pM3hPzoxtu4pf\nZ38q0lwwfKEGSLEby4nZIh2hVZlePpNuGacVnbv1E3aYy73gkwLq8y6I0ldXUbUR\nj17ezYLUc14YkuHI9kVChvJe/CJ7/YoKxYmtZPE0E11DcSqMchl5uvr/u3wx22eS\njGFKoYXM7LLjKl4pQx/OfdZGDH7qOuXRIUxy9hCCnfM+Oul/FK8fHaj5NpLwMhMl\neAzR5MFnAgMBAAECggEAHGkaHWmjpSgiVkFGebsqL8Uc3jA5fU9abKbsb3mX3f73\nx9J8OlNus0/qc2eC1DtC5l/pOgHSTSlQB4ZUT5U6XS10baR/FNdSg7j5txOrVTCX\ngo32CoQtOTXatz2OtFGLCIeggv6Ljp4VLC1eYQI11+XetZYOo+ZtYX1YoOapugcB\nGJg0NwRAhDe0ZIJ6o/FKO+5Em/EEJ9qVp2L2uYLDe2JSkuGb2adNiXI9fPZbwM1F\nGXesXNptU7WwlLgA842Hm0MfoVb24uRkCMSk7QVUqOO8DanXpVG90CEu7KOSwgza\n8enTOT6TQGAezp3f0m535urGs1d5uw3dv7yhJOl68QKBgQD9fE0cgi+5DUx2o7+e\nc+2pQgxJQ+CD6KGICTAklbhbEv9gsEYik2YYjLjsGO7FKVVi6pDNAyWMPJ3t1Zdg\nEQRx2mZSo9LsrYUQFqWXEQad0LJVgrgG7TTFJ9ZEguKHsmyC5Opr2Og5qD9C0yF1\nPtsad15gyizj2nDBrLMhcTruiQKBgQDSCBCg5r0WIrPpDCegK4o1rriARSfO48Is\n602VB02SLW3B9IS2bGbSlvyxAFD/N1lhPGCay4IZN8QArHukHzpwU/caF37B2Jhd\n6b1H0YQ2PXe6hhuMwevHzA4piwx5Yzj770B7Htlpp6JHkpFkdVgGBL5KyEuefEZ8\nLHEOrOe0bwKBgGJU6NjpS7f+h63yQbAnCofBPmDheuPQx3CtF8bpaZWy3exVFS/u\nfAmD9WxpE57aNOxlT/ynftZS4XTUiZ9TmqTL8yuVr4numhKuplfe2/E2dyeiyN6u\n/+yHUqBLIbNALMXuJV3my9cqBDhZDL6dvoMa0Tq80wMkxt7qrqaHdTP5AoGBAIxp\nMdyvhPeYaZhCNPeCRBqRXOz7zpokb3qiMDKSOEyiLD8/Hb3rCG5+3B3krUGBmjJE\nL/0sUiRTwKgGp33YFrRjnc2GqYokJ/CYw56Qtgeg3jsHTsGyHtNqWolxWPyJ1d2v\nW/czb3uPwxCALszvGdKkNyc9cjhYsrJu74I1G43nAoGBAMHKioy4mAn782SwhGiJ\njPawXstquE33gnH1hXnXnNypxmVrzfH/I4KTTce+G/stIYaKDEz21N6W89hGQfv7\nWwxpNQXy8CwYbAe0lPSyGqZF52BYJD4ZNu31ffAgB4aH45aSdVSTZbE6ugceZ5vu\nl+XU8Q6CMHXlickgrGMbLFax\n-----END PRIVATE KEY-----\n"
os.environ["FB_CLIENT_EMAIL"] = "firebase-adminsdk-djqvj@tikuzenni-abec3.iam.gserviceaccount.com"
os.environ["FB_TOKEN_URI"] = "https://oauth2.googleapis.com/token"
os.environ["FB_APIKEY"] = "AIzaSyBuqPOtJLdDusfyE__R-JtuYFDEQmT6RuU"
os.environ["FB_AUTH_DOMAIN"] = "tikuzenni-abec3.firebaseapp.com"
os.environ["FB_STORAGE_BUCKET"] = "tikuzenni-abec3.appspot.com"
os.environ["FB_MESSAGING_SENDER_ID"] = "72812691936"
os.environ["FB_APP_ID"] = "1:72812691936:web:ee07eb7ba8ba5bc0ad2b85"
os.environ["FB_DATABASE_URL"] = "https://tikuzenni-abec3-default-rtdb.firebaseio.com"

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

#student側POST

# run the app.
if __name__ == "__main__":
    app.debug = True
    app.run(port=5000)
