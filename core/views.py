import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.conf import settings
from django.db.models import Sum
import google.generativeai as genai
from itertools import groupby
from .models import Absensi, UangKas, Member

# Konfigurasi Gemini (Aman jika key belum diset)
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except:
    pass

@ensure_csrf_cookie
def index(request):
    """Render halaman utama"""
    return render(request, 'index.html')

# --- API MEMBERS ---
@csrf_exempt
def api_members(request):
    if request.method == 'GET':
        members = list(Member.objects.values('id', 'name').order_by('name'))
        return JsonResponse(members, safe=False)
    elif request.method == 'POST':
        data = json.loads(request.body)
        Member.objects.create(name=data['name'])
        return JsonResponse({'status': 'success'})
@csrf_exempt
def api_delete_member(request, id):
    if request.method == 'DELETE':
        Member.objects.filter(id=id).delete()
        return JsonResponse({'status': 'deleted'    })

# --- API TRAINING HISTORY ---
def api_training_history(request):
    queryset = Absensi.objects.select_related('member').order_by('-date', 'member__name')
    history = []
    
    # Grouping data berdasarkan tanggal
    for date, group in groupby(queryset, key=lambda x: x.date):
        sessions_list = list(group)
        present_count = sum(1 for x in sessions_list if x.status == 'Hadir')
        attendees = [{'id': r.id, 'name': r.member.name, 'status': r.status} for r in sessions_list]
            
        history.append({
            'date': date,
            'total_present': present_count,
            'attendees': attendees
        })
    return JsonResponse(history, safe=False)

# --- API REPORT ---
def api_member_report(request):
    try:
        fee = int(request.GET.get('fee', 15000))
    except ValueError:
        fee = 15000

    data = []
    members = Member.objects.all()

    for m in members:
        present_count = Absensi.objects.filter(member=m, status='Hadir').count()
        total_paid_agg = UangKas.objects.filter(member=m, type='masuk').aggregate(Sum('amount'))
        total_paid = total_paid_agg['amount__sum'] or 0
        paid_freq = UangKas.objects.filter(member=m, type='masuk').count()

        target = present_count * fee
        debt = target - total_paid
        
        status = 'Lunas'
        if debt > 0: status = 'Nunggak'
        elif debt < 0: status = 'Deposit'

        data.append({
            'name': m.name,
            'present': present_count,
            'paid_freq': paid_freq,
            'total_paid': total_paid,
            'target': target,
            'debt': debt,
            'status': status
        })

    data.sort(key=lambda x: x['debt'], reverse=True)
    return JsonResponse(data, safe=False)

# --- API ABSENSI ---
def api_absensi(request):
    if request.method == 'GET':
        data = list(Absensi.objects.select_related('member').values(
            'id', 'date', 'member__name', 'member__id', 'status'
        ).order_by('-date'))
        return JsonResponse(data, safe=False)
    elif request.method == 'POST':
        data = json.loads(request.body)
        member = Member.objects.get(id=data['member_id'])
        # Cegah duplikat di hari yang sama
        if not Absensi.objects.filter(date=data['date'], member=member).exists():
            Absensi.objects.create(date=data['date'], member=member, status=data['status'])
        return JsonResponse({'status': 'success'})

@csrf_exempt
def api_absensi_bulk(request):
    """API Baru untuk menyimpan banyak absensi sekaligus"""
    if request.method == 'POST':
        data = json.loads(request.body)
        date = data.get('date')
        member_ids = data.get('member_ids', [])
        status = data.get('status', 'Hadir') # Default Hadir
        
        count = 0
        for mid in member_ids:
            try:
                member = Member.objects.get(id=mid)
                # Cek duplikat
                if not Absensi.objects.filter(date=date, member=member).exists():
                    Absensi.objects.create(date=date, member=member, status=status)
                    count += 1
            except Member.DoesNotExist:
                continue
                
        return JsonResponse({'status': 'success', 'count': count})
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def api_delete_absensi(request, id):
    if request.method == 'DELETE':
        Absensi.objects.filter(id=id).delete()
        return JsonResponse({'status': 'deleted'})

# --- API KAS ---
def api_kas(request):
    if request.method == 'GET':
        kas_list = UangKas.objects.select_related('member').order_by('-date')
        data = []
        for k in kas_list:
            display_name = k.description
            if k.member:
                display_name = f"{k.member.name} ({k.description})"
            data.append({
                'id': k.id, 'date': k.date, 'name': display_name,
                'type': k.type, 'amount': k.amount
            })
        return JsonResponse(data, safe=False)
    elif request.method == 'POST':
        data = json.loads(request.body)
        member = None
        if data.get('member_id'):
            member = Member.objects.get(id=data['member_id'])
        UangKas.objects.create(
            date=data['date'], description=data['description'],
            member=member, type=data['type'], amount=data['amount']
        )
        return JsonResponse({'status': 'success'})
    
def api_kas_total(request):
    total_masuk_agg = UangKas.objects.filter(type='masuk').aggregate(Sum('amount'))
    total_keluar_agg = UangKas.objects.filter(type='keluar').aggregate(Sum('amount'))
    total_masuk = total_masuk_agg['amount__sum'] or 0
    total_keluar = total_keluar_agg['amount__sum'] or 0
    saldo = total_masuk - total_keluar
    return JsonResponse({
        'total_masuk': total_masuk,
        'total_keluar': total_keluar,
        'saldo': saldo
    })

def api_delete_kas(request, id):
    if request.method == 'DELETE':
        UangKas.objects.filter(id=id).delete()
        return JsonResponse({'status': 'deleted'})

# --- API AI ---
def api_ask_ai(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if not settings.GEMINI_API_KEY:
            return JsonResponse({'response': 'API Key belum disetting di server.'})
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(data.get('prompt'))
            return JsonResponse({'response': response.text})
        except Exception as e:
            return JsonResponse({'response': f"Error AI: {str(e)}"}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)