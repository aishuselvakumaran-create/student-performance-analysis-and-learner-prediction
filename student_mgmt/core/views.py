from core.ml.predict import predict_for_semester
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
import csv
from django.http import HttpResponse
from .models import User, Faculty, Student, Score, Notification, DEPARTMENT_CHOICES, SEMESTER_CHOICES
 
 
# ─── Helpers ──────────────────────────────────────────────────────────────────
def login_required_role(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.session.get('user_id'):
                return redirect('login')
            if roles and request.session.get('role') not in roles:
                return redirect('login')
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        return wrapper
    return decorator
 
 
def get_current_user(request):
    uid = request.session.get('user_id')
    if uid:
        return User.objects.filter(id=uid).first()
    return None
 
 
# ─── Auth ──────────────────────────────────────────────────────────────────────
def login_view(request):
    if request.session.get('user_id'):
        role = request.session.get('role')
        return redirect(f'{role}_dashboard')
 
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                request.session['user_id'] = user.id
                request.session['role'] = user.role
                request.session['username'] = user.username
                return redirect(f'{user.role}_dashboard')
            else:
                messages.error(request, 'Invalid password.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return render(request, 'login.html')
 
 
def logout_view(request):
    request.session.flush()
    return redirect('login')
 
 
# ─── Admin Dashboard ───────────────────────────────────────────────────────────
@login_required_role('admin')
def admin_dashboard(request):
    total_students = Student.objects.count()
    total_faculty = Faculty.objects.count()
    dept_students = Student.objects.values('department').annotate(count=Count('id')).order_by('department')
    dept_faculty = Faculty.objects.values('department').annotate(count=Count('id')).order_by('department')
    recent_students = Student.objects.order_by('-created_at')[:5]
    recent_faculty = Faculty.objects.order_by('-created_at')[:5]
 
    dept_labels = [d[0] for d in DEPARTMENT_CHOICES]
    dept_student_data = {d['department']: d['count'] for d in dept_students}
    dept_faculty_data = {d['department']: d['count'] for d in dept_faculty}
    student_counts = [dept_student_data.get(d, 0) for d in dept_labels]
    faculty_counts = [dept_faculty_data.get(d, 0) for d in dept_labels]
 
    return render(request, 'admin_panel/dashboard.html', {
        'total_students': total_students,
        'total_faculty': total_faculty,
        'dept_students': dept_students,
        'dept_faculty': dept_faculty,
        'recent_students': recent_students,
        'recent_faculty': recent_faculty,
        'dept_labels': json.dumps(dept_labels),
        'student_counts': json.dumps(student_counts),
        'faculty_counts': json.dumps(faculty_counts),
    })
 
 
# ─── Admin: Student CRUD ───────────────────────────────────────────────────────
@login_required_role('admin')
def add_student(request):
    if request.method == 'POST':
        try:
            p = request.POST
            if User.objects.filter(username=p['username']).exists():
                messages.error(request, 'Username already exists.')
                return render(request, 'admin_panel/add_student.html', {'departments': DEPARTMENT_CHOICES, 'semesters': SEMESTER_CHOICES})
            user = User(username=p['username'], role='student')
            user.set_password(p['password'])
            user.save()
            Student.objects.create(
                user=user,
                student_id=p['student_id'],
                first_name=p['first_name'],
                last_name=p['last_name'],
                email=p['email'],
                department=p['department'],
                semester=p['semester'],
                phone_number=p.get('phone_number', ''),
                address=p.get('address', ''),
                dob=p.get('dob') or None,
            )
            messages.success(request, f"Student '{p['first_name']} {p['last_name']}' added successfully.")
            return redirect('view_students')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'admin_panel/add_student.html', {'departments': DEPARTMENT_CHOICES, 'semesters': SEMESTER_CHOICES})
 
 
@login_required_role('admin')
def view_students(request):
    qs = Student.objects.select_related('user').order_by('-created_at')
    search = request.GET.get('search', '')
    dept = request.GET.get('department', '')
    sem = request.GET.get('semester', '')
    if search:
        qs = qs.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) |
                       Q(student_id__icontains=search) | Q(email__icontains=search))
    if dept:
        qs = qs.filter(department=dept)
    if sem:
        qs = qs.filter(semester=sem)
    return render(request, 'admin_panel/view_students.html', {
        'students': qs, 'departments': DEPARTMENT_CHOICES,
        'semesters': SEMESTER_CHOICES, 'search': search,
        'selected_dept': dept, 'selected_sem': sem,
    })
 
 
