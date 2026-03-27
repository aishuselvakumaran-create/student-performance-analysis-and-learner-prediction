from django.db import models
from django.contrib.auth.hashers import make_password, check_password


DEPARTMENT_CHOICES = [
    ('BCA', 'BCA'),
    ('MCA', 'MCA'),
    ('BSC', 'BSC'),
    ('BA', 'BA'),
    ('BCOM', 'BCOM'),
    ('BBM', 'BBM'),
    ('BBA', 'BBA'),
    ('MSC', 'MSC'),
]

SEMESTER_CHOICES = [(str(i), f'Semester {i}') for i in range(1, 7)]


class User(models.Model):
    ROLE_CHOICES = [('admin', 'Admin'), ('faculty', 'Faculty'), ('student', 'Student')]
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw):
        self.password = make_password(raw)

    def check_password(self, raw):
        return check_password(raw, self.password)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    faculty_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    dob = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.get_full_name()} - {self.faculty_id}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    dob = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_overall_percentage(self):
        scores = self.scores.all()
        if not scores:
            return 0
        fields = ['previous_exam_marks', 'internal_test_marks',
                  'assignment_score', 'quiz_score',
                  'attendance_percentage', 'class_participation']
        total = sum(
            sum(getattr(s, f) or 0 for f in fields) / len(fields)
            for s in scores
        )
        return round(total / scores.count(), 2)

   
    def __str__(self):
        return f"{self.get_full_name()} - {self.student_id}"
    def get_current_semester(self):
        scores = self.scores.all()
        if not scores.exists():
            return self.semester  # fallback to enrolled semester
        latest = max(int(s.semester) for s in scores)
        current = latest + 1
        return str(current) if current <= 6 else str(latest)

        


    

class Score(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='scores')
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='uploaded_scores')
    semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES)
    previous_exam_marks = models.FloatField(default=0)
    internal_test_marks = models.FloatField(default=0)
    assignment_score = models.FloatField(default=0)
    quiz_score = models.FloatField(default=0)
    attendance_percentage = models.FloatField(default=0)
    class_participation = models.FloatField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'semester')

    def get_average(self):
        fields = [self.previous_exam_marks, self.internal_test_marks,
                  self.assignment_score, self.quiz_score,
                  self.attendance_percentage, self.class_participation]
        return round(sum(fields) / len(fields), 2)

    def __str__(self):
        return f"{self.student} - Sem {self.semester}"


class Notification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notif → {self.student} : {self.message[:40]}"
