"""
setup.py  –  Run once after migrations to seed the database.
Usage:  python setup.py
"""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_mgmt.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import User, Faculty, Student, Score, Notification

def create_admin():
    if User.objects.filter(username='admin').exists():
        print("Admin already exists.")
        return
    u = User(username='admin', role='admin')
    u.set_password('admin123')
    u.save()
    print("✅ Admin created: admin / admin123")

def create_sample_faculty():
    data = [
        dict(username='faculty1', password='faculty123', faculty_id='FAC001',
             first_name='Priya', last_name='Sharma', email='priya@edu.com', department='BCA'),
        dict(username='faculty2', password='faculty123', faculty_id='FAC002',
             first_name='Rajan', last_name='Kumar', email='rajan@edu.com', department='MCA'),
    ]
    for d in data:
        if User.objects.filter(username=d['username']).exists():
            continue
        u = User(username=d['username'], role='faculty')
        u.set_password(d.pop('password'))
        u.save()
        Faculty.objects.create(user=u, **d)
        print(f"✅ Faculty: {d['username']}")

def create_sample_students():
    data = [
        dict(username='student1', password='student123', student_id='STU001',
             first_name='Arjun', last_name='Patel', email='arjun@edu.com',
             department='BCA', semester='3'),
        dict(username='student2', password='student123', student_id='STU002',
             first_name='Sneha', last_name='Nair', email='sneha@edu.com',
             department='BCA', semester='3'),
        dict(username='student3', password='student123', student_id='STU003',
             first_name='Rohit', last_name='Singh', email='rohit@edu.com',
             department='MCA', semester='2'),
    ]
    for d in data:
        if User.objects.filter(username=d['username']).exists():
            continue
        u = User(username=d['username'], role='student')
        u.set_password(d.pop('password'))
        u.save()
        Student.objects.create(user=u, **d)
        print(f"✅ Student: {d['username']}")

def create_sample_scores():
    faculty = Faculty.objects.first()
    for student in Student.objects.all():
        for sem in ['1', '2', '3']:
            if not Score.objects.filter(student=student, semester=sem).exists():
                import random
                sc = Score.objects.create(
                    student=student, faculty=faculty, semester=sem,
                    previous_exam_marks=round(random.uniform(55, 95), 1),
                    internal_test_marks=round(random.uniform(50, 90), 1),
                    assignment_score=round(random.uniform(60, 95), 1),
                    quiz_score=round(random.uniform(45, 90), 1),
                    attendance_percentage=round(random.uniform(60, 100), 1),
                    class_participation=round(random.uniform(50, 90), 1),
                )
                Notification.objects.create(
                    student=student,
                    message=f"Your marks for Semester {sem} have been uploaded."
                )
                print(f"✅ Scores for {student} sem {sem}")

if __name__ == '__main__':
    print("\n── EduTrack Database Setup ──")
    create_admin()
    create_sample_faculty()
    create_sample_students()
    create_sample_scores()
    print("\n✅ Setup complete!")
    print("   Admin:    admin / admin123")
    print("   Faculty:  faculty1 / faculty123")
    print("   Student:  student1 / student123")