@login_required_role('admin')
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        try:
            p = request.POST
            student.first_name = p['first_name']
            student.last_name = p['last_name']
            student.email = p['email']
            student.department = p['department']
            student.semester = p['semester']
            student.phone_number = p.get('phone_number', '')
            student.address = p.get('address', '')
            student.dob = p.get('dob') or None
            student.student_id = p['student_id']
            student.save()
            if p.get('password'):
                student.user.set_password(p['password'])
                student.user.save()
            messages.success(request, 'Student updated successfully.')
            return redirect('view_students')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'admin_panel/edit_student.html', {
        'student': student, 'departments': DEPARTMENT_CHOICES, 'semesters': SEMESTER_CHOICES
    })
 
 
@login_required_role('admin')
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    student.user.delete()
    messages.success(request, 'Student deleted.')
    return redirect('view_students')
 
 
@login_required_role('admin')
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    scores = student.scores.all().order_by('semester')
    sem_labels = [f"Sem {s.semester}" for s in scores]
    chart_data = {
        'labels': sem_labels,
        'previous_exam': [s.previous_exam_marks for s in scores],
        'internal_test': [s.internal_test_marks for s in scores],
        'assignment': [s.assignment_score for s in scores],
        'quiz': [s.quiz_score for s in scores],
        'attendance': [s.attendance_percentage for s in scores],
        'participation': [s.class_participation for s in scores],
    }
    return render(request, 'admin_panel/student_detail.html', {
        'student': student, 'scores': scores,
        'chart_data': json.dumps(chart_data),
        'overall': student.get_overall_percentage(),
        
    })
 
 
# ─── Admin: Faculty CRUD ───────────────────────────────────────────────────────
@login_required_role('admin')
def add_faculty(request):
    if request.method == 'POST':
        try:
            p = request.POST
            if User.objects.filter(username=p['username']).exists():
                messages.error(request, 'Username already exists.')
                return render(request, 'admin_panel/add_faculty.html', {'departments': DEPARTMENT_CHOICES})
            user = User(username=p['username'], role='faculty')
            user.set_password(p['password'])
            user.save()
            Faculty.objects.create(
                user=user,
                faculty_id=p['faculty_id'],
                first_name=p['first_name'],
                last_name=p['last_name'],
                email=p['email'],
                department=p['department'],
                phone_number=p.get('phone_number', ''),
                address=p.get('address', ''),
                dob=p.get('dob') or None,
            )
            messages.success(request, f"Faculty '{p['first_name']} {p['last_name']}' added successfully.")
            return redirect('view_faculty')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'admin_panel/add_faculty.html', {'departments': DEPARTMENT_CHOICES})
 
 
@login_required_role('admin')
def view_faculty(request):
    qs = Faculty.objects.select_related('user').order_by('-created_at')
    search = request.GET.get('search', '')
    dept = request.GET.get('department', '')
    if search:
        qs = qs.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) |
                       Q(faculty_id__icontains=search) | Q(email__icontains=search))
    if dept:
        qs = qs.filter(department=dept)
    return render(request, 'admin_panel/view_faculty.html', {
        'faculty_list': qs, 'departments': DEPARTMENT_CHOICES,
        'search': search, 'selected_dept': dept,
    })
 
 
