"""
Run this once from your project root:
    python core/ml/train_model.py
 
Place student_learning_dataset_2000.csv in core/ml/ folder.
"""
 
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os
 
BASE_DIR = os.path.dirname(__file__)
 
FEATURES = [
    'Previous_Exam_Marks', 'Internal_Test_Marks',
    'Assignment_Score', 'Quiz_Score',
    'Attendance_Percentage', 'Class_Participation'
]
 
df = pd.read_csv(os.path.join(BASE_DIR, 'student_learning_dataset_2000.csv'))
 
X_rows, y_rows = [], []
 
for student_id, group in df.groupby('Student_ID'):
    group = group.sort_values('Semester')
 
    for target_sem in range(2, 7):          # predict sem 2,3,4,5,6
        prior   = group[group['Semester'] < target_sem]
        current = group[group['Semester'] == target_sem]
 
        if prior.empty or current.empty:
            continue
 
        # X = average of all prior semesters' feature values
        avg_features = prior[FEATURES].mean().values
        # y = category of the target semester
        label = current['Predicted_Category'].values[0]
 
        X_rows.append(avg_features)
        y_rows.append(label)
 
X = np.array(X_rows)
y = np.array(y_rows)
 
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
 
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
 
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"✅ Model Accuracy : {round(acc * 100, 2)}%")
print(classification_report(y_test, y_pred))
 
with open(os.path.join(BASE_DIR, 'student_model.pkl'), 'wb') as f:
    pickle.dump(model, f)
 
print("✅ Model saved to core/ml/student_model.pkl")