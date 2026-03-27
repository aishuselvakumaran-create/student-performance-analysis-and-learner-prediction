# EduTrack – Student Performance Management System

A full-stack Django web application for managing student academic performance with role-based dashboards for Admin, Faculty, and Students.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations core
python manage.py migrate
```

### 3. Seed the Database
```bash
python setup.py
```

### 4. Start the Server
```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000**

---

## 🔑 Default Credentials

| Role    | Username  | Password    |
|---------|-----------|-------------|
| Admin   | admin     | admin123    |
| Faculty | faculty1  | faculty123  |
| Faculty | faculty2  | faculty123  |
| Student | student1  | student123  |
| Student | student2  | student123  |
| Student | student3  | student123  |

---

## 📁 Project Structure

```
student_mgmt/
├── core/                   # Main Django app
│   ├── models.py           # User, Faculty, Student, Score, Notification
│   ├── views.py            # All role-based views
│   ├── urls.py             # URL routing
│   └── admin.py
├── student_mgmt/           # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/
│   ├── login.html          # Beautiful gradient login page
│   ├── base.html           # Shared layout with sidebar
│   ├── admin_panel/        # Admin templates
│   ├── faculty/            # Faculty templates
│   └── student/            # Student templates
├── manage.py
├── setup.py                # Database seeder
└── requirements.txt
```

---

## 🎯 Features

### 👨‍💼 Admin Dashboard
- Total student & faculty counts
- Department-wise bar charts
- Add / View / Edit / Delete Students & Faculty
- Search & filter by department, semester, name
- View student mark lists with learner category
- Click any student to see semester-wise charts

### 👩‍🏫 Faculty Dashboard
- Department overview with student distribution chart
- Upload scores per semester (Previous Exam, Internal Test, Assignment, Quiz, Attendance, Participation)
- Pre-fills existing scores for editing
- View all student results with search & filter
- Click any student for detailed charts

### 🎓 Student Dashboard
- Personal analytics: overall %, learner category
- Line chart (all semesters), Radar chart (latest sem), Bar chart (averages)
- Semester-wise mark sheet with progress bars
- Profile page
- Notifications when marks are uploaded

---

## 🏗️ Models

- **User** – Login credentials with role (admin / faculty / student)
- **Faculty** – Faculty profile linked to User
- **Student** – Student profile linked to User
- **Score** – Per-student per-semester marks (6 indicators)
- **Notification** – Alerts sent to students on mark upload

---

## 🎨 Tech Stack

- **Backend:** Django 4.2, SQLite
- **Frontend:** HTML5, CSS3 (custom design system), Vanilla JS
- **Charts:** Chart.js (Line, Bar, Doughnut, Radar)
- **Icons:** Font Awesome 6
- **Fonts:** Google Fonts (Inter)