@login_required_role('admin')
def edit_faculty(request, faculty_id):
    faculty = get_object_or_404(Faculty, id=faculty_id)
    if request.method == 'POST':
        try:
            p = request.POST
            faculty.first_name = p['first_name']
            faculty.last_name = p['last_name']
            faculty.email = p['email']
            faculty.department = p['department']
            faculty.phone_number = p.get('phone_number', '')
            faculty.address = p.get('address', '')
            faculty.dob = p.get('dob') or None
            faculty.faculty_id = p['faculty_id']
            faculty.save()
            if p.get('password'):
                faculty.user.set_password(p['password'])
                faculty.user.save()
            messages.success(request, 'Faculty updated successfully.')
            return redirect('view_faculty')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'admin_panel/edit_faculty.html', {
        'faculty': faculty, 'departments': DEPARTMENT_CHOICES
    })
 
 
@login_required_role('admin')
def delete_faculty(request, faculty_id):
    faculty = get_object_or_404(Faculty, id=faculty_id)
    faculty.user.delete()
    messages.success(request, 'Faculty deleted.')
    return redirect('view_faculty')
 
 
@login_required_role('admin')
def admin_marklist(request):
    students = Student.objects.all().order_by('department', 'first_name')
    search = request.GET.get('search', '')
    dept = request.GET.get('department', '')
    if search:
        students = students.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(student_id__icontains=search))
    if dept:
        students = students.filter(department=dept)
    return render(request, 'admin_panel/marklist.html', {
        'students': students, 'departments': DEPARTMENT_CHOICES,
        'search': search, 'selected_dept': dept,
    })
 
 
# ─── Faculty Dashboard ─────────────────────────────────────────────────────────
@login_required_role('faculty')
def faculty_dashboard(request):
    user    = get_current_user(request)
    faculty = get_object_or_404(Faculty, user=user)
    dept_students       = Student.objects.filter(department=faculty.department)
    total_dept_students = dept_students.count()
    sem_dist = dept_students.values('semester').annotate(count=Count('id')).order_by('semester')

    sem_labels = [f"Sem {s['semester']}" for s in sem_dist]
    sem_counts = [s['count'] for s in sem_dist]

    # ── ML Prediction overview ──────────────────────────────────────
    fast_learners    = []
    average_learners = []
    slow_learners    = []

    for student in dept_students:
        scores = student.scores.all()
        if not scores.exists():
            continue
        # Use latest uploaded semester to predict next
        latest_sem = max(int(s.semester) for s in scores)
        next_sem   = latest_sem + 1
        if next_sem > 6:
            continue
        result = predict_for_semester(scores, next_sem)
        if 'error' in result:
            continue
        cat = result.get('predicted_category')
        entry = {
            'student'    : student,
            'confidence' : result['confidence'],
            'trend'      : result['trend'],
            'based_on_sem': latest_sem,
            'predicting_for_sem': next_sem,
        }
        if cat == 'Fast Learner':
            fast_learners.append(entry)
        elif cat == 'Average Learner':
            average_learners.append(entry)
        elif cat == 'Slow Learner':
            slow_learners.append(entry)
    # ───────────────────────────────────────────────────────────────

    return render(request, 'faculty/dashboard.html', {
        'faculty'           : faculty,
        'total_dept_students': total_dept_students,
        'sem_labels'        : json.dumps(sem_labels),
        'sem_counts'        : json.dumps(sem_counts),
        'fast_learners'     : fast_learners,
        'average_learners'  : average_learners,
        'slow_learners'     : slow_learners,
        'pred_counts'       : json.dumps({
            'Fast Learner'   : len(fast_learners),
            'Average Learner': len(average_learners),
            'Slow Learner'   : len(slow_learners),
        }),
    })
 
