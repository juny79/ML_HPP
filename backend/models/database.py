from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    """사용자 모델"""
    __tablename__ = 'users'
    
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    team_name     = db.Column(db.String(100), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin      = db.Column(db.Boolean, default=False)
    
    # 관계 설정
    submissions = db.relationship('Submission', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.password_hash.encode('utf-8')
        )
    
    def to_dict(self):
        return {
            'id':         self.id,
            'username':   self.username,
            'email':      self.email,
            'team_name':  self.team_name,
            'created_at': self.created_at.isoformat()
        }


class Submission(db.Model):
    """제출 모델"""
    __tablename__ = 'submissions'
    
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename         = db.Column(db.String(255), nullable=False)
    original_filename= db.Column(db.String(255), nullable=False)
    
    # 점수 관련
    public_rmse      = db.Column(db.Float, nullable=True)   # Public 리더보드 점수
    private_rmse     = db.Column(db.Float, nullable=True)   # Private 리더보드 점수
    
    # 상태 관련
    status           = db.Column(
                           db.String(20), 
                           default='pending'
                       )  # pending, processing, completed, failed
    error_message    = db.Column(db.Text, nullable=True)
    
    # 메타데이터
    description      = db.Column(db.String(500), nullable=True)
    submitted_at     = db.Column(db.DateTime, default=datetime.utcnow)
    is_selected      = db.Column(db.Boolean, default=False)  # 최종 제출 선택 여부
    
    def to_dict(self):
        return {
            'id':                self.id,
            'user_id':           self.user_id,
            'username':          self.user.username,
            'team_name':         self.user.team_name,
            'public_rmse':       round(self.public_rmse, 4) if self.public_rmse else None,
            'private_rmse':      round(self.private_rmse, 4) if self.private_rmse else None,
            'status':            self.status,
            'description':       self.description,
            'submitted_at':      self.submitted_at.isoformat(),
            'is_selected':       self.is_selected
        }


class DailySubmissionCount(db.Model):
    """일일 제출 횟수 추적"""
    __tablename__ = 'daily_submission_counts'
    
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date       = db.Column(db.Date, nullable=False)
    count      = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='unique_user_date'),
    )

