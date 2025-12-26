from django.shortcuts import render, redirect, HttpResponse
import json
import pandas as pd
import requests
from movil.models import *

# Create your views here.
def abct(request):
    if request.user.is_authenticated:
        endp = EndPoint.objects.all().first()
        perm = Permision.objects.filter(user=request.user).first()
        if not perm.abct:
            return redirect("fijo") 
        doc = Document.objects.filter(user=request.user).last()
        total = 0
        name = ""
        if doc:
            total = doc.total
            name = str(doc.file)
        return render(request, "abct.html",{
                    "segment":"abct", 
                    "subido": total, 
                    "endpoint": endp, 
                    "perm": perm, 
                    "name":name
                })
    else:
        return redirect("login")

def reanude(request):
    doc = Document.objects.filter(user=request.user)
    for d in doc:
        if str(d.file).split("/")[1] == request.POST["file"]:
            pro_file(d, request, False)
            break
    return redirect("abct")

def upload(request):
    print("SAM")
    try:
        doc = Document.objects.create(
            file = request.FILES["file"],
            user = request.user
        )
        pro_file(doc, request, True)
    except:
        pass
    return redirect("abct")

def pro_file(doc, request, op):
    name_file = str(doc.file).split("/")[1]
    data = read_file(name_file)
    doc.save()
    send_data(request.user.username, data, op, name_file)

def read_file(name_file):
	name_file = name_file.replace(" ", "_")
	file = "media/subido/" + name_file
	df = pd.read_excel(file, sheet_name='Hoja1')
	df.describe()
	documents = df['numeros'].tolist()
	return documents

def export(request):
    if request.user.is_authenticated:
        data = json.loads(request.POST["data"])["data"]
        #print(data)
        data_all = {"name":[], "telephone":[], "streetAddress":[], "addressLocality":[], "addressCountry":[]}
        df = pd.DataFrame()
        for d in data:
            data_all["name"].append(d["name"])
            data_all["telephone"].append(d["telephone"])
            data_all["streetAddress"].append(d["streetAddress"])
            data_all["addressLocality"].append(d["addressLocality"])
            data_all["addressCountry"].append(d["addressCountry"])

        df["name"] = data_all["name"]
        df["telephone"] = data_all["telephone"]
        df["streetAddress"] = data_all["streetAddress"]
        df["addressLocality"] = data_all["addressLocality"]
        df["addressCountry"] = data_all["addressCountry"]

        try:
            df.to_excel("media/proces/"+str(request.user.username)+".xlsx")
        except Exception as e:
            print("Error: "+str(e))
        message = "Procesado correctamente"
        return HttpResponse(json.dumps({"message": message, "file": str(request.user.username)+".xlsx", "path": "media/proces/"+str(request.user.username)+".xlsx"}))
    else:
        return redirect("login")

def send_data(user, data, op, name_file):
    #print(data)
    url = "https://127.0.0.1:8008/process/"
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