@login_required_role('faculty')
def upload_scores(request):
    user = get_current_user(request)
    faculty = get_object_or_404(Faculty, user=user)
    selected_sem = request.GET.get('semester', '')
    search = request.GET.get('search', '')
 
    students = Student.objects.filter(department=faculty.department)
    
    if search:
        students = students.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(student_id__icontains=search))
 
    if request.method == 'POST':
        sem = request.POST.get('semester')
        student_ids = request.POST.getlist('student_ids')
        for sid in student_ids:
            student = Student.objects.get(id=sid)
            score, created = Score.objects.get_or_create(
                student=student, semester=sem,
                defaults={'faculty': faculty}
            )
            score.faculty = faculty
            score.previous_exam_marks = float(request.POST.get(f'prev_{sid}', 0))
            score.internal_test_marks = float(request.POST.get(f'internal_{sid}', 0))
            score.assignment_score = float(request.POST.get(f'assignment_{sid}', 0))
            score.quiz_score = float(request.POST.get(f'quiz_{sid}', 0))
            score.attendance_percentage = float(request.POST.get(f'attendance_{sid}', 0))
            score.class_participation = float(request.POST.get(f'participation_{sid}', 0))
            score.save()
            Notification.objects.create(
                student=student,
                message=f"Your marks for Semester {sem} have been uploaded/updated by {faculty.get_full_name()}."
            )
        messages.success(request, f'Scores uploaded for Semester {sem}.')
        return redirect('upload_scores')
 
    existing_scores = {}
    existing_scores_json = {}
    if selected_sem:
        for s in students:
            score = Score.objects.filter(student=s, semester=selected_sem).first()
            if score:
                existing_scores[s.id] = score
                existing_scores_json[str(s.id)] = {
                    'previous_exam_marks': score.previous_exam_marks,
                    'internal_test_marks': score.internal_test_marks,
                    'assignment_score': score.assignment_score,
                    'quiz_score': score.quiz_score,
                    'attendance_percentage': score.attendance_percentage,
                    'class_participation': score.class_participation,
                }
 
    return render(request, 'faculty/upload_scores.html', {
        'faculty': faculty,
        'students': students,
        'semesters': SEMESTER_CHOICES,
        'selected_sem': selected_sem,
        'search': search,
        'existing_scores': existing_scores,
        'existing_scores_json': json.dumps(existing_scores_json),
    })
 
 
@login_required_role('faculty')
def faculty_results(request):
    user = get_current_user(request)
    faculty = get_object_or_404(Faculty, user=user)
    students = Student.objects.filter(department=faculty.department).prefetch_related('scores')
    search = request.GET.get('search', '')
    selected_sem = request.GET.get('semester', '')
    if search:
        students = students.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(student_id__icontains=search))
 
    student_data = []
    for student in students:
        scores = student.scores.all()
        if selected_sem:
            scores = scores.filter(semester=selected_sem)
        student_data.append({'student': student, 'scores': scores})
 
    return render(request, 'faculty/results.html', {
        'faculty': faculty,
        'student_data': student_data,
        'semesters': SEMESTER_CHOICES,
        'selected_sem': selected_sem,
        'search': search,
    })
 
@login_required_role('faculty')
def edit_score(request, score_id):
    user = get_current_user(request)
    faculty = get_object_or_404(Faculty, user=user)
    score = get_object_or_404(Score, id=score_id, student__department=faculty.department)
    if request.method == 'POST':
        try:
            score.previous_exam_marks = float(request.POST.get('previous_exam_marks', 0))
            score.internal_test_marks = float(request.POST.get('internal_test_marks', 0))
            score.assignment_score = float(request.POST.get('assignment_score', 0))
            score.quiz_score = float(request.POST.get('quiz_score', 0))
            score.attendance_percentage = float(request.POST.get('attendance_percentage', 0))
            score.class_participation = float(request.POST.get('class_participation', 0))
            score.faculty = faculty
            score.save()
            Notification.objects.create(
                student=score.student,
                message=f"Your marks for Semester {score.semester} have been updated by {faculty.get_full_name()}."
            )
            messages.success(request, f"Scores updated for {score.student.get_full_name()} – Sem {score.semester}.")
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('faculty_results')


@login_required_role('faculty')
def delete_score(request, score_id):
    user = get_current_user(request)
    faculty = get_object_or_404(Faculty, user=user)
    score = get_object_or_404(Score, id=score_id, student__department=faculty.department)
    student_name = score.student.get_full_name()
    sem = score.semester
    score.delete()
    messages.success(request, f"Scores deleted for {student_name} – Sem {sem}.")
    return redirect('faculty_results')
