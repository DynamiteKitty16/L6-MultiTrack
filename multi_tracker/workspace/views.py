from django.shortcuts import render, get_object_or_404, redirect
from .models import AttendanceRecord, LeaveRequest
from django.contrib.auth.decorators import login_required
from .decorators import tenant_required

# AttendanceRecord List View
@login_required
@tenant_required
def attendance_list(request):
    records = AttendanceRecord.objects.filter(user=request.user)
    return render(request, 'attendance/list.html', {'records': records})

# AttendanceRecord Create View
@login_required
@tenant_required
def attendance_create(request):
    if request.method == 'POST':
        # Handle form submission
        tenant = request.user.profile.tenant
        AttendanceRecord.objects.create(
            user=request.user,
            tenant=tenant,
            date=request.POST.get('date'),
            type=request.POST.get('type'),
        )
        return redirect('attendance_list')
    return render(request, 'attendance/create.html')

# AttendanceRecord Delete View
@login_required
@tenant_required
def attendance_delete(request, pk):
    record = get_object_or_404(AttendanceRecord, pk=pk, user=request.user)
    record.delete()
    return redirect('attendance_list')
