import requests
import time
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from movil.models import Permision
from types import SimpleNamespace
import tempfile
import os

@login_required
@permission_required('movil.can_access_whatsapp', raise_exception=True)
def whatsapp_console(request):
    """Vista principal del módulo WhatsApp"""
    
    try:
        perm = Permision.objects.get(user=request.user)
    except:
        perm = SimpleNamespace(
            movil=False, fijo=False, orange1=False, orange2=False, 
            abct=False, wsp=True, amarilla=False, infobel=False, peoplecall=False
        )
    
    context = {
        'segment': 'wsp',
        'perm': perm,
        'title': 'Consulta WhatsApp',
        'user_permissions': {
            'can_access': request.user.has_perm('movil.can_access_whatsapp'),
            'can_consult': request.user.has_perm('movil.can_consult_numbers'),
            'can_bulk': request.user.has_perm('movil.can_bulk_consult'),
        }
    }
    return render(request, 'wsp/console.html', context)

def upload_whatsapp_task(phone_numbers):
    """
    Sube archivo a la API de CheckNumber.ai y retorna el task_id
    """
    try:
        api_url = "https://api.checknumber.ai/wa/api/simple/tasks"
        api_key = settings.CHECKNUMBER_API_KEY
        
        headers = {
            'X-API-Key': api_key
        }
        
        # Crear archivo temporal con los números
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            for phone in phone_numbers:
                temp_file.write(f"{phone}\n")
            temp_file_path = temp_file.name
        
        # Subir archivo
        with open(temp_file_path, 'rb') as file:
            files = {'file': ('numbers.txt', file, 'text/plain')}
            response = requests.post(api_url, headers=headers, files=files, timeout=30)
        
        # Eliminar archivo temporal
        os.unlink(temp_file_path)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'task_id': data.get('task_id'),
                'data': data
            }
        else:
            return {
                'success': False,
                'error': f'API error: {response.status_code} - {response.text}'
            }
            
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        try:
            os.unlink(temp_file_path)
        except:
            pass
        return {
            'success': False,
            'error': f'Error: {str(e)}'
        }

def check_task_status(task_id):
    """
    Consulta el estado de una tarea en la API
    """
    try:
        api_url = f"https://api.checknumber.ai/wa/api/simple/tasks/{task_id}"
        api_key = settings.CHECKNUMBER_API_KEY
        
        headers = {
            'X-API-Key': api_key
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {
                'success': True,
                'data': response.json()
            }
        else:
            return {
                'success': False,
                'error': f'API error: {response.status_code} - {response.text}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Error: {str(e)}'
        }

def download_results(result_url):
    """
    Descarga y procesa los resultados desde la URL proporcionada por la API
    """
    try:
        response = requests.get(result_url, timeout=30)
        
        if response.status_code == 200:
            # La API retorna un archivo Excel, necesitamos procesarlo
            import io
            import openpyxl
            
            workbook = openpyxl.load_workbook(io.BytesIO(response.content))
            sheet = workbook.active
            
            results = []
            # Saltar la primera fila si es encabezado
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if row[0]:  # Si hay un número en la primera columna
                    results.append({
                        'phone': str(row[0]),
                        'has_whatsapp': str(row[1]).lower() == 'yes' if len(row) > 1 else False,
                        'status': 'active' if (len(row) > 1 and str(row[1]).lower() == 'yes') else 'inactive'
                    })
            
            return {
                'success': True,
                'results': results
            }
        else:
            return {
                'success': False,
                'error': f'Error downloading results: {response.status_code}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Error processing results: {str(e)}'
        }

@login_required
@permission_required('movil.can_bulk_consult', raise_exception=True)
@require_http_methods(["POST"])
def bulk_consult(request):
    """Consultar múltiples números - Subir tarea"""
    phones = request.POST.get('phones', '').strip().split('\n')
    phones = [p.strip() for p in phones if p.strip()]
    
    if not phones:
        return JsonResponse({'error': 'Debe proporcionar al menos un número'}, status=400)
    
    if len(phones) > 100:
        return JsonResponse({'error': 'Máximo 100 números por consulta'}, status=400)
    
    # Subir tarea a la API
    upload_result = upload_whatsapp_task(phones)
    
    if upload_result['success']:
        return JsonResponse({
            'success': True,
            'task_id': upload_result['task_id'],
            'total': len(phones)
        })
    else:
        return JsonResponse({
            'success': False,
            'error': upload_result['error']
        }, status=500)

@login_required
@permission_required('movil.can_bulk_consult', raise_exception=True)
@require_http_methods(["GET"])
def check_task(request, task_id):
    """Consultar estado de una tarea"""
    status_result = check_task_status(task_id)
    
    if status_result['success']:
        data = status_result['data']
        response_data = {
            'success': True,
            'status': data.get('status'),
            'total': data.get('total', 0),
            'success_count': data.get('success', 0),
            'failure': data.get('failure', 0),
            'result_url': data.get('result_url')
        }
        
        # Si está completado y hay URL de resultados, descargar
        if data.get('status') == 'exported' and data.get('result_url'):
            download_result = download_results(data['result_url'])
            if download_result['success']:
                response_data['results'] = download_result['results']
        
        return JsonResponse(response_data)
    else:
        return JsonResponse({
            'success': False,
            'error': status_result['error']
        }, status=500)