@login_required_role('faculty')
def faculty_student_detail(request, student_id):
    user = get_current_user(request)
    faculty = get_object_or_404(Faculty, user=user)
    student = get_object_or_404(Student, id=student_id, department=faculty.department)
    scores = student.scores.all().order_by('semester')
    sem_labels = [f"Sem {s.semester}" for s in scores]
    chart_data = {
        'labels': sem_labels,
        'previous_exam': [s.previous_exam_marks for s in scores],
        'internal_test': [s.internal_test_marks for s in scores],
        'assignment': [s.assignment_score for s in scores],
        'quiz': [s.quiz_score for s in scores],
        'attendance': [s.attendance_percentage for s in scores],
        'participation': [s.class_participation for s in scores],
    }
    return render(request, 'faculty/student_detail.html', {
        'student': student, 'scores': scores,
        'chart_data': json.dumps(chart_data),
        'overall': student.get_overall_percentage(),
      
        'faculty': faculty,
    })
 
 
# ─── Student Dashboard ─────────────────────────────────────────────────────────
@login_required_role('student')
def student_dashboard(request):
    user = get_current_user(request)
    student = get_object_or_404(Student, user=user)
    scores = student.scores.all().order_by('semester')
    sem_labels = [f"Sem {s.semester}" for s in scores]
    chart_data = {
        'labels': sem_labels,
        'previous_exam': [s.previous_exam_marks for s in scores],
        'internal_test': [s.internal_test_marks for s in scores],
        'assignment': [s.assignment_score for s in scores],
        'quiz': [s.quiz_score for s in scores],
        'attendance': [s.attendance_percentage for s in scores],
        'participation': [s.class_participation for s in scores],
    }
    unread_count = student.notifications.filter(is_read=False).count()
    # inside student_dashboard view, before the return render(...)
    current_semester = student.get_current_semester()
    return render(request, 'student/dashboard.html', {
        'student': student,
        'scores': scores,
        'current_semester': current_semester,
        'chart_data': json.dumps(chart_data),
        'overall': student.get_overall_percentage(),
       
        'unread_count': unread_count,
    })
 
 
@login_required_role('student')
def student_profile(request):
    user = get_current_user(request)
    student = get_object_or_404(Student, user=user)
    unread_count = student.notifications.filter(is_read=False).count()
    return render(request, 'student/profile.html', {'student': student, 'unread_count': unread_count})
 
 
@login_required_role('student')
def student_marklist(request):
    user = get_current_user(request)
    student = get_object_or_404(Student, user=user)
    raw_scores = student.scores.all().order_by('semester')
    score_colors = ['#6C63FF','#06b6d4','#10b981','#f59e0b','#ef4444','#a78bfa']
    score_labels = ['Previous Exam','Internal Test','Assignment','Quiz','Attendance','Participation']
    scores = []
    for s in raw_scores:
        vals = [s.previous_exam_marks, s.internal_test_marks, s.assignment_score,
                s.quiz_score, s.attendance_percentage, s.class_participation]
        s.fields = list(zip(score_labels, vals, score_colors))
        scores.append(s)
    return render(request, 'student/marklist.html', {'student': student, 'scores': scores, 'unread_count': student.notifications.filter(is_read=False).count()})
 
 
@login_required_role('student')
def student_notifications(request):
    user = get_current_user(request)
    student = get_object_or_404(Student, user=user)
    notifications = student.notifications.all().order_by('-created_at')
    student.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'student/notifications.html', {
        'student': student, 'notifications': notifications, 'unread_count': 0
    })
@login_required_role('admin', 'faculty', 'student')
def predict_student_category(request, student_id):
    user        = get_current_user(request)
    role        = request.session.get('role')
    predict_sem = int(request.GET.get('semester', 2))

    if role == 'student':
        student = get_object_or_404(Student, user=user, id=student_id)
    elif role == 'faculty':
        faculty = get_object_or_404(Faculty, user=user)
        student = get_object_or_404(Student, id=student_id, department=faculty.department)
    else:
        student = get_object_or_404(Student, id=student_id)

    if predict_sem < 2 or predict_sem > 6:
        return JsonResponse({'error': 'Please select a semester between 2 and 6.'}, status=400)

    scores = student.scores.all()
    if not scores.exists():
        return JsonResponse({'error': 'No scores uploaded for this student yet.'}, status=400)

    result = predict_for_semester(scores, predict_sem)
    return JsonResponse(result)


