from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import uuid
import threading
import pandas as pd

from models.database import db, Submission, DailySubmissionCount
from services.evaluator import RMSEEvaluator

submission_bp = Blueprint('submission', __name__)

def allowed_file(filename: str) -> bool:
    """허용된 파일 확장자 확인"""
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in
        current_app.config['ALLOWED_EXTENSIONS']
    )

def check_daily_limit(user_id: int):
    """
    일일 제출 횟수 확인
    Returns: (가능 여부, 남은 횟수)
    """
    today       = date.today()
    max_per_day = current_app.config['MAX_SUBMISSIONS_PER_DAY']

    record = DailySubmissionCount.query.filter_by(
        user_id=user_id,
        date=today
    ).first()

    if not record:
        return True, max_per_day

    remaining = max_per_day - record.count
    return remaining > 0, remaining

def increment_daily_count(user_id: int):
    """일일 제출 횟수 증가"""
    today  = date.today()
    record = DailySubmissionCount.query.filter_by(
        user_id=user_id,
        date=today
    ).first()

    if not record:
        record = DailySubmissionCount(
            user_id=user_id,
            date=today,
            count=0
        )
        db.session.add(record)

    record.count += 1
    db.session.commit()

def process_submission_async(app, submission_id: int, file_path: str):
    """
    비동기 채점 처리
    별도 스레드에서 RMSE 계산 후 DB 업데이트
    """
    with app.app_context():
        submission = Submission.query.get(submission_id)
        if not submission:
            return

        try:
            submission.status = 'processing'
            db.session.commit()

            # RMSE 평가
            evaluator = RMSEEvaluator(
                ground_truth_path=current_app.config['GROUND_TRUTH_PATH'],
                public_ratio=current_app.config['LEADERBOARD_PUBLIC_RATIO']
            )
            scores = evaluator.evaluate(file_path)

            # 결과 저장
            submission.public_rmse  = scores['public_rmse']
            submission.private_rmse = scores['private_rmse']
            submission.status       = 'completed'

        except Exception as e:
            submission.status        = 'failed'
            submission.error_message = str(e)

        finally:
            db.session.commit()
            # 채점 완료 후 파일 삭제 (선택적)
            # os.remove(file_path)


@submission_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit():
    """파일 제출 및 채점 요청"""
    user_id = get_jwt_identity()

    # 1. 일일 제출 횟수 확인
    can_submit, remaining = check_daily_limit(user_id)
    if not can_submit:
        return jsonify({
            'success': False,
            'message': f'일일 제출 횟수({current_app.config["MAX_SUBMISSIONS_PER_DAY"]}회)를 초과했습니다.'
        }), 429

    # 2. 파일 확인
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '파일명이 없습니다.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'CSV 파일만 업로드 가능합니다.'}), 400

    # 3. 파일 저장
    original_filename = secure_filename(file.filename)
    unique_filename   = f"{uuid.uuid4().hex}_{original_filename}"
    upload_folder     = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    file_path         = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    # 4. 제출 기록 생성
    description = request.form.get('description', '')
    submission  = Submission(
        user_id           = user_id,
        filename          = unique_filename,
        original_filename = original_filename,
        description       = description,
        status            = 'pending'
    )
    db.session.add(submission)
    db.session.commit()

    # 5. 일일 횟수 증가
    increment_daily_count(user_id)

    # 6. 비동기 채점 시작
    app = current_app._get_current_object()
    thread = threading.Thread(
        target=process_submission_async,
        args=(app, submission.id, file_path)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success':        True,
        'message':        '제출이 완료되었습니다. 채점 중입니다.',
        'submission_id':  submission.id,
        'remaining_today': remaining - 1
    }), 201


@submission_bp.route('/submissions', methods=['GET'])
@jwt_required()
def get_my_submissions():
    """내 제출 목록 조회"""
    user_id     = get_jwt_identity()
    page        = request.args.get('page', 1, type=int)
    per_page    = request.args.get('per_page', 10, type=int)

    submissions = Submission.query.filter_by(user_id=user_id)\
                    .order_by(Submission.submitted_at.desc())\
                    .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'data': {
            'submissions': [s.to_dict() for s in submissions.items],
            'total':       submissions.total,
            'pages':       submissions.pages,
            'current_page': page
        }
    })


@submission_bp.route('/submissions/<int:submission_id>/status', methods=['GET'])
@jwt_required()
def get_submission_status(submission_id: int):
    """특정 제출 상태 조회 (폴링용)"""
    user_id    = get_jwt_identity()
    submission = Submission.query.filter_by(
        id=submission_id,
        user_id=user_id
    ).first()

    if not submission:
        return jsonify({'success': False, 'message': '제출 내역을 찾을 수 없습니다.'}), 404

    return jsonify({
        'success': True,
        'data': {
            'status':      submission.status,
            'public_rmse': round(submission.public_rmse, 4) if submission.public_rmse else None,
            'error':       submission.error_message
        }
    })


@submission_bp.route('/submissions/<int:submission_id>/select', methods=['POST'])
@jwt_required()
def select_submission(submission_id: int):
    """최종 제출 선택 (Private 리더보드용)"""
    user_id    = get_jwt_identity()
    submission = Submission.query.filter_by(
        id=submission_id,
        user_id=user_id
    ).first()

    if not submission:
        return jsonify({'success': False, 'message': '제출 내역을 찾을 수 없습니다.'}), 404

    if submission.status != 'completed':
        return jsonify({'success': False, 'message': '채점이 완료된 제출만 선택 가능합니다.'}), 400

    # 기존 선택 해제
    Submission.query.filter_by(user_id=user_id, is_selected=True)\
        .update({'is_selected': False})

    # 새로운 선택
    submission.is_selected = True
    db.session.commit()

    return jsonify({'success': True, 'message': '최종 제출이 선택되었습니다.'})


@submission_bp.route('/daily-limit', methods=['GET'])
@jwt_required()
def get_daily_limit():
    """오늘 남은 제출 횟수 조회"""
    user_id              = get_jwt_identity()
    can_submit, remaining = check_daily_limit(user_id)

    return jsonify({
        'success':   True,
        'data': {
            'max_per_day': current_app.config['MAX_SUBMISSIONS_PER_DAY'],
            'remaining':   remaining,
            'can_submit':  can_submit
        }
    })
