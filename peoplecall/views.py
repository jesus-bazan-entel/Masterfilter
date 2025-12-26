from django.shortcuts import render, redirect, HttpResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
import json
import pandas as pd
import requests
from .models import *
from movil.models import *
from threading import Thread
from datetime import datetime as dt
import logging
from time import sleep
# Create your views here.

_logging = logging.basicConfig(filename="logger.log", level=logging.INFO)

def peoplecall(request):
    if request.user.is_authenticated:
        #return redirect("abct")
        endp = EndPoint.objects.all().first()
        perm = Permision.objects.filter(user=request.user).first()
        if not perm.peoplecall:
            return redirect("fijo")
        doc = Document.objects.filter(user=request.user).last()
        total = 0
        name = ""
        if doc:
            total = doc.total
            name = str(doc.file)
        return render(request, "peoplecall.html",{
                    "segment":"peoplecall", 
                    "subido": total, 
                    "endpoint": endp, 
                    "perm": perm, 
                    "name":name
                })
    else:
        return redirect("login")

def reanude(request):
    cons = Consecutive.objects.filter(pk = request.POST["pk"]).first()
    data = read_file(cons.document.file.url)
    if len(Consecutive.objects.filter(user = request.user, active=True)) + 1 <= 3:
        pro_file(cons, data)
    return redirect("peoplecall")

def upload(request):
    try:
        doc = Document.objects.create(
            file = request.FILES["file"],
            user = request.user
        )
        data = read_file(doc.file.url)
        if len(data) <= 10000:
            cons = Consecutive.objects.create(
                active = False,
                finish = False,
                file = str(doc.file.url),
                total = len(data),
                progres = 0,
                created = dt.now(),
                num = 0,
                user = request.user,
                document = doc
            )
            if len(Consecutive.objects.filter(user = request.user, active=True)) + 1 <= 3:
                pro_file(cons, data)
    except Exception as e:
        logging.info(f"Error upload: {e}")
    return redirect("peoplecall")

def pro_file(cons:Consecutive, data):
    result = {
        "code": 400,
        "status": "Fail",
        "message": ""
    }
    if not cons.active:
        Thread(target=active_process, args=(data,cons)).start()
        result["code"] = 200
        result["status"] = "OK"
        result["message"] = "Proceso activado."
    else:
        result["message"] = "Proceso ya estaba activado."
    
    return result

def read_file(file):
    df = pd.read_excel(file[1:], sheet_name='Hoja1')
    df.describe()
    documents = df['numeros'].tolist()
    return documents

def export(request):
    if request.user.is_authenticated:
        data = request.POST["data"]
        #print(request.POST["data"])
        #print(request.POST["nameFile"])
        data_all = {
            "phone":[], 
            "originalOperator":[], 
            "originalOperatorRaw":[], 
            "currentOperator":[], 
            "currentOperatorRaw":[], 
            "prefix":[],
            "type_p":[],
            "typeDescription":[],
            "when_p":[],
            "from_p":[],
            "fromRaw_p":[],
            "to_p":[],
            "toRaw_p":[]
        }
        
        df = pd.DataFrame()
        #file = "media/" + request.POST["nameFile"]
        #df = pd.read_excel(file, sheet_name='Hoja1')
        data = json.loads(data)["data"]["list"]
        for d in data:
            data_all["phone"].append(d["phone"])
            data_all["originalOperator"].append(d["originalOperator"])
            data_all["originalOperatorRaw"].append(d["originalOperatorRaw"])
            data_all["currentOperator"].append(d["currentOperator"])
            data_all["currentOperatorRaw"].append(d["currentOperatorRaw"])
            data_all["prefix"].append(d["prefix"])
            data_all["type_p"].append(d["type_p"])
            data_all["typeDescription"].append(d["typeDescription"])
            data_all["when_p"].append(d["when_p"])
            data_all["from_p"].append(d["from_p"])
            data_all["fromRaw_p"].append(d["fromRaw_p"])
            data_all["to_p"].append(d["to_p"])
            data_all["toRaw_p"].append(d["toRaw_p"])

        df["phone"] = data_all["phone"]
        df["originalOperator"] = data_all["originalOperator"]
        df["originalOperatorRaw"] = data_all["originalOperatorRaw"]
        df["currentOperator"] = data_all["currentOperator"]
        df["currentOperatorRaw"] = data_all["currentOperatorRaw"]
        df["prefix"] = data_all["prefix"]
        df["type_p"] = data_all["type_p"]
        df["typeDescription"] = data_all["typeDescription"]
        df["when_p"] = data_all["when_p"]
        df["from_p"] = data_all["from_p"]
        df["fromRaw_p"] = data_all["fromRaw_p"]
        df["to_p"] = data_all["to_p"]
        df["toRaw_p"] = data_all["toRaw_p"]

        try:
            df.to_excel("media/proces/"+str(request.user.username)+".xlsx")
        except Exception as e:
            logging.info(f"Error export: {e}")
        message = "Procesado correctamente"
        return HttpResponse(json.dumps({"message": message, "file": str(request.user.username)+".xlsx", "path": "media/proces/"+str(request.user.username)+".xlsx"}))
    else:
        return redirect("login")

