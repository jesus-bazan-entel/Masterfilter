from django.shortcuts import render, redirect, HttpResponse
import json
import pandas as pd
import requests
from movil.models import *

# Create your views here.
def orange(request):
    if request.user.is_authenticated:
        endp = EndPoint.objects.all().first()
        perm = Permision.objects.filter(user=request.user).first()
        if not perm.orange1:
            return redirect("fijo")
        doc = Document.objects.filter(user=request.user).last()
        total = 0
        name = ""
        if doc:
            total = doc.total
            name = str(doc.file)
        return render(request, "orange.html",{
                    "segment":"orange1", 
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
    return redirect("orange1")

def upload(request):
    try:
        doc = Document.objects.create(
            file = request.FILES["file"],
            user = request.user
        )
        pro_file(doc, request, True)
    except:
        pass
    return redirect("orange1")

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
        data = request.POST["data"]
        #print(request.POST["data"])
        #print(request.POST["nameFile"])
        data_all = {"name":[], "document":[], "telephoneNumber":[], "emailContact":[], "postalContact":[], "product":[], "agreement":[]}
        #print(data)
        df = pd.DataFrame()
        #file = "media/" + request.POST["nameFile"]
        #df = pd.read_excel(file, sheet_name='Hoja1')
        data = json.loads(data)["data"]["list"]
        name_file = request.POST["nameFile"]
        for d in data:
            if d["telephoneNumber"] != "":
                _phone = ""
                for p in json.loads(d["telephoneNumber"]):
                    _phone += str(p["number"])+" | "

                _email = ""
                for p in json.loads(d["emailContact"]):
                    _email += str(p["eMailAddress"])+" | "

                _address = ""
                for ad in json.loads(d["postalContact"]):
                    _address += ""+str(ad["country"])+"-"+str(ad["city"])+"-"+str(ad["stateOrProvince"])+"-"+str(ad["streetType"])+":"+str(ad["streetName"])+" "+str(ad["streetNr"])+" "+str(ad["staircaseNumber"])+" - Piso: "+str(ad["floorNumber"])+" - Apt: "+str(ad["apartmentNumber"])+"- CP:"+str(ad["postCode"])+" | "
                    
                aux = json.loads(d["individual"])
                _name = ""
                _document = ""
                if aux != "" and aux != '""':
                    _name = aux["formattedName"]
                    _document = aux["id"]

                _campain = ""
                _campain_json = json.loads(d["product"])
                if _campain_json != "" and _campain_json != '""':
                    #print(_campain_json)
                    try:
                        for p in _campain_json["result"]:
                            for item_camp in p["campaignNum"]:
                                if item_camp["nomCampaign"] not in _campain:
                                    _campain += ""+item_camp["nomCampaign"]+" | "
                    except Exception as err:
                        print("Error in campain json: "+str(err))

                agreement = ""
                if "Agreement" in d["agreement"]:
                    for a in json.loads(d["agreement"])["Agreement"]:
                        agreement += str(a["agreementPeriod"])+" | "
                data_all["telephoneNumber"].append(_phone[:-2])
                data_all["emailContact"].append(_email[:-2])
                data_all["postalContact"].append(_address[:-2])
                data_all["name"].append(_name)
                data_all["document"].append(_document)
                data_all["product"].append(_campain)
                data_all["agreement"].append(agreement)

        df["name"] = data_all["name"]
        df["document"] = data_all["document"]
        df["telephoneNumber"] = data_all["telephoneNumber"]
        df["emailContact"] = data_all["emailContact"]
        df["postalContact"] = data_all["postalContact"]
        df["product"] = data_all["product"]
        df["agreement"] = data_all["agreement"]

        try:
            df.to_excel("media/proces/filtrado_"+str(name_file))
        except Exception as e:
            print("Error: "+str(e))
        message = "Procesado correctamente"
        print("filtrado_"+str(name_file))
        return HttpResponse(json.dumps({"message": message, "file": "filtrado_"+str(name_file), "path": "media/proces/filtrado_"+str(name_file)}))
    else:
        return redirect("login")

def send_data(user, data, op, name_file):
    #print(data)
    url = "http://127.0.0.1:8888/process/"
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