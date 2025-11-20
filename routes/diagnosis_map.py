from enum import IntEnum
from typing import Dict, List


class DiagnosisStatus(IntEnum):
    """진단 상태 우선순위 (높을수록 심각)"""
    OK = 0
    INFORMATION = 1
    WARNING = 2
    INSPECT = 3
    REPAIR = 4


class AlarmStatusMatcher:
    """status_info와 API 응답을 매칭하여 최종 진단 상태를 결정"""

    def __init__(self):
        pass

    def _normalize_name(self, name: str) -> str:
        """이름 정규화 (공백 제거, 소문자)"""
        return name.replace(" ", "").lower()

    def parse_status_info(self, status_info: Dict) -> Dict[str, int]:

        config = {}

        # Diagnosis 파싱
        if "diagnosis" in status_info:
            for item in status_info["diagnosis"]:
                name = self._normalize_name(item["name"])
                config[name] = item["level"]

        # PQ 파싱
        if "pq" in status_info:
            for item in status_info["pq"]:
                name = self._normalize_name(item["name"])
                config[name] = item["level"]

        return config

    def parse_api_response(self, bar_graph: List[Dict]) -> Dict[str, int]:
        result = {}
        for item in bar_graph:
            name = item.get("Name")
            status = item.get("Status", 0)
            if name:
                normalized_name = self._normalize_name(name)
                result[normalized_name] = status
        return result

    def calculate_final_status(
            self,
            status_config: Dict[str, int],
            api_response: Dict[str, int]
    ) -> tuple[int, List[Dict]]:
        matched_statuses = []
        max_status = DiagnosisStatus.OK

        for name, configured_level in status_config.items():
            actual_status = api_response.get(name)

            # API 응답에 해당 Name이 있고, 레벨 이상이면
            if actual_status is not None and actual_status >= configured_level:
                matched_statuses.append({
                    "name": name,
                    "configured_level": configured_level,
                    "actual_status": actual_status,
                    "triggered": True
                })

                if actual_status > max_status:
                    max_status = actual_status

        return max_status, matched_statuses

    def get_status_name(self, status: int) -> str:
        """상태 코드를 문자열로 변환"""
        status_map = {
            0: "NoData",
            1: "OK",
            2: "Warning",
            3: "Inspect",
            4: "Repair"
        }
        return status_map.get(status, "Unknown")

    def diagnose(
            self,
            status_info: Dict,
            bar_graph: List[Dict]
    ) -> Dict:
        # 설정 파싱
        config = self.parse_status_info(status_info)

        # API 응답 파싱
        response = self.parse_api_response(bar_graph)

        # 최종 상태 계산
        final_status, matched = self.calculate_final_status(config, response)

        return {
            "final_status": final_status,
            "status_name": self.get_status_name(final_status),
            "matched_parameters": matched,
            "total_configured": len(config),
            "total_matched": len(matched)
        }