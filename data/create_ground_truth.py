"""
정답 데이터 생성 스크립트
실제 대회에서는 실제 정답 데이터로 교체 필요
"""
import pandas as pd
import numpy as np
import os

def create_sample_ground_truth(
    n_samples   : int   = 9272,
    output_path : str   = 'ground_truth.csv',
    random_seed : int   = 42
):
    """
    샘플 정답 데이터 생성
    
    Args:
        n_samples   : 샘플 수 (기본값: 9272)
        output_path : 저장 경로
        random_seed : 랜덤 시드
    """
    np.random.seed(random_seed)

    # 서울 아파트 실거래가 분포 시뮬레이션
    # 평균 8억, 표준편차 4억 (단위: 만원)
    prices = np.random.lognormal(
        mean  = np.log(80000),
        sigma = 0.6,
        size  = n_samples
    ).astype(int)

    # 최솟값 5000만원, 최댓값 300000만원으로 클리핑
    prices = np.clip(prices, 5000, 300000)

    df = pd.DataFrame({
        'index':  range(n_samples),
        'target': prices
    })

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"✅ 정답 데이터 생성 완료")
    print(f"   저장 경로  : {output_path}")
    print(f"   샘플 수    : {len(df):,}개")
    print(f"   가격 평균  : {prices.mean():,.0f} 만원")
    print(f"   가격 중앙값: {np.median(prices):,.0f} 만원")
    print(f"   가격 최솟값: {prices.min():,.0f} 만원")
    print(f"   가격 최댓값: {prices.max():,.0f} 만원")

    return df


def create_sample_submission(
    n_samples   : int = 9272,
    output_path : str = 'sample_submission.csv',
    random_seed : int = 99
):
    """
    샘플 제출 파일 생성 (참가자 배포용)
    
    Args:
        n_samples   : 샘플 수
        output_path : 저장 경로
        random_seed : 랜덤 시드
    """
    np.random.seed(random_seed)

    df = pd.DataFrame({
        'index':  range(n_samples),
        'target': np.zeros(n_samples, dtype=int)  # 0으로 초기화
    })

    df.to_csv(output_path, index=False)

    print(f"\n✅ 샘플 제출 파일 생성 완료")
    print(f"   저장 경로: {output_path}")
    print(f"   샘플 수  : {len(df):,}개")
    print(f"   ※ target 컬럼을 예측값으로 채워서 제출하세요.")

    return df


if __name__ == '__main__':
    # 정답 데이터 생성
    create_sample_ground_truth(
        n_samples   = 9272,
        output_path = 'ground_truth.csv'
    )

    # 샘플 제출 파일 생성
    create_sample_submission(
        n_samples   = 9272,
        output_path = 'sample_submission.csv'
    )
