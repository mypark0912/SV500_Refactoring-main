"""
EN50160 주간 리포트 데이터 가공 모듈

Parquet 데이터를 Chart.js용으로 변환
- 시계열 그래프 데이터
- 히스토그램 분포 데이터
- 통계 테이블 데이터
"""

import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


class NumpyEncoder(json.JSONEncoder):
    """Numpy 타입을 JSON으로 변환하는 인코더"""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


@dataclass
class WeeklyReportConfig:
    """주간 리포트 설정"""
    output_dir: str = "/usr/local/sv500/reports/weekly"
    bucket: str = "ntek30"
    measurement: str = "en10min"
    channels: List[str] = field(default_factory=lambda: ["Main", "Sub"])
    retention_weeks: int = 12


# EN50160 기준값 (60Hz 시스템 기준)
EN50160_LIMITS = {
    "frequency": {
        "nominal": 60.0,
        "limit_99_5": {"min": 59.40, "max": 60.60},  # ±1%
        "limit_100": {"min": 56.40, "max": 62.40},   # +4%/-6%
    },
    "voltage": {
        "nominal_percent": 100.0,
        "limit_95": {"min": 90.0, "max": 110.0},     # ±10%
        "limit_100": {"min": 85.0, "max": 110.0},    # -15%/+10%
    },
    "voltage_unbalance": {
        "limit_95": 2.0,  # 2% 미만
    },
    "thd": {
        "limit_95": 8.0,  # 8% 미만
    },
    "flicker": {
        "pst_limit": 1.0,
        "plt_limit_95": 1.0,
    },
    "harmonics": {
        # 각 고조파별 한계 (% of fundamental)
        "h2": 2.0, "h3": 5.0, "h4": 1.0, "h5": 6.0,
        "h6": 0.5, "h7": 5.0, "h8": 0.5, "h9": 1.5,
        "h10": 0.5, "h11": 3.5, "h12": 0.5, "h13": 3.0,
        "h14": 0.5, "h15": 0.5, "h16": 0.5, "h17": 2.0,
        "h18": 0.5, "h19": 1.5, "h20": 0.5, "h21": 0.5,
        "h22": 0.5, "h23": 1.5, "h24": 0.5, "h25": 1.5,
    }
}


