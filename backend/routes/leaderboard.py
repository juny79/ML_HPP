from flask import Blueprint, request, jsonify

from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from sqlalchemy import func



from models.database import db, Submission, User



leaderboard_bp = Blueprint('leaderboard', __name__)



def get_public_leaderboard_data():

    """

    Public 리더보드 데이터 조회

    - 유저별 최고 점수(최저 RMSE) 기준

    - 동점 시 먼저 달성한 순서

    """

    # 유저별 최저 public_rmse 서브쿼리

    best_scores = db.session.query(

        Submission.user_id,

        func.min(Submission.public_rmse).label('best_rmse')

    ).filter(

        Submission.status == 'completed',

        Submission.public_rmse.isnot(None)

    ).group_by(Submission.user_id).subquery()



    # 해당 점수의 제출 시간 조회

    results = db.session.query(

        User.username,

        User.team_name,

        best_scores.c.best_rmse,

        func.min(Submission.submitted_at).label('achieved_at'),

        func.count(Submission.id).label('submission_count')

    ).join(

        best_scores, User.id == best_scores.c.user_id

    ).join(

        Submission,

        (Submission.user_id == best_scores.c.user_id) &

        (Submission.public_rmse == best_scores.c.best_rmse) &

        (Submission.status == 'completed')

    ).group_by(

        User.username,

        User.team_name,

        best_scores.c.best_rmse

    ).order_by(

        best_scores.c.best_rmse.asc(),

        func.min(Submission.submitted_at).asc()

    ).all()



    leaderboard = []

    for rank, row in enumerate(results, start=1):

        leaderboard.append({

            'rank':             rank,

            'username':         row.username,

            'team_name':        row.team_name or row.username,

            'public_rmse':      round(row.best_rmse, 4),

            'submission_count': row.submission_count,

            'achieved_at':      row.achieved_at.isoformat()

        })



    return leaderboard





def get_private_leaderboard_data():

    """

    Private 리더보드 데이터 조회

    - is_selected=True인 제출 기준

    - 선택 안 한 경우 최고 점수 자동 선택

    """

    results = []



    users = User.query.filter_by(is_admin=False).all()



    for user in users:

        # 선택된 제출 우선

        selected = Submission.query.filter_by(

            user_id=user.id,

            is_selected=True,

            status='completed'

        ).first()



        if not selected:

            # 선택 없으면 최고 점수 자동 선택

            selected = Submission.query.filter_by(

                user_id=user.id,

                status='completed'

            ).filter(

                Submission.private_rmse.isnot(None)

            ).order_by(Submission.private_rmse.asc()).first()



        if selected and selected.private_rmse:

            results.append({

                'username':      user.username,

                'team_name':     user.team_name or user.username,

                'private_rmse':  selected.private_rmse,

                'public_rmse':   selected.public_rmse,

                'submitted_at':  selected.submitted_at.isoformat(),

                'is_selected':   selected.is_selected

            })



    # private_rmse 기준 정렬

    results.sort(key=lambda x: x['private_rmse'])



    for rank, row in enumerate(results, start=1):

        row['rank']          = rank

        row['private_rmse']  = round(row['private_rmse'], 4)

        row['public_rmse']   = round(row['public_rmse'], 4)



    return results





@leaderboard_bp.route('/leaderboard/public', methods=['GET'])

def public_leaderboard():

    """Public 리더보드 조회 (로그인 불필요)"""

    try:

        page     = request.args.get('page', 1, type=int)

        per_page = request.args.get('per_page', 20, type=int)



        data     = get_public_leaderboard_data()



        # 페이지네이션

        total    = len(data)

        start    = (page - 1) * per_page

        end      = start + per_page

        paginated = data[start:end]



        return jsonify({

            'success': True,

            'data': {

                'leaderboard':  paginated,

                'total':        total,

                'pages':        (total + per_page - 1) // per_page,

                'current_page': page,

                'type':         'public'

            }

        })



    except Exception as e:

        return jsonify({'success': False, 'message': str(e)}), 500





@leaderboard_bp.route('/leaderboard/private', methods=['GET'])

@jwt_required()

def private_leaderboard():

    """

    Private 리더보드 조회 (관리자만)

    대회 종료 후 공개

    """

    user_id = get_jwt_identity()

    user    = User.query.get(user_id)



    if not user or not user.is_admin:

        return jsonify({

            'success': False,

            'message': '관리자만 접근 가능합니다.'

        }), 403



    try:

        data = get_private_leaderboard_data()

        return jsonify({

            'success': True,

            'data': {

                'leaderboard': data,

                'total':       len(data),

                'type':        'private'

            }

        })



    except Exception as e:

        return jsonify({'success': False, 'message': str(e)}), 500





@leaderboard_bp.route('/leaderboard/my-rank', methods=['GET'])

@jwt_required()

def my_rank():

    """내 현재 순위 조회"""

    user_id  = get_jwt_identity()

    user     = User.query.get(user_id)



    data     = get_public_leaderboard_data()

    my_entry = next(

        (row for row in data if row['username'] == user.username),

        None

    )



    if not my_entry:

        return jsonify({

            'success': True,

            'data': {

                'rank':        None,

                'public_rmse': None,

                'message':     '아직 유효한 제출이 없습니다.'

            }

        })



    return jsonify({

        'success': True,

        'data': {

            'rank':             my_entry['rank'],

            'public_rmse':      my_entry['public_rmse'],

            'submission_count': my_entry['submission_count'],

            'total_participants': len(data)

        }

    })

