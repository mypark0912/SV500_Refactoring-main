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
    output_dir: str = "/usr/local/sv500/reports"
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
    # 주파수 (Frequency)
    # =========================================================================
    def get_frequency_chart_data(self, filepath: str = None, filename: str = None) -> Optional[Dict]:
        """
        주파수 Chart.js용 데이터 반환

        Returns:
            {
                "timeseries": { "labels": [...], "data": [...] },
                "histogram": { "labels": [...], "data": [...] },
                "statistics": { "min": ..., "max": ..., "avg": ..., "result": ... },
                "limits": { "nominal": ..., "limit_99_5": {...}, "limit_100": {...} }
            }
        """
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None

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

        # 히스토그램 (분포)
        histogram = self._calculate_histogram(values, bin_min=59.0, bin_max=61.0, bin_count=40)

        # 통계
        limits = self.limits["frequency"]
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
        """
        전압 변동 Chart.js용 데이터 반환

        Args:
            nominal_voltage: 정격전압 (V), 기본값 22.9kV

        Returns:
            3상 각각의 시계열, 히스토그램, 통계 데이터
        """
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None

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

            # 히스토그램
            histogram = self._calculate_histogram(
                values,
                bin_min=nominal_voltage * 0.85,
                bin_max=nominal_voltage * 1.15,
                bin_count=30
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
        """전압 불평형 Chart.js용 데이터 반환"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None

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

        # 히스토그램
        histogram = self._calculate_histogram(values, bin_min=0, bin_max=5, bin_count=25)

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
        """전압 THD Chart.js용 데이터 반환"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None

        timestamps = df['timestamp'].dt.strftime("%Y-%m-%d %H:%M").tolist()
        limit = self.limits["thd"]["limit_95"]

        phases_data = {}
        for phase in range(1, 4):
            col = f"voltage_thd_l{phase}"
            if col not in df.columns:
                continue

            values = df[col].dropna().values

            timeseries = {
                "labels": timestamps,
                "data": [round(float(v), 2) for v in df[col].values]
            }

            histogram = self._calculate_histogram(values, bin_min=0, bin_max=15, bin_count=30)

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
        """Flicker (Pst, Plt) Chart.js용 데이터 반환"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None

        timestamps = df['timestamp'].dt.strftime("%Y-%m-%d %H:%M").tolist()
        pst_limit = self.limits["flicker"]["pst_limit"]
        plt_limit = self.limits["flicker"]["plt_limit_95"]

        result = {"pst": {}, "plt": {}}

        for phase in range(1, 4):
            # Pst
            pst_col = f"pst_l{phase}"
            if pst_col in df.columns:
                pst_values = df[pst_col].dropna().values
                result["pst"][f"L{phase}"] = {
                    "timeseries": {
                        "labels": timestamps,
                        "data": [round(float(v), 3) for v in df[pst_col].values]
                    },
                    "statistics": {
                        "max": round(float(np.max(pst_values)), 3),
                        "avg": round(float(np.mean(pst_values)), 3)
                    }
                }

            # Plt
            plt_col = f"plt_l{phase}"
            if plt_col in df.columns:
                plt_values = df[plt_col].dropna().values
                in_range = np.sum(plt_values <= plt_limit) / len(plt_values) * 100
                result["plt"][f"L{phase}"] = {
                    "timeseries": {
                        "labels": timestamps,
                        "data": [round(float(v), 3) for v in df[plt_col].values]
                    },
                    "statistics": {
                        "max": round(float(np.max(plt_values)), 3),
                        "avg": round(float(np.mean(plt_values)), 3),
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
        """고조파 테이블 데이터 반환 (H2~H25)"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None

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

                    result["phases"][phase_key][h_key] = {
                        "max": round(float(np.max(h_values)), 3),
                        "avg": round(float(np.mean(h_values)), 3),
                        "percentile_95": round(float(np.percentile(h_values, 95)), 3),
                        "limit": limit,
                        "in_range_95_percent": round(in_range, 2),
                        "result": "PASS" if in_range >= 95.0 else "FAIL"
                    }

        result["total_samples"] = len(df)
        return result

    # =========================================================================
    # 전체 요약 (Summary)
    # =========================================================================
    def get_summary_data(self, filepath: str = None, filename: str = None,
                         nominal_voltage: float = 22900.0) -> Optional[Dict]:
        """EN50160 전체 요약 테이블 데이터"""
        df = self.read_parquet(filepath, filename)
        if df is None:
            return None

        summary = {
            "period": {
                "start": df['timestamp'].min().strftime("%Y-%m-%d %H:%M"),
                "end": df['timestamp'].max().strftime("%Y-%m-%d %H:%M")
            },
            "total_samples": len(df),
            "parameters": []
        }

        # 주파수
        freq_data = self.get_frequency_chart_data(filepath, filename)
        if freq_data:
            summary["parameters"].append({
                "name": "Frequency Variation 1",
                "L1": freq_data["statistics"]["in_range_99_5_percent"],
                "L2": None,
                "L3": None,
                "compliance": freq_data["statistics"]["result_99_5"],
                "requirement": "(±1%), 99.5%/Week"
            })
            summary["parameters"].append({
                "name": "Frequency Variation 2",
                "L1": freq_data["statistics"]["in_range_100_percent"],
                "L2": None,
                "L3": None,
                "compliance": freq_data["statistics"]["result_100"],
                "requirement": "(+4%/-6%), 100%/Week"
            })

        # 전압
        volt_data = self.get_voltage_chart_data(filepath, filename, nominal_voltage)
        if volt_data:
            summary["parameters"].append({
                "name": "Voltage Variation 1",
                "L1": volt_data["phases"].get("L1", {}).get("statistics", {}).get("in_range_95_percent"),
                "L2": volt_data["phases"].get("L2", {}).get("statistics", {}).get("in_range_95_percent"),
                "L3": volt_data["phases"].get("L3", {}).get("statistics", {}).get("in_range_95_percent"),
                "compliance": self._get_worst_result([
                    volt_data["phases"].get(f"L{i}", {}).get("statistics", {}).get("result_95", "N/A")
                    for i in range(1, 4)
                ]),
                "requirement": "(±10%), 95%/Week"
            })

        # THD
        thd_data = self.get_thd_chart_data(filepath, filename)
        if thd_data:
            summary["parameters"].append({
                "name": "THD",
                "L1": thd_data["phases"].get("L1", {}).get("statistics", {}).get("in_range_95_percent"),
                "L2": thd_data["phases"].get("L2", {}).get("statistics", {}).get("in_range_95_percent"),
                "L3": thd_data["phases"].get("L3", {}).get("statistics", {}).get("in_range_95_percent"),
                "compliance": self._get_worst_result([
                    thd_data["phases"].get(f"L{i}", {}).get("statistics", {}).get("result", "N/A")
                    for i in range(1, 4)
                ]),
                "requirement": "(<8%), 95%/Week"
            })

        # 불평형
        unbal_data = self.get_unbalance_chart_data(filepath, filename)
        if unbal_data:
            summary["parameters"].append({
                "name": "Voltage Unbalance",
                "L1": unbal_data["statistics"]["in_range_95_percent"],
                "L2": None,
                "L3": None,
                "compliance": unbal_data["statistics"]["result"],
                "requirement": "(<2%), 95%/Week"
            })

        # Flicker
        flicker_data = self.get_flicker_chart_data(filepath, filename)
        if flicker_data:
            summary["parameters"].append({
                "name": "Plt",
                "L1": flicker_data["plt"].get("L1", {}).get("statistics", {}).get("in_range_95_percent"),
                "L2": flicker_data["plt"].get("L2", {}).get("statistics", {}).get("in_range_95_percent"),
                "L3": flicker_data["plt"].get("L3", {}).get("statistics", {}).get("in_range_95_percent"),
                "compliance": self._get_worst_result([
                    flicker_data["plt"].get(f"L{i}", {}).get("statistics", {}).get("result", "N/A")
                    for i in range(1, 4)
                ]),
                "requirement": "(≤1), 95%/Week"
            })

        return summary

    # =========================================================================
    # 유틸리티 함수
    # =========================================================================
    def _calculate_histogram(self, values: np.ndarray, bin_min: float, bin_max: float,
                              bin_count: int = 20) -> Dict:
        """히스토그램 계산"""
        counts, bin_edges = np.histogram(values, bins=bin_count, range=(bin_min, bin_max))

        # 라벨은 각 빈의 중간값
        labels = [f"{(bin_edges[i] + bin_edges[i+1])/2:.2f}" for i in range(len(counts))]

        return {
            "labels": labels,
            "data": [int(c) for c in counts],
            "bin_edges": [round(float(e), 2) for e in bin_edges]
        }

    def _get_worst_result(self, results: List[str]) -> str:
        """결과 중 가장 나쁜 것 반환"""
        if "FAIL" in results:
            return "FAIL"
        if "N/A" in results:
            return "N/A"
        return "PASS"