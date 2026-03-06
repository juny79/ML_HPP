"""
베이스라인 코드
서울시 아파트 실거래가 예측 - House Price Prediction
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
import warnings
warnings.filterwarnings('ignore')


# =============================================
# 1. 데이터 로드
# =============================================
def load_data(train_path: str, test_path: str):
    """
    학습/테스트 데이터 로드
    
    Args:
        train_path : 학습 데이터 경로
        test_path  : 테스트 데이터 경로
    Returns:
        train_df, test_df
    """
    train_df = pd.read_csv(train_path)
    test_df  = pd.read_csv(test_path)

    print(f"학습 데이터 shape : {train_df.shape}")
    print(f"테스트 데이터 shape: {test_df.shape}")

    return train_df, test_df


# =============================================
# 2. 전처리
# =============================================
def preprocess(
    train_df : pd.DataFrame,
    test_df  : pd.DataFrame,
    target_col: str = 'target'
):
    """
    기본 전처리
    - 결측값 처리
    - 범주형 인코딩
    - 학습/테스트 분리
    
    Args:
        train_df   : 학습 데이터
        test_df    : 테스트 데이터
        target_col : 타겟 컬럼명
    Returns:
        X_train, y_train, X_test
    """
    # 타겟 분리
    y_train  = train_df[target_col].copy()
    train_df = train_df.drop(columns=[target_col])

    # 학습/테스트 합치기 (일관된 전처리)
    n_train  = len(train_df)
    combined = pd.concat([train_df, test_df], axis=0).reset_index(drop=True)

    # 범주형 컬럼 인코딩
    cat_cols = combined.select_dtypes(include=['object']).columns.tolist()
    print(f"\n범주형 컬럼 ({len(cat_cols)}개): {cat_cols}")

    le = LabelEncoder()
    for col in cat_cols:
        combined[col] = combined[col].astype(str)
        combined[col] = le.fit_transform(combined[col])

    # 결측값 처리 (중앙값으로 대체)
    num_cols     = combined.select_dtypes(include=[np.number]).columns
    missing_cols = combined[num_cols].columns[combined[num_cols].isnull().any()]

    if len(missing_cols) > 0:
        print(f"결측값 처리 컬럼 ({len(missing_cols)}개): {list(missing_cols)}")
        for col in missing_cols:
            median_val      = combined[col].median()
            combined[col]   = combined[col].fillna(median_val)

    # 학습/테스트 재분리
    X_train = combined.iloc[:n_train].copy()
    X_test  = combined.iloc[n_train:].copy()

    print(f"\n전처리 완료")
    print(f"  X_train shape: {X_train.shape}")
    print(f"  X_test  shape: {X_test.shape}")

    return X_train, y_train, X_test


# =============================================
# 3. 모델 학습
# =============================================
def train_model(
    X_train : pd.DataFrame,
    y_train : pd.Series,
    params  : dict = None
):
    """
    RandomForest 모델 학습
    
    Args:
        X_train : 학습 피처
        y_train : 학습 타겟
        params  : 모델 하이퍼파라미터
    Returns:
        학습된 모델
    """
    if params is None:
        params = {
            'n_estimators'  : 100,
            'max_depth'     : 10,
            'min_samples_split': 5,
            'random_state'  : 42,
            'n_jobs'        : -1,
        }

    print(f"\n모델 학습 시작...")
    print(f"  파라미터: {params}")

    model = RandomForestRegressor(**params)
    model.fit(X_train, y_train)

    # 학습 데이터 RMSE
    train_pred = model.predict(X_train)
    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    print(f"  Train RMSE: {train_rmse:,.2f}")

    return model


# =============================================
# 4. 예측 & 제출 파일 생성
# =============================================
def predict_and_save(
    model       : RandomForestRegressor,
    X_test      : pd.DataFrame,
    output_path : str = 'submission.csv'
):
    """
    예측 및 제출 파일 저장
    
    Args:
        model       : 학습된 모델
        X_test      : 테스트 피처
        output_path : 저장 경로
    Returns:
        submission DataFrame
    """
    preds = model.predict(X_test)

    # 음수 예측값 처리 (아파트 가격은 양수)
    preds = np.maximum(preds, 0).astype(int)

    submission = pd.DataFrame({
        'index':  range(len(preds)),
        'target': preds
    })

    submission.to_csv(output_path, index=False)

    print(f"\n제출 파일 저장 완료: {output_path}")
    print(f"  예측값 평균  : {preds.mean():,.0f} 만원")
    print(f"  예측값 중앙값: {np.median(preds):,.0f} 만원")
    print(f"  예측값 최솟값: {preds.min():,.0f} 만원")
    print(f"  예측값 최댓값: {preds.max():,.0f} 만원")

    return submission


# =============================================
# 5. 피처 중요도 출력
# =============================================
def print_feature_importance(
    model    : RandomForestRegressor,
    X_train  : pd.DataFrame,
    top_n    : int = 20
):
    """
    상위 N개 피처 중요도 출력
    
    Args:
        model   : 학습된 모델
        X_train : 학습 피처
        top_n   : 출력할 피처 수
    """
    importance_df = pd.DataFrame({
        'feature':    X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False).head(top_n)

    print(f"\n피처 중요도 Top {top_n}")
    print("-" * 40)
    for _, row in importance_df.iterrows():
        bar = "█" * int(row['importance'] * 100)
        print(f"  {row['feature']:<30} {row['importance']:.4f} {bar}")


# =============================================
# 메인 실행
# =============================================
if __name__ == '__main__':
    # 경로 설정
    TRAIN_PATH  = 'data/train.csv'
    TEST_PATH   = 'data/test.csv'
    OUTPUT_PATH = 'submission.csv'
    TARGET_COL  = 'target'

    print("=" * 50)
    print("  House Price Prediction - Baseline")
    print("=" * 50)

    # 1. 데이터 로드
    train_df, test_df = load_data(TRAIN_PATH, TEST_PATH)

    # 2. 전처리
    X_train, y_train, X_test = preprocess(train_df, test_df, TARGET_COL)

    # 3. 모델 학습
    model = train_model(X_train, y_train)

    # 4. 피처 중요도
    print_feature_importance(model, X_train)

    # 5. 예측 & 저장
    submission = predict_and_save(model, X_test, OUTPUT_PATH)

    print("\n" + "=" * 50)
    print("  완료! submission.csv를 리더보드에 제출하세요.")
    print("=" * 50)
