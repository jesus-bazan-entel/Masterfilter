from django.shortcuts import render, redirect, HttpResponse
import json
import pandas as pd
import requests
from movil.models import *

# Create your views here.
def fijo(request):
    print("FIJO-Sam-Bazan")
    if request.user.is_authenticated:
        #return redirect("abct")
        endp = EndPoint.objects.all().first()
        perm = Permision.objects.filter(user=request.user).first()
        if perm.fijo:
            doc = Document.objects.filter(user=request.user).last()
            total = 0
            name = ""
            if doc:
                total = doc.total
                name = str(doc.file)
            return render(request, "fijo.html",{
                        "segment":"fijo", 
                        "subido": total, 
                        "endpoint": endp, 
                        "perm": perm, 
                        "name":name
                    })
        else:
            if perm.peoplecall:
                return redirect("peoplecall")
            elif perm.amarilla:
                return redirect("arles")
            elif perm.abct:
                return redirect("atreyus")
            elif perm.infobel:
                return redirect("infolfull")
            elif perm.orange1:
                return redirect("orange1")
            elif perm.orange2:
                return redirect("orange2")
            else:
                redirect("logout")
    else:
        return redirect("login")

def reanude(request):
    doc = Document.objects.filter(user=request.user)
    for d in doc:
        if str(d.file).split("/")[1] == request.POST["file"]:
            pro_file(d, request, False)
            break
    return redirect("fijo")

def upload(request):
    print("FIJO-views-upload")
    try:
        doc = Document.objects.create(
            file = request.FILES["file"],
            user = request.user
        )
        pro_file(doc, request, True)
    except:
        pass
    return redirect("fijo")

def pro_file(doc, request, op):
    print("FIJO-views-pro_file")
    name_file = str(doc.file).split("/")[1]
    print(f"FIJO-views-pro_file {name_file}")
    data = read_file(name_file)
    doc.save()
    send_data(request.user.username, data, op, name_file)

def read_file(name_file):
    name_file = name_file.replace(" ", "_")
    file = "media/subido/" + name_file
    df = pd.read_excel(file, sheet_name='Hoja1')
    df.describe()
    documents = df['numeros'].tolist()
    #print(documents)
    return documents

def export(request):
    if request.user.is_authenticated:
        #print(request.POST)
        data = request.POST["data"]
        #print(request.POST["data"])
        #print(request.POST["nameFile"])
        #data_all = {"number":[], "operator":[]}
        #df = pd.DataFrame()
        name_file = json.loads(data)["nameFile"]
        data = json.loads(data)["data"]["list"]
        print(name_file)
        file = "media/subido/" + name_file
        df = pd.read_excel(file, sheet_name='Hoja1')
        df['operador'] = pd.NA
        #print(df)
        for d in data:
            #print(d)
            df.loc[df['numeros'] == int(d['number']), 'operador'] = d["operator"]
            #data_all["operator"].append(d["operator"])
            #data_all["number"].append(d["number"])

        try:
            df.to_excel("media/proces/"+name_file)
        except Exception as e:
            print("Error: "+str(e))
        message = "Procesado correctamente"
        return HttpResponse(json.dumps({
            "message": message, 
            #"file": str(request.user.username)+".xlsx", 
            "file": name_file,
            "path": "media/proces/"+name_file
        }))
    else:
        return redirect("login")

def send_data(user, data, op, name_file):
    print("FIJO-views-send_data")
    #url = "http://127.0.0.1:8088/process/"
    url = "http://185.47.131.53:5500/process/"
    payload = json.dumps({
        "user": user,
        "number": data,
        "new":op,
        "file": name_file
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)