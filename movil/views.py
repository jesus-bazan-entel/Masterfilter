from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login as do_login
from django.contrib.auth import authenticate
from django.contrib.auth import logout as do_logout
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
import json
import pandas as pd
import requests
import logging
from .models import *

_logging = logging.basicConfig(filename="logger.log", level=logging.INFO)

# Create your views here.

def movil(request):
    logging.info(f"Sesión del usuario:{request.session}")
    logging.info(f"Cookies recibidas:{request.COOKIES}")
    logging.info(f"Usuario autenticado:{request.user}")
    if request.user.is_authenticated:
        #return redirect("abct")
        logging.info(f"Username: {request.user.username}")
        logging.info(f"Email: {request.user.email}")
        logging.info(f"Nombre completo: {request.user.get_full_name()}")
        logging.info(f"Último login: {request.user.last_login}")
        logging.info(f"Fecha de registro: {request.user.date_joined}")
    
        endp = EndPoint.objects.all().first()
        perm = Permision.objects.filter(user=request.user).first()
        if not perm.movil:
            return redirect("fijo")
        doc = Document.objects.filter(user=request.user).last()
        total = 0
        name = ""
        
        #if doc:
        #    total = doc.total
        #    name = str(doc.file)
        
        # Verifica si `doc` es `None`
        if doc is not None:
            logging.info(f"ID: {doc.id}, File: {doc.file}")
            total = doc.total
            name = str(doc.file)
        else:
            # Si no hay documentos asociados, asigna valores predeterminados
            logging.info("No documents found for this user.")
            total = 0
            name = ""

        logging.info(endp)
        logging.info(total)
        logging.info(perm.movil)
        logging.info(name)
        return render(request, "movil.html",{
                    "segment":"movil", 
                    "subido": total, 
                    "endpoint": endp, 
                    "perm": perm, 
                    "name":name
                })
    else:
        return redirect("login")

def consult_individual(request):
    try:
        body = json.loads(request.body)
        phone = body.get("phone")

        payload = json.dumps({
            "user": request.user.username,
            "phone": phone
        })

        headers = { 'Content-Type': 'application/json' }

        response = requests.post("https://api.masterfilter.es/phone/consult/", headers=headers, data=payload)
        response_json = response.json()

        status_code = response_json["data"][0]
        data_or_error = response_json["data"][1]

        if status_code == 200:
            return JsonResponse({
                "success": True,
                "operator": data_or_error
            })
        else:
            try:
                error_data = json.loads(data_or_error)
            except:
                error_data = {"message": data_or_error}
            return JsonResponse({"success": False, "error": error_data}, status=404)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

def reanude(request):
    logging.info("REANUDE SAM")
    doc = Document.objects.filter(user=request.user)
    for d in doc:
        if str(d.file).split("/")[1] == request.POST["file"]:
            pro_file(d, request, False)
            break
    return redirect("movil")

