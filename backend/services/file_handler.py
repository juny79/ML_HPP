import os
import uuid
import pandas as pd
import logging
from werkzeug.utils import secure_filename
from typing import Tuple

logger = logging.getLogger(__name__)


class FileHandler:
    """파일 업로드 및 관리 서비스"""

    ALLOWED_EXTENSIONS = {'csv'}
    MAX_FILE_SIZE_MB   = 16

    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)

    def allowed_file(self, filename: str) -> bool:
        """허용된 확장자 확인"""
        return (
            '.' in filename and
            filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
        )

    def save_file(self, file) -> Tuple[str, str]:
        """
        파일 저장
        Returns:
            (unique_filename, file_path)
        """
        original_filename = secure_filename(file.filename)
        unique_filename   = f"{uuid.uuid4().hex}_{original_filename}"
        file_path         = os.path.join(self.upload_folder, unique_filename)

        file.save(file_path)
        logger.info(f"파일 저장 완료: {file_path}")

        return unique_filename, file_path

    def validate_csv_format(
        self,
        file_path: str,
        required_columns: list,
        expected_rows: int
    ) -> Tuple[bool, str]:
        """
        CSV 파일 형식 검증
        Returns:
            (is_valid, message)
        """
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            return False, f"CSV 파일 읽기 실패: {str(e)}"

        # 컬럼 확인
        missing_cols = [c for c in required_columns if c not in df.columns]
        if missing_cols:
            return False, f"필수 컬럼 누락: {missing_cols}"

        # 행 수 확인
        if len(df) != expected_rows:
            return False, (
                f"행 수 불일치 - "
                f"예상: {expected_rows}개, "
                f"실제: {len(df)}개"
            )

        # 결측값 확인
        for col in required_columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                return False, f"'{col}' 컬럼에 결측값 {null_count}개 존재"

        return True, "유효한 파일입니다."

    def delete_file(self, file_path: str) -> bool:
        """파일 삭제"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"파일 삭제 완료: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"파일 삭제 실패: {str(e)}")
            return False

    def get_file_size_mb(self, file_path: str) -> float:
        """파일 크기 반환 (MB)"""
        return os.path.getsize(file_path) / (1024 * 1024)

    def cleanup_old_files(self, days: int = 30):
        """
        오래된 파일 정리
        Args:
            days: 보관 기간 (일)
        """
        import time
        now        = time.time()
        cutoff     = now - (days * 86400)
        deleted    = 0

        for filename in os.listdir(self.upload_folder):
            file_path = os.path.join(self.upload_folder, filename)
            if os.path.isfile(file_path):
                if os.path.getmtime(file_path) < cutoff:
                    os.remove(file_path)
                    deleted += 1

        logger.info(f"오래된 파일 {deleted}개 삭제 완료")
        return deleted