@login_required_role('admin', 'faculty')
def prediction_chart_data(request):
    user = get_current_user(request)
    role = request.session.get('role')

    if role == 'faculty':
        faculty  = get_object_or_404(Faculty, user=user)
        students = Student.objects.filter(department=faculty.department)
    else:
        students = Student.objects.all()

    counts = {'Fast Learner': 0, 'Average Learner': 0, 'Slow Learner': 0}

    for student in students:
        scores = student.scores.all()
        if not scores.exists():
            continue
        latest_sem = max(int(s.semester) for s in scores)
        next_sem   = latest_sem + 1
        if next_sem > 6:
            continue
        result = predict_for_semester(scores, next_sem)
        if 'error' not in result:
            cat = result.get('next_year_category')
            if cat in counts:
                counts[cat] += 1

    return JsonResponse(counts)
# ─── CSV Import: Students ──────────────────────────────────────────────────────
@login_required_role('admin')
def sample_students_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_students.csv"'
    writer = csv.writer(response)
    writer.writerow(['first_name', 'last_name', 'student_id', 'email',
                     'username', 'password', 'department', 'semester',
                     'phone_number', 'dob', 'address'])
    writer.writerow(['John', 'Doe', 'STU001', 'john@example.com',
                     'johndoe', 'pass123', 'BCA', '1',
                     '9876543210', '2003-05-15', '123 Main St'])
    return response


@login_required_role('admin')
def import_students_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid .csv file.')
            return redirect('add_student')

        decoded = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)

        success_count = 0
        skip_count = 0
        errors = []

        for i, row in enumerate(reader, start=2):  # start=2 because row 1 is header
            try:
                username   = row.get('username', '').strip()
                student_id = row.get('student_id', '').strip()
                email      = row.get('email', '').strip()

                # Skip duplicates
                if User.objects.filter(username=username).exists():
                    skip_count += 1
                    continue
                if Student.objects.filter(student_id=student_id).exists():
                    skip_count += 1
                    continue
                if Student.objects.filter(email=email).exists():
                    skip_count += 1
                    continue

                user = User(username=username, role='student')
                user.set_password(row.get('password', '').strip())
                user.save()

                Student.objects.create(
                    user=user,
                    student_id=student_id,
                    first_name=row.get('first_name', '').strip(),
                    last_name=row.get('last_name', '').strip(),
                    email=email,
                    department=row.get('department', '').strip(),
                    semester=row.get('semester', '1').strip(),
                    phone_number=row.get('phone_number', '').strip(),
                    address=row.get('address', '').strip(),
                    dob=row.get('dob', '').strip() or None,
                )
                success_count += 1

            except Exception as e:
                errors.append(f'Row {i}: {e}')

        if success_count:
            messages.success(request, f'{success_count} student(s) imported successfully.')
        if skip_count:
            messages.warning(request, f'{skip_count} row(s) skipped (duplicate username, ID, or email).')
        for err in errors:
            messages.error(request, err)

        return redirect('add_student')

    return redirect('add_student')


# ─── CSV Import: Faculty ───────────────────────────────────────────────────────
@login_required_role('admin')
def sample_faculty_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_faculty.csv"'
    writer = csv.writer(response)
    writer.writerow(['first_name', 'last_name', 'faculty_id', 'email',
                     'username', 'password', 'department',
                     'phone_number', 'dob', 'address'])
    writer.writerow(['Jane', 'Smith', 'FAC001', 'jane@example.com',
                     'janesmith', 'pass123', 'BCA',
                     '9876543210', '1985-08-20', '456 College Rd'])
    return response


