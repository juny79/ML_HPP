import pandas as pd
import numpy as np
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)

class RMSEEvaluator:
    """
    RMSE 기반 평가 서비스
    
    Public/Private 리더보드 분리 평가 지원
    """
    
    def __init__(self, ground_truth_path: str, public_ratio: float = 0.5):
        """
        Args:
            ground_truth_path : 정답 CSV 파일 경로
            public_ratio      : Public 리더보드에 사용할 데이터 비율
        """
        self.ground_truth_path = ground_truth_path
        self.public_ratio      = public_ratio
        self._load_ground_truth()
    
    def _load_ground_truth(self):
        """정답 데이터 로드 및 Public/Private 분리"""
        try:
            df = pd.read_csv(self.ground_truth_path)
            
            # 필수 컬럼 검증
            required_columns = ['index', 'target']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"정답 파일에 필수 컬럼이 없습니다: {required_columns}")
            
            df = df.sort_values('index').reset_index(drop=True)
            
            # Public/Private 분리 (앞 50%: Public, 뒤 50%: Private)
            split_idx = int(len(df) * self.public_ratio)
            
            self.public_truth  = df.iloc[:split_idx].copy()
            self.private_truth = df.iloc[split_idx:].copy()
            self.full_truth    = df.copy()
            
            logger.info(
                f"정답 데이터 로드 완료 - "
                f"전체: {len(df)}, "
                f"Public: {len(self.public_truth)}, "
                f"Private: {len(self.private_truth)}"
            )
            
        except Exception as e:
            logger.error(f"정답 데이터 로드 실패: {str(e)}")
            raise
    
    def _calculate_rmse(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray
    ) -> float:
        """
        RMSE 계산
        
        RMSE = sqrt(1/n * Σ(y_i - ŷ_i)²)
        """
        if len(y_true) != len(y_pred):
            raise ValueError(
                f"배열 길이 불일치: y_true={len(y_true)}, y_pred={len(y_pred)}"
            )
        
        squared_errors = (y_true - y_pred) ** 2
        mse            = np.mean(squared_errors)
        rmse           = np.sqrt(mse)
        
        return float(rmse)
    
    def validate_submission(
        self, 
        submission_df: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        제출 파일 유효성 검사
        
        Returns:
            (is_valid, error_message)
        """
        # 1. 필수 컬럼 확인
        required_cols = ['index', 'target']
        missing_cols  = [col for col in required_cols if col not in submission_df.columns]
        if missing_cols:
            return False, f"필수 컬럼 누락: {missing_cols}"
        
        # 2. 행 수 확인
        expected_rows = len(self.full_truth)
        if len(submission_df) != expected_rows:
            return False, (
                f"행 수 불일치: 예상 {expected_rows}개, "
                f"제출 {len(submission_df)}개"
            )
        
        # 3. 결측값 확인
        if submission_df['target'].isnull().any():
            null_count = submission_df['target'].isnull().sum()
            return False, f"target 컬럼에 결측값 {null_count}개 존재"
        
        # 4. 숫자형 확인
        try:
            submission_df['target'] = pd.to_numeric(submission_df['target'])
        except ValueError:
            return False, "target 컬럼에 숫자가 아닌 값이 존재합니다"
        
        # 5. 음수값 확인 (아파트 가격은 양수여야 함)
        if (submission_df['target'] < 0).any():
            return False, "target 컬럼에 음수값이 존재합니다"
        
        # 6. index 확인
        submission_indices = set(submission_df['index'].values)
        truth_indices      = set(self.full_truth['index'].values)
        if submission_indices != truth_indices:
            return False, "index 값이 정답 데이터와 일치하지 않습니다"
        
        return True, "유효한 제출 파일입니다"
    
    def evaluate(
        self, 
        submission_path: str
    ) -> Dict[str, float]:
        """
        제출 파일 평가
        
        Returns:
            {
                'public_rmse'  : float,
                'private_rmse' : float,
                'total_rmse'   : float
            }
        """
        # 제출 파일 로드
        submission_df = pd.read_csv(submission_path)
        
        # 유효성 검사
        is_valid, message = self.validate_submission(submission_df)
        if not is_valid:
            raise ValueError(message)
        
        # index 기준 정렬
        submission_df = submission_df.sort_values('index').reset_index(drop=True)
        
        # Public RMSE 계산
        public_pred   = submission_df[
            submission_df['index'].isin(self.public_truth['index'])
        ]['target'].values
        public_true   = self.public_truth['target'].values
        public_rmse   = self._calculate_rmse(public_true, public_pred)
        
        # Private RMSE 계산
        private_pred  = submission_df[
            submission_df['index'].isin(self.private_truth['index'])
        ]['target'].values
        private_true  = self.private_truth['target'].values
        private_rmse  = self._calculate_rmse(private_true, private_pred)
        
        # 전체 RMSE 계산
        total_rmse    = self._calculate_rmse(
            self.full_truth['target'].values,
            submission_df['target'].values
        )
        
        logger.info(
            f"평가 완료 - "
            f"Public RMSE: {public_rmse:.4f}, "
            f"Private RMSE: {private_rmse:.4f}, "
            f"Total RMSE: {total_rmse:.4f}"
        )
        
        return {
            'public_rmse':  public_rmse,
            'private_rmse': private_rmse,
            'total_rmse':   total_rmse
        }