def active_process(data, cons:Consecutive):
    cons.active = True
    cons.save()
    key = ApiKey.objects.all().last()
    headers = {
        "x-api-key": key.key,  # Reemplaza <apikey> con tu clave real
    }
    progres = cons.progres
    logging.info(f"Progreso: {progres} - Total para filtrar: {len(data)}")
    for d in data[progres:len(data)]:
        try:
            cons = Consecutive.objects.filter(pk = cons.pk).first()
            if not cons.active:
                break
            url = f"https://numclass-api.nubefone.com/v2/numbers/{d}"
            response = requests.get(url, headers=headers)
            logging.info(f"User: {cons.user} - Consulta: {d} - Status: {response.status_code}, Response JSON: {response.json()}")  # O .text si no es JSON
            resp = response.json()
            if "Consultas agotadas" in str(resp):
                logging.info(f"User: {cons.user} - Deteniendo proceso, Consultas agotadas")
                break
            PhoneNumber.objects.create(
                phone = resp["number"] if "error" not in resp else resp["issued"],
                originalOperator = resp["originalOperator"] if "error" not in resp else resp["errorMessage"],
                originalOperatorRaw = resp["originalOperatorRaw"] if "error" not in resp else resp["errorMessage"],
                currentOperator = resp["currentOperator"] if "error" not in resp else resp["errorMessage"],
                currentOperatorRaw = resp["currentOperatorRaw"] if "error" not in resp else resp["errorMessage"],
                prefix = resp["prefix"] if "error" not in resp else resp["errorMessage"],
                type_p = resp["type"] if "error" not in resp else resp["errorMessage"],
                typeDescription = resp["typeDescription"] if "error" not in resp else resp["errorMessage"],
                user = cons.user,
                consecutive = cons,
                fecha_hora = dt.now(),
                when_p = resp["lastPortability"]["when"] if "lastPortability" in resp else "",
                from_p = resp["lastPortability"]["from"] if "lastPortability" in resp else "",
                fromRaw_p = resp["lastPortability"]["fromRaw"] if "lastPortability" in resp else "",
                to_p = resp["lastPortability"]["to"] if "lastPortability" in resp else "",
                toRaw_p = resp["lastPortability"]["toRaw"] if "lastPortability" in resp else ""
            )
            cons.progres += 1
            cons.save()
            key.queriesLeft = resp["queriesLeft"] if "queriesLeft" in resp else key.queriesLeft - 1
            key.save()
            sleep(1)
        except Exception as e:
            logging.info(f"Error get phone: {e}")

    cons.active = False
    if cons.total <= cons.progres:
        cons.finish = True
    cons.save()

def change_status_consecutive():
    for c in Consecutive.objects.all():
        c.active = False
        c.save()

Thread(target=change_status_consecutive).start()

# no es necesaria, queda obsoleta.
@api_view(["POST"])
def process(request):
    result = {
        "code": 400,
        "status": "Fail",
        "message": ""
    }
    data = request.data
    user = User.objects.filter(username=data["user"]).first()
    c = Consecutive.objects.filter(pk = data["pk"]).first()
    if not c.active:
        Thread(target=active_process, args=(data,)).start()
        result["code"] = 200
        result["status"] = "OK"
        result["message"] = "Proceso activado."
    else:
        result["message"] = "Proceso ya estaba activado."

    return Response(result)

@api_view(["POST"])
def pause(request):
    data = request.data
    result = {
        "code": 400,
        "status": "Fail",
        "message": "No encontrado"
    }
    qs_conse = Consecutive.objects.filter(pk=data["pk"])
    for obj in qs_conse:
        obj.active = False
        obj.save()
        result["code"] = 200
        result["status"] = "OK"
        result["message"] = "Proceso pausado"

    return Response(result)

@api_view(["POST"])
def remove(request):
    data = request.data
    user = User.objects.filter(username=data["user"]).first()
    if user is None:
        user = User.objects.create(username=data["user"])
    c = Consecutive.objects.filter(id=data["id"]).last()
    result = {
        "code": 400,
        "status": "Fail",
        "message": "No encontrado"
    }
    if c:
        result["code"] = 200
        result["status"] = "OK"
        result["message"] = "Base eliminada correctamente"
        c.delete()

    return Response(result)

@api_view(["POST"])
def consult(request):
    data = request.data
    user = User.objects.filter(username=data["user"]).first()
    if user is None:
        user = User.objects.create(username=data["user"])
    c = Consecutive.objects.filter(id=data["id"]).last()
    result = {
        "code": 400,
        "status": "Fail",
        "message": "No encontrado",
        "nameFile": "",
        "data": {}
    }
    if c:
        data = []
        for i in PhoneNumber.objects.filter(consecutive=c).all().order_by("id"):
            data.append({
                "phone":i.phone,
                "originalOperator":i.originalOperator,
                "originalOperatorRaw":i.originalOperatorRaw,
                "currentOperator":i.currentOperator,
                "currentOperatorRaw":i.currentOperatorRaw,
                "prefix":i.prefix,
                "type_p":i.type_p,
                "typeDescription":i.typeDescription,
                "when_p":i.when_p,
                "from_p":i.from_p,
                "fromRaw_p":i.fromRaw_p,
                "to_p":i.to_p,
                "toRaw_p":i.toRaw_p
            })
        total = PhoneNumber.objects.filter(user=user).count()
        result["code"] = 200
        result["status"] = "OK"
        result["message"] = "Proceso pausado"
        result["nameFile"] = c.file
        result["data"] = {"total": total, "proces": c.progres, "subido": c.total, "list":data}
    return Response(result)

@api_view(["POST"])
def filter_data(request):
    data = request.data
    user = User.objects.filter(username=data["user"]).first()
    if user is None:
        user = User.objects.create(username=data["user"])
    c = Consecutive.objects.filter(user=user).order_by("-id")
    data = []
    for i in c:
        data.append({
            "id": i.pk,
            "file": i.file,
            "total": i.total,
            "progres": i.progres,
            "conse": i.num,
            "created": i.created,
            "finish": i.finish,
            "active": i.active
        })
    return Response({"data": data})