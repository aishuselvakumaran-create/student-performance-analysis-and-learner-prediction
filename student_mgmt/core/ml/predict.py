import pickle
import os
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'student_model.pkl')
_model = None

FEATURES = [
    'previous_exam_marks', 'internal_test_marks',
    'assignment_score', 'quiz_score',
    'attendance_percentage', 'class_participation'
]


def load_model():
    global _model
    if _model is None:
        with open(MODEL_PATH, 'rb') as f:
            _model = pickle.load(f)
    return _model


def get_trend(scores_ordered):
    """
    Compares average of first half semesters vs second half.
    Returns: 'improving', 'declining', or 'stable'
    """
    if len(scores_ordered) < 2:
        return 'stable'

    avgs = []
    for s in scores_ordered:
        vals = [getattr(s, f) for f in FEATURES]
        avgs.append(sum(vals) / len(vals))

    mid = len(avgs) // 2
    first_half  = sum(avgs[:mid]) / mid
    second_half = sum(avgs[mid:]) / (len(avgs) - mid)
    diff = second_half - first_half

    if diff > 5:
        return 'improving'
    elif diff < -5:
        return 'declining'
    return 'stable'


def get_next_year_category(current_category, improvement):
    """Your exact next-year logic."""
    if current_category == 'Slow Learner' and improvement > 5:
        return 'Average Learner'
    elif current_category == 'Average Learner' and improvement > 8:
        return 'Fast Learner'
    elif current_category == 'Fast Learner':
        return 'Fast Learner'
    else:
        return current_category


def predict_for_semester(scores_queryset, predict_sem):
    model = load_model()

    all_scores   = list(scores_queryset.order_by('semester'))
    prior_scores = [s for s in all_scores if int(s.semester) < predict_sem]

    if not prior_scores:
        return {
            'error': f'No scores found before Semester {predict_sem}. '
                     f'Please upload Semester {predict_sem - 1} marks first.'
        }

    # ── NEW: Check all required semesters are present ──────────────
    uploaded_sems   = {int(s.semester) for s in prior_scores}
    required_sems   = set(range(1, predict_sem))   # {1} for sem2, {1,2} for sem3 etc.
    missing_sems    = required_sems - uploaded_sems

    if missing_sems:
        missing_str = ', '.join(f'Sem {s}' for s in sorted(missing_sems))
        return {
            'error': f'Missing scores for {missing_str}. '
                     f'Please upload those marks before predicting Semester {predict_sem}.'
        }
    # ──────────────────────────────────────────────────────────────

    n = len(prior_scores)
    averaged = []
    for f in FEATURES:
        averaged.append(sum(getattr(s, f) for s in prior_scores) / n)

    X = np.array(averaged).reshape(1, -1)

    predicted_category = model.predict(X)[0]
    proba              = model.predict_proba(X)[0]
    confidence         = round(max(proba) * 100, 1)

    avg_internal = sum(s.internal_test_marks for s in prior_scores) / n
    avg_previous = sum(s.previous_exam_marks for s in prior_scores) / n
    improvement  = round(avg_internal - avg_previous, 2)

    next_year_category = get_next_year_category(predicted_category, improvement)
    trend              = get_trend(prior_scores)

    return {
        'predicted_category' : predicted_category,
        'next_year_category' : next_year_category,
        'confidence'         : confidence,
        'improvement'        : improvement,
        'trend'              : trend,
        'based_on_sems'      : [int(s.semester) for s in prior_scores],
        'predicting_for_sem' : predict_sem,
    }