@login_required_role('admin')
def import_faculty_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid .csv file.')
            return redirect('add_faculty')

        decoded = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)

        success_count = 0
        skip_count = 0
        errors = []

        for i, row in enumerate(reader, start=2):
            try:
                username   = row.get('username', '').strip()
                faculty_id = row.get('faculty_id', '').strip()
                email      = row.get('email', '').strip()

                # Skip duplicates
                if User.objects.filter(username=username).exists():
                    skip_count += 1
                    continue
                if Faculty.objects.filter(faculty_id=faculty_id).exists():
                    skip_count += 1
                    continue
                if Faculty.objects.filter(email=email).exists():
                    skip_count += 1
                    continue

                user = User(username=username, role='faculty')
                user.set_password(row.get('password', '').strip())
                user.save()

                Faculty.objects.create(
                    user=user,
                    faculty_id=faculty_id,
                    first_name=row.get('first_name', '').strip(),
                    last_name=row.get('last_name', '').strip(),
                    email=email,
                    department=row.get('department', '').strip(),
                    phone_number=row.get('phone_number', '').strip(),
                    address=row.get('address', '').strip(),
                    dob=row.get('dob', '').strip() or None,
                )
                success_count += 1

            except Exception as e:
                errors.append(f'Row {i}: {e}')

        if success_count:
            messages.success(request, f'{success_count} faculty member(s) imported successfully.')
        if skip_count:
            messages.warning(request, f'{skip_count} row(s) skipped (duplicate username, ID, or email).')
        for err in errors:
            messages.error(request, err)

        return redirect('add_faculty')

    return redirect('add_faculty')
# ─── CSV: Sample Scores ────────────────────────────────────────────────────────
@login_required_role('faculty')
def sample_scores_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_scores.csv"'
    writer = csv.writer(response)
    writer.writerow(['student_id', 'semester', 'previous_exam_marks',
                     'internal_test_marks', 'assignment_score',
                     'quiz_score', 'attendance_percentage', 'class_participation'])
    writer.writerow(['STU001', '1', '75', '80', '90', '85', '95', '70'])
    writer.writerow(['STU002', '1', '60', '65', '70', '55', '80', '60'])
    return response


# ─── CSV: Import Scores ────────────────────────────────────────────────────────
@login_required_role('faculty')
def import_scores_csv(request):
    if request.method == 'POST':
        user = get_current_user(request)
        faculty = get_object_or_404(Faculty, user=user)
        csv_file = request.FILES.get('csv_file')

        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid .csv file.')
            return redirect('upload_scores')

        decoded = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)

        success_count = 0
        skip_count = 0
        errors = []

        for i, row in enumerate(reader, start=2):
            try:
                student_id = row.get('student_id', '').strip()
                semester   = row.get('semester', '').strip()

                # Only allow students in faculty's department
                student = Student.objects.filter(
                    student_id=student_id,
                    department=faculty.department
                ).first()

                if not student:
                    skip_count += 1
                    errors.append(f'Row {i}: Student "{student_id}" not found in your department — skipped.')
                    continue

                score, _ = Score.objects.get_or_create(
                    student=student,
                    semester=semester,
                    defaults={'faculty': faculty}
                )
                score.faculty                = faculty
                score.previous_exam_marks    = float(row.get('previous_exam_marks', 0) or 0)
                score.internal_test_marks    = float(row.get('internal_test_marks', 0) or 0)
                score.assignment_score       = float(row.get('assignment_score', 0) or 0)
                score.quiz_score             = float(row.get('quiz_score', 0) or 0)
                score.attendance_percentage  = float(row.get('attendance_percentage', 0) or 0)
                score.class_participation    = float(row.get('class_participation', 0) or 0)
                score.save()

                Notification.objects.create(
                    student=student,
                    message=f"Your marks for Semester {semester} have been uploaded/updated by {faculty.get_full_name()}."
                )
                success_count += 1

            except Exception as e:
                errors.append(f'Row {i}: {e}')

        if success_count:
            messages.success(request, f'{success_count} score record(s) imported successfully.')
        if skip_count:
            messages.warning(request, f'{skip_count} row(s) skipped.')
        for err in errors:
            messages.error(request, err)

        return redirect('upload_scores')

    return redirect('upload_scores')