def upload(request):
    logging.info("upload request")
    status = True
    try:
        url = "http://185.47.131.53:8800/filter_data/"
        payload = json.dumps({
            "user": request.user.username,
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        logging.info(response.text)

        if response.status_code == 200:
            data = response.json()
            dataFull = data
            status = True if not dataFull["data"] else False
            logging.info(dataFull)
        else:
            logging.info(f"Error {response.status_code}: {response.text}")
            status = False
    except Exception as e:
        logging.info(f"Error Exception: {e}")
        status = False

    if status:
        try:
            logging.info(request)
            logging.info("before Document")
            logging.info(request.user)
            doc = Document.objects.create(
                file = request.FILES["file"],
                user = request.user
            )
            pro_file(doc, request, True)
        except Exception as e:
            logging.info(f"Se produjo una excepción: {str(e)}")
            pass
    return redirect("/")

def pro_file(doc, request, op):
    name_file = str(doc.file).split("/")[1]
    logging.info(name_file)
    data = read_file(name_file)

    if data is None:
        logging.info("Archivo no válido, deteniendo proceso.")
        return  # No continuar si hay error
        
    doc.save()
    
    # Crear ScrapingJob para tracking
    scraping_job = ScrapingJob.objects.create(
        document=doc,
        user=request.user,
        file_name=name_file,
        total_numbers=len(data),
        status='pending'
    )
    logging.info(f"ScrapingJob creado: {scraping_job.id}")
    
    # Marcar como en proceso
    scraping_job.mark_as_processing()
    
    try:
        send_data(request.user.username, data, op, name_file, scraping_job)
    except Exception as e:
        logging.error(f"Error al enviar datos: {str(e)}")
        scraping_job.mark_as_failed(str(e))

def read_file(name_file):
    try:
        name_file = name_file.replace(" ", "_")
        file = "media/subido/" + name_file
        df = pd.read_excel(file, sheet_name='Hoja1')

        # Validar si tiene más de 5,000 registros
        if len(df) > 5000:
            logging.info(f"Error: El archivo {name_file} tiene más de 5,000 registros ({len(df)} encontrados).")
            return None  # Devuelve None para indicar que no se procesará

        df.describe()
        documents = df['numeros'].tolist()
        return documents
    except Exception as e:
        logging.info(f"Error al leer el archivo: {str(e)}")
        logging.info("Detalle del error:")
        return None

def export(request):
    logging.info("SAM inicio funcion export en views.py")
    logging.info(f"Sesión del usuario:{request.session}")
    logging.info(f"Cookies recibidas:{request.COOKIES}")
    logging.info(f"Usuario autenticado:{request.user}")
    if request.user.is_authenticated:
        logging.info("SAM user autenticado en views.py")
        data = request.POST["data"]
        #print(request.POST["data"])
        #print(request.POST["nameFile"])
        #data_all = {"number":[], "operator":[]}
        #df = pd.DataFrame()
        name_file = json.loads(data)["nameFile"]
        data = json.loads(data)["data"]["list"]
        logging.info("SAM en views: def export request")
        logging.info(name_file)
        file = "media/subido/" + name_file
        df = pd.read_excel(file, sheet_name='Hoja1')
        df['operador'] = pd.NA
        #print(df)
        for d in data:
            #print(d)
            #df.loc[df['numeros'] == int(d['number']), 'operador'] = d["operator"]

            num_str = str(d['number']).strip().replace(" ", "")  # Eliminar espacios en caso de que existan
            if num_str.isdigit():  # Verificar si es un número válido
                df.loc[df['numeros'] == int(num_str), 'operador'] = d["operator"]
            else:
                logging.warning(f"Número inválido encontrado: {num_str}")
            #data_all["operator"].append(d["operator"])
            #data_all["number"].append(d["number"])

        #df["numeros"] = data_all["number"]
        #df["operador"] = data_all["operator"]

        try:
            #df.to_excel("media/proces/"+str(request.user.username)+".xlsx")
            df.to_excel("media/proces/"+name_file)
            
            # Marcar el job como completado
            scraping_job = ScrapingJob.objects.filter(
                user=request.user,
                file_name=name_file,
                status__in=['processing', 'retrying']
            ).first()
            
            if scraping_job:
                scraping_job.processed_numbers = len(data)
                scraping_job.mark_as_completed()
                logging.info(f"ScrapingJob {scraping_job.id} marcado como completado")
                
        except Exception as e:
            logging.info("Error: "+str(e))
            
        message = "Procesado correctamente"
        #return HttpResponse(json.dumps({"message": message, "file": str(request.user.username)+".xlsx", "path": "media/proces/"+str(request.user.username)+".xlsx"}))
        return HttpResponse(json.dumps({
            "message": message,
            "file": name_file, 
            #"file": str(request.user.username)+"_Movil_"+name_file+".xlsx", 
            "path": "media/proces/"+name_file
            #"path": "media/proces/"+str(request.user.username)+"_Movil_"+name_file+".xlsx"
        }))
        #return HttpResponse(json.dumps({"message": message, "file": str(request.user.username)+"_Movil_"+name_file+".xlsx", "path": "media/proces/"+str(request.user.username)+".xlsx"}))
    else:
        return redirect("login")

def send_data(user, data, op, name_file, scraping_job=None):
    try:    
        #url = "http://127.0.0.1:8800/process/"
        url = "http://185.47.131.53:8800/process/"
        #url = "https://api.masterfilter.es/process/"
        payload = json.dumps({
            "user": user,
            "number": data,
            "new":op,
            "reprocess":False,
            "file": name_file
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        logging.info(response.text)
        
        # Si hay un job asociado y la respuesta es exitosa, actualizarlo
        if scraping_job and response.status_code == 200:
            logging.info(f"Datos enviados exitosamente para job {scraping_job.id}")
            
    except Exception as e:
        logging.info(f"Error al enviar datos: {str(e)}")
        if scraping_job:
            scraping_job.mark_as_failed(str(e))
        raise

def login(request):
    message = {"valid": ""}
    if request.method == "POST":
        user = request.POST["username"]
        passw = request.POST["password"]
        logging.info(user)
        logging.info(passw)
        Users = authenticate(username=user, password=passw)
        if Users is not None:
            do_login(request, Users)
            logging.info("SAM auth OK")
            return redirect("movil")
        else:
            message = {"valid": "Usuario o password incorrecto"}

    return render(request, "sign-in.html", message)

def logout(request):
    do_logout(request)
    return redirect('/')

def sign_in_fijo(request):
    result = {
        "code": 400,
        "status": "Fail",
        "message": "",
        "data": {}
    }
    if request.method == "GET":
        user = request.GET["username"]
        passw = request.GET["password"]
        Users = authenticate(username=user, password=passw)
        if Users is not None:
            user_pangea = UserPangea.objects.filter(user = User.objects.filter(username = user).first()).first()
            if user_pangea:
                result["data"] = {
                    "username": user_pangea.username,
                    "password": user_pangea.password
                }
                result["code"] = 200
                result["status"] = "OK"
                result["message"] = "Success"
            else:
                result["message"] = "Usuario Pangea no asignado"
        else:
            result["message"] = "Usuario o password incorrecto"

    return HttpResponse(json.dumps(result))