class EN50160ReportProcessor:
    """EN50160 리포트 데이터 가공 클래스"""

    def __init__(self, config: WeeklyReportConfig = None):
        self.config = config or WeeklyReportConfig()
        self.limits = EN50160_LIMITS
        self.nominal_voltage = 22900.0
        self.nominal_current = 100.0
        self.nominal_frequency = 60.0

    def set_limits(self, nominal_voltage: float = None, nominal_current: float = None, nominal_frequency: float = None):
        """정격값 설정"""
        if nominal_voltage is not None:
            self.nominal_voltage = nominal_voltage
        if nominal_current is not None:
            self.nominal_current = nominal_current
        if nominal_frequency is not None:
            self.nominal_frequency = nominal_frequency
            # 주파수 리미트 재계산
            self.limits["frequency"]["nominal"] = nominal_frequency
            self.limits["frequency"]["limit_99_5"] = {
                "min": nominal_frequency * 0.99,
                "max": nominal_frequency * 1.01
            }
            self.limits["frequency"]["limit_100"] = {
                "min": nominal_frequency * 0.94,
                "max": nominal_frequency * 1.04
            }

    # =========================================================================
    # 히스토그램 계산 유틸리티
    # =========================================================================
    def _calculate_histogram(self, values: np.ndarray, bins: int = 30,
                             range_min: float = None, range_max: float = None) -> Dict:
        """
        히스토그램 데이터 계산

        Args:
            values: 데이터 배열
            bins: 구간 개수 (기본 30)
            range_min: 최소 범위 (None이면 데이터 최소값)
            range_max: 최대 범위 (None이면 데이터 최대값)

        Returns:
            {
                "bins": [경계값들 (bins+1개)],
                "counts": [빈도수 (bins개)],
                "percentages": [백분율 (bins개)],
                "bin_labels": ["59.40-59.44", ...],
                "bin_centers": [구간 중심값들]
            }
        """
        if len(values) == 0:
            return {
                "bins": [],
                "counts": [],
                "percentages": [],
                "bin_labels": [],
                "bin_centers": []
            }

        if range_min is None:
            range_min = float(np.min(values))
        if range_max is None:
            range_max = float(np.max(values))

        counts, bin_edges = np.histogram(values, bins=bins, range=(range_min, range_max))
        total = len(values)

        # 구간 중심값 계산
        bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(counts))]

        return {
            "bins": [round(float(b), 4) for b in bin_edges],
            "counts": [int(c) for c in counts],
            "percentages": [round(c / total * 100, 2) for c in counts],
            "bin_labels": [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(counts))],
            "bin_centers": [round(float(c), 4) for c in bin_centers]
        }

    def list_files(self) -> List[Dict[str, Any]]:
        """저장된 Parquet 파일 목록 조회"""
        import pyarrow.parquet as pq
        from datetime import datetime

        output_dir = Path(self.config.output_dir)
        files = []

        for file in sorted(output_dir.glob("pq_weekly_*.parquet"), reverse=True):
            try:
                parquet_file = pq.ParquetFile(file)
                metadata = parquet_file.metadata

                files.append({
                    "filename": file.name,
                    "filepath": str(file),
                    "num_rows": metadata.num_rows,
                    "file_size_kb": round(file.stat().st_size / 1024, 1),
                    "created_at": datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                logger.warning(f"파일 읽기 실패: {file.name} - {e}")

        return files

    def read_parquet(self, filepath: str = None, filename: str = None) -> Optional[pd.DataFrame]:
        """Parquet 파일 읽기"""
        try:
            if filepath:
                path = Path(filepath)
            elif filename:
                path = Path(self.config.output_dir) / filename
            else:
                logger.error("filepath 또는 filename 필요")
                return None

            if not path.exists():
                logger.error(f"파일 없음: {path}")
                return None

            df = pd.read_parquet(path)
            logger.info(f"파일 로드: {path.name} ({len(df)} 레코드)")
            return df

        except Exception as e:
            logger.error(f"파일 읽기 실패: {e}")
            return None

    def read_to_dict(self, filepath: str = None, filename: str = None) -> Optional[List[Dict]]:
        """Parquet 파일을 딕셔너리 리스트로 변환"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None

        if 'timestamp' in df.columns:
            df['timestamp'] = df['timestamp'].dt.strftime("%Y-%m-%d %H:%M:%S")

        return df.to_dict(orient='records')

    # =========================================================================
    # 전체 리포트 데이터 (단일 API용)
    # =========================================================================
    def get_all_chart_data(self, filepath: str = None, filename: str = None) -> Optional[Dict]:
        """
        전체 차트 데이터 반환 (파일 1번만 읽기)

        Returns:
            {
                "frequency": {...},
                "voltage": {...},
                "thd": {...},
                "unbalance": {...},
                "flicker": {...},
                "summary": {...}
            }
        """
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None

        return {
            "frequency": self._get_frequency_from_df(df),
            "voltage": self._get_voltage_from_df(df, nominal_voltage),
            "thd": self._get_thd_from_df(df),
            "unbalance": self._get_unbalance_from_df(df),
            "flicker": self._get_flicker_from_df(df),
            "harmonics": self._get_harmonics_from_df(df),
        }

    # =========================================================================
    # 주파수 (Frequency)
    # =========================================================================
    def get_frequency_chart_data(self, filepath: str = None, filename: str = None) -> Optional[Dict]:
        """주파수 Chart.js용 데이터 반환 (파일 경로 지정)"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None
        return self._get_frequency_from_df(df)

    def _get_frequency_from_df(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        주파수 Chart.js용 데이터 반환 (DataFrame 직접 전달)

        Returns:
            {
                "timeseries": { "labels": [...], "data": [...] },
                "histogram": { "bins": [...], "counts": [...], ... },
                "statistics": { "min": ..., "max": ..., "avg": ..., "result": ... },
                "limits": { "nominal": ..., "limit_99_5": {...}, "limit_100": {...} }
            }
        """
        freq_col = "frequency_avg"
        if freq_col not in df.columns:
            logger.error(f"컬럼 없음: {freq_col}")
            return None

        values = df[freq_col].dropna().values
        timestamps = df['timestamp'].dt.strftime("%Y-%m-%d %H:%M").tolist()

        # 시계열 데이터
        timeseries = {
            "labels": timestamps,
            "data": [round(float(v), 3) for v in df[freq_col].values]
        }

        # 히스토그램 데이터
        limits = self.limits["frequency"]
        histogram = self._calculate_histogram(
            values,
            bins=30,
            range_min=limits["limit_99_5"]["min"],  # 59.4Hz
            range_max=limits["limit_99_5"]["max"]   # 60.6Hz
        )

        # 통계
        measured_min = float(np.min(values))
        measured_max = float(np.max(values))
        measured_avg = float(np.mean(values))

        # 99.5% 범위 내 비율 계산
        in_range_99_5 = np.sum(
            (values >= limits["limit_99_5"]["min"]) &
            (values <= limits["limit_99_5"]["max"])
        ) / len(values) * 100

        in_range_100 = np.sum(
            (values >= limits["limit_100"]["min"]) &
            (values <= limits["limit_100"]["max"])
        ) / len(values) * 100

        # 판정
        result_99_5 = "PASS" if in_range_99_5 >= 99.5 else "FAIL"
        result_100 = "PASS" if in_range_100 >= 100.0 else "FAIL"

        statistics = {
            "min": round(measured_min, 3),
            "max": round(measured_max, 3),
            "avg": round(measured_avg, 3),
            "in_range_99_5_percent": round(in_range_99_5, 2),
            "in_range_100_percent": round(in_range_100, 2),
            "result_99_5": result_99_5,
            "result_100": result_100,
            "total_samples": len(values)
        }

        return {
            "timeseries": timeseries,
            "histogram": histogram,
            "statistics": statistics,
            "limits": limits
        }

    # =========================================================================
    # 전압 변동 (Voltage Variations)
    # =========================================================================
    def get_voltage_chart_data(self, filepath: str = None, filename: str = None,
                                nominal_voltage: float = 22900.0) -> Optional[Dict]:
        """전압 변동 Chart.js용 데이터 반환 (파일 경로 지정)"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None
        return self._get_voltage_from_df(df, nominal_voltage)

    def _get_voltage_from_df(self, df: pd.DataFrame, nominal_voltage: float = 22900.0) -> Optional[Dict]:
        """
        전압 변동 Chart.js용 데이터 반환 (DataFrame 직접 전달)

        Args:
            df: DataFrame
            nominal_voltage: 정격전압 (V), 기본값 22.9kV

        Returns:
            3상 각각의 시계열, 히스토그램, 통계 데이터
        """
        timestamps = df['timestamp'].dt.strftime("%Y-%m-%d %H:%M").tolist()
        limits = self.limits["voltage"]

        # 정격전압 기준 한계값 계산
        limit_95_min = nominal_voltage * limits["limit_95"]["min"] / 100
        limit_95_max = nominal_voltage * limits["limit_95"]["max"] / 100
        limit_100_min = nominal_voltage * limits["limit_100"]["min"] / 100
        limit_100_max = nominal_voltage * limits["limit_100"]["max"] / 100

        phases_data = {}
        for phase in range(1, 4):
            col = f"voltage_l{phase}"
            if col not in df.columns:
                continue

            values = df[col].dropna().values

            # 시계열
            timeseries = {
                "labels": timestamps,
                "data": [round(float(v), 1) for v in df[col].values]
            }

            # 히스토그램 (95% 범위 기준)
            histogram = self._calculate_histogram(
                values,
                bins=30,
                range_min=limit_95_min,
                range_max=limit_95_max
            )

            # 통계
            measured_min = float(np.min(values))
            measured_max = float(np.max(values))
            measured_avg = float(np.mean(values))

            # 95% 범위 내 비율
            in_range_95 = np.sum(
                (values >= limit_95_min) & (values <= limit_95_max)
            ) / len(values) * 100

            in_range_100 = np.sum(
                (values >= limit_100_min) & (values <= limit_100_max)
            ) / len(values) * 100

            result_95 = "PASS" if in_range_95 >= 95.0 else "FAIL"
            result_100 = "PASS" if in_range_100 >= 100.0 else "FAIL"

            phases_data[f"L{phase}"] = {
                "timeseries": timeseries,
                "histogram": histogram,
                "statistics": {
                    "min": round(measured_min, 1),
                    "max": round(measured_max, 1),
                    "avg": round(measured_avg, 1),
                    "in_range_95_percent": round(in_range_95, 2),
                    "in_range_100_percent": round(in_range_100, 2),
                    "result_95": result_95,
                    "result_100": result_100
                }
            }

        return {
            "phases": phases_data,
            "limits": {
                "nominal": nominal_voltage,
                "limit_95": {"min": round(limit_95_min, 1), "max": round(limit_95_max, 1)},
                "limit_100": {"min": round(limit_100_min, 1), "max": round(limit_100_max, 1)}
            },
            "total_samples": len(df)
        }

    # =========================================================================
    # 전압 불평형 (Voltage Unbalance)
    # =========================================================================
    def get_unbalance_chart_data(self, filepath: str = None, filename: str = None) -> Optional[Dict]:
        """전압 불평형 Chart.js용 데이터 반환 (파일 경로 지정)"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None
        return self._get_unbalance_from_df(df)

    def _get_unbalance_from_df(self, df: pd.DataFrame) -> Optional[Dict]:
        """전압 불평형 Chart.js용 데이터 반환 (DataFrame 직접 전달)"""
        col = "voltage_unbalance_0"  # 역상 불평형
        if col not in df.columns:
            logger.error(f"컬럼 없음: {col}")
            return None

        timestamps = df['timestamp'].dt.strftime("%Y-%m-%d %H:%M").tolist()
        values = df[col].dropna().values
        limit = self.limits["voltage_unbalance"]["limit_95"]

        # 시계열
        timeseries = {
            "labels": timestamps,
            "data": [round(float(v), 3) for v in df[col].values]
        }

        # 히스토그램 (0% ~ limit*1.5 범위)
        histogram = self._calculate_histogram(
            values,
            bins=25,
            range_min=0.0,
            range_max=limit * 1.5  # 3.0%
        )

        # 통계
        measured_max = float(np.max(values))
        in_range_95 = np.sum(values <= limit) / len(values) * 100
        result = "PASS" if in_range_95 >= 95.0 else "FAIL"

        statistics = {
            "max": round(measured_max, 3),
            "avg": round(float(np.mean(values)), 3),
            "percentile_95": round(float(np.percentile(values, 95)), 3),
            "in_range_95_percent": round(in_range_95, 2),
            "result": result
        }

        return {
            "timeseries": timeseries,
            "histogram": histogram,
            "statistics": statistics,
            "limits": {"limit_95": limit}
        }

    # =========================================================================
    # 전압 THD
    # =========================================================================
    def get_thd_chart_data(self, filepath: str = None, filename: str = None) -> Optional[Dict]:
        """전압 THD Chart.js용 데이터 반환 (파일 경로 지정)"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None
        return self._get_thd_from_df(df)

    def _get_thd_from_df(self, df: pd.DataFrame) -> Optional[Dict]:
        """전압 THD Chart.js용 데이터 반환 (DataFrame 직접 전달)"""
        timestamps = df['timestamp'].dt.strftime("%Y-%m-%d %H:%M").tolist()
        limit = self.limits["thd"]["limit_95"]

        phases_data = {}
        for phase in range(1, 4):
            col = f"voltage_thd_l{phase}"
            if col not in df.columns:
                continue

            values = df[col].dropna().values

            # 시계열
            timeseries = {
                "labels": timestamps,
                "data": [round(float(v), 2) for v in df[col].values]
            }

            # 히스토그램 (0% ~ limit*1.25 범위)
            histogram = self._calculate_histogram(
                values,
                bins=25,
                range_min=0.0,
                range_max=limit * 1.25  # 10%
            )

            measured_max = float(np.max(values))
            in_range_95 = np.sum(values <= limit) / len(values) * 100
            result = "PASS" if in_range_95 >= 95.0 else "FAIL"

            phases_data[f"L{phase}"] = {
                "timeseries": timeseries,
                "histogram": histogram,
                "statistics": {
                    "max": round(measured_max, 2),
                    "avg": round(float(np.mean(values)), 2),
                    "percentile_95": round(float(np.percentile(values, 95)), 2),
                    "in_range_95_percent": round(in_range_95, 2),
                    "result": result
                }
            }

        return {
            "phases": phases_data,
            "limits": {"limit_95": limit},
            "total_samples": len(df)
        }

    # =========================================================================
    # Flicker (Pst, Plt)
    # =========================================================================
    def get_flicker_chart_data(self, filepath: str = None, filename: str = None) -> Optional[Dict]:
        """Flicker (Pst, Plt) Chart.js용 데이터 반환 (파일 경로 지정)"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None
        return self._get_flicker_from_df(df)

    def _get_flicker_from_df(self, df: pd.DataFrame) -> Optional[Dict]:
        """Flicker (Pst, Plt) Chart.js용 데이터 반환 (DataFrame 직접 전달)"""
        timestamps = df['timestamp'].dt.strftime("%Y-%m-%d %H:%M").tolist()
        pst_limit = self.limits["flicker"]["pst_limit"]
        plt_limit = self.limits["flicker"]["plt_limit_95"]

        result = {"pst": {}, "plt": {}}

        for phase in range(1, 4):
            # Pst
            pst_col = f"pst_l{phase}"
            if pst_col in df.columns:
                pst_values = df[pst_col].dropna().values

                # Pst 히스토그램
                pst_histogram = self._calculate_histogram(
                    pst_values,
                    bins=25,
                    range_min=0.0,
                    range_max=pst_limit * 2.0
                )

                result["pst"][f"L{phase}"] = {
                    "timeseries": {
                        "labels": timestamps,
                        "data": [round(float(v), 3) for v in df[pst_col].values]
                    },
                    "histogram": pst_histogram,
                    "statistics": {
                        "max": round(float(np.max(pst_values)), 3),
                        "avg": round(float(np.mean(pst_values)), 3),
                        "percentile_95": round(float(np.percentile(pst_values, 95)), 3)
                    }
                }

            # Plt
            plt_col = f"plt_l{phase}"
            if plt_col in df.columns:
                plt_values = df[plt_col].dropna().values
                in_range = np.sum(plt_values <= plt_limit) / len(plt_values) * 100

                # Plt 히스토그램
                plt_histogram = self._calculate_histogram(
                    plt_values,
                    bins=25,
                    range_min=0.0,
                    range_max=plt_limit * 2.0
                )

                result["plt"][f"L{phase}"] = {
                    "timeseries": {
                        "labels": timestamps,
                        "data": [round(float(v), 3) for v in df[plt_col].values]
                    },
                    "histogram": plt_histogram,
                    "statistics": {
                        "max": round(float(np.max(plt_values)), 3),
                        "avg": round(float(np.mean(plt_values)), 3),
                        "percentile_95": round(float(np.percentile(plt_values, 95)), 3),
                        "in_range_95_percent": round(in_range, 2),
                        "result": "PASS" if in_range >= 95.0 else "FAIL"
                    }
                }

        result["limits"] = {
            "pst": pst_limit,
            "plt_95": plt_limit
        }
        result["total_samples"] = len(df)

        return result

    # =========================================================================
    # 고조파 (Harmonics)
    # =========================================================================
    def get_harmonics_table_data(self, filepath: str = None, filename: str = None) -> Optional[Dict]:
        """고조파 테이블 데이터 반환 (파일 경로 지정)"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None
        return self._get_harmonics_from_df(df)

    def _get_harmonics_from_df(self, df: pd.DataFrame) -> Optional[Dict]:
        """고조파 테이블 데이터 반환 (DataFrame 직접 전달)"""
        harmonics_limits = self.limits["harmonics"]
        result = {"phases": {}, "limits": harmonics_limits}

        for phase in range(1, 4):
            phase_key = f"L{phase}"
            result["phases"][phase_key] = {}

            # harmonics_l1, harmonics_l2, harmonics_l3 컬럼 (리스트)
            col = f"harmonics_l{phase}"
            if col in df.columns:
                # 각 행의 harmonics 리스트에서 평균/최대값 계산
                all_harmonics = np.array(df[col].tolist())  # shape: (n_samples, 24)

                for h in range(24):
                    h_num = h + 2  # H2 ~ H25
                    h_values = all_harmonics[:, h]
                    h_key = f"h{h_num}"
                    limit = harmonics_limits.get(h_key, 0.5)

                    in_range = np.sum(h_values <= limit) / len(h_values) * 100

                    # 각 고조파별 히스토그램
                    histogram = self._calculate_histogram(
                        h_values,
                        bins=20,
                        range_min=0.0,
                        range_max=limit * 1.5
                    )

                    result["phases"][phase_key][h_key] = {
                        "max": round(float(np.max(h_values)), 3),
                        "avg": round(float(np.mean(h_values)), 3),
                        "percentile_95": round(float(np.percentile(h_values, 95)), 3),
                        "limit": limit,
                        "in_range_95_percent": round(in_range, 2),
                        "result": "PASS" if in_range >= 95.0 else "FAIL",
                        "histogram": histogram
                    }

        result["total_samples"] = len(df)
        return result

    # =========================================================================
    # 유틸리티 함수
    # =========================================================================
    def _get_worst_result(self, results: List[str]) -> str:
        """결과 중 가장 나쁜 것 반환"""
        if "FAIL" in results:
            return "FAIL"
        if "N/A" in results:
            return "N/A"
        return "PASS"