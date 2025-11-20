from enum import IntEnum
from typing import Dict, List


class EquipmentType(IntEnum):
    NONE = 0
    COMPRESSOR = 1
    FAN = 2
    PUMP = 3
    MOTOR = 4
    POWER_SUPPLY = 5
    TRANSFORMER = 6
    MOTORFEED = 7
    PRIMARYTRANSFORMER = 8


class AlarmCategory(IntEnum):
    DIAGNOSIS = 0
    PQ = 1
    FAULTS = 2
    EVENTS = 3


# Component to field name mapping
DIAGNOSIS_COMPONENTS = {
    EquipmentType.COMPRESSOR: [
        "Turbulence_CMP",
        "MechanicalUnbalance_MDE",
        "SoftFoot_MDE",
        "TorqueRipple_MOT",
        "Load_MFD",
        "CableConnection_MFD",
        "NoiseVibration_PWS",
        "Heat_PWS",
        "IncomingVoltage_VOL",
        "Rotor_ROT",
        "Stator_STA",
        "Bearing_MIB",
        "DCLink_MFD"
    ],
    EquipmentType.FAN: [
        "Turbulence_FAN",
        "MechanicalUnbalance_MDE",
        "SoftFoot_MDE",
        "TorqueRipple_MOT",
        "Load_MFD",
        "CableConnection_MFD",
        "NoiseVibration_PWS",
        "Heat_PWS",
        "IncomingVoltage_VOL",
        "Rotor_ROT",
        "Stator_STA",
        "Bearing_MIB",
        "DCLink_MFD"
    ],
    EquipmentType.PUMP: [
        "Cavitation_PMP",
        "MechanicalUnbalance_MDE",
        "SoftFoot_MDE",
        "TorqueRipple_MOT",
        "Load_MFD",
        "CableConnection_MFD",
        "NoiseVibration_PWS",
        "Heat_PWS",
        "IncomingVoltage_VOL",
        "Rotor_ROT",
        "Stator_STA",
        "Bearing_MIB",
        "DCLink_MFD"
    ],
    EquipmentType.MOTOR: [
        "TorqueRipple_MOT",
        "MechanicalUnbalance_MOT",
        "SoftFoot_MOT",
        "Load_MFD",
        "CableConnection_MFD",
        "NoiseVibration_PWS",
        "Heat_PWS",
        "IncomingVoltage_VOL",
        "Rotor_ROT",
        "Stator_STA",
        "Bearing_MIB",
        "DCLink_MFD"
    ],
    EquipmentType.MOTORFEED: [
        "Load_MFD",
        "CableConnection_MFD",
        "NoiseVibration_PWS",
        "Heat_PWS",
        "IncomingVoltage_VOL",
        "DCLink_MFD"
    ],
    EquipmentType.POWER_SUPPLY: [
        "NoiseVibration_PWS",
        "Heat_PWS",
        "IncomingVoltage_VOL"
    ],
    EquipmentType.TRANSFORMER: [
        "Core_TRA",
        "Load_TRA",
        "GroundFaultD_TRA",
        "Capacitor_PTR",
        "TapChanger_PTR",
        "Bushings_PTR",
        "Stress_PTR",
        "LoadUnbalance_PTR",
        "CableConnection_PTR",
        "Winding_PTR",
        "NoiseVibration_PWS",
        "Heat_PWS",
        "IncomingVoltage_VOL"
    ],
    EquipmentType.PRIMARYTRANSFORMER: [
        "Capacitor_PTR",
        "TapChanger_PTR",
        "Bushings_PTR",
        "Stress_PTR",
        "LoadUnbalance_PTR",
        "CableConnection_PTR",
        "Winding_PTR",
        "NoiseVibration_PWS",
        "Heat_PWS",
        "IncomingVoltage_VOL"
    ]
}

PQ_COMPONENTS = [
    "VoltagePhaseAngle",
    "CurrentRMS",
    "CrestFactor",
    "Unbalance",
    "Harmonics",
    "ZeroSequence",
    "NegativeSequence",
    "CurrentPhaseAngle",
    "PhaseAngle",
    "PowerFactor",
    "TotalDemandDistortion",
    "Power",
    "VoltageRMS",
    "DC",
    "Events"
]

FAULTS_COMPONENTS = [
    "PhaseOrder",
    "NoLoad",
    "OverCurrent",
    "CF",
    "NoPower",
    "OverVoltage",
    "UnderVoltage",
    "LowFrequency",
    "VF"
]

EVENTS_COMPONENTS = [
    "TransientCurrentEvent",
    "OverCurrentEvent",
    "UnderCurrentEvent",
    "SagEvent",
    "SwellEvent",
    "InterruptionEvent",
    "TransientVoltageEvent"
]


class AlarmConfig:
    """알람 설정을 관리하는 클래스"""

    def __init__(self):
        self.diagnosis_alarms: Dict[str, int] = {}
        self.pq_alarms: Dict[str, int] = {}
        self.faults_alarms: Dict[str, int] = {}
        self.events_alarms: Dict[str, int] = {}

    def set_diagnosis_alarm(self, component: str, level: int):
        """진단 알람 설정 (level: -1=disabled, 0=OK, 1=Warning, 2=Alarm, 3=Danger)"""
        self.diagnosis_alarms[component] = level

    def set_pq_alarm(self, component: str, level: int):
        """PQ 알람 설정"""
        self.pq_alarms[component] = level

    def set_faults_alarm(self, component: str, level: int):
        """Faults 알람 설정"""
        self.faults_alarms[component] = level

    def set_events_alarm(self, component: str, level: int):
        """Events 알람 설정"""
        self.events_alarms[component] = level

    def get_enabled_diagnosis_components(self, equipment_type: EquipmentType) -> List[str]:
        """활성화된 진단 컴포넌트 리스트 반환"""
        components = DIAGNOSIS_COMPONENTS.get(equipment_type, [])
        return [c for c in components if self.diagnosis_alarms.get(c, -1) >= 0]

    def get_alarm_level(self, category: AlarmCategory, component: str) -> int:
        """특정 컴포넌트의 알람 레벨 반환"""
        if category == AlarmCategory.DIAGNOSIS:
            return self.diagnosis_alarms.get(component, -1)
        elif category == AlarmCategory.PQ:
            return self.pq_alarms.get(component, -1)
        elif category == AlarmCategory.FAULTS:
            return self.faults_alarms.get(component, -1)
        elif category == AlarmCategory.EVENTS:
            return self.events_alarms.get(component, -1)
        return -1

    def from_dict(self, data: Dict):
        """프론트엔드에서 받은 데이터로 설정"""
        if "Diagnosis" in data:
            for component, level in data["Diagnosis"].items():
                self.diagnosis_alarms[component] = level
        if "PQ" in data:
            for component, level in data["PQ"].items():
                self.pq_alarms[component] = level
        if "Faults" in data:
            for component, level in data["Faults"].items():
                self.faults_alarms[component] = level
        if "Events" in data:
            for component, level in data["Events"].items():
                self.events_alarms[component] = level

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "Diagnosis": self.diagnosis_alarms,
            "PQ": self.pq_alarms,
            "Faults": self.faults_alarms,
            "Events": self.events_alarms
        }


# 사용 예시
def example_usage():
    # 프론트엔드에서 받은 데이터
    frontend_data = {
        "Diagnosis": {
            "Turbulence_CMP": 2,  # Alarm level
            "Load_MFD": 1,  # Warning level
            "Rotor_ROT": -1  # Disabled
        },
        "PQ": {
            "VoltageRMS": 2,
            "CurrentRMS": 1
        }
    }

    # AlarmConfig 생성 및 설정
    # config = AlarmConfig()
    # config.from_dict(frontend_data)
    #
    # # 특정 장비 타입의 활성화된 컴포넌트 확인
    # enabled = config.get_enabled_diagnosis_components(EquipmentType.COMPRESSOR)
    # print(f"Enabled components: {enabled}")
    #
    # # 특정 컴포넌트의 알람 레벨 확인
    # level = config.get_alarm_level(AlarmCategory.DIAGNOSIS, "Turbulence_CMP")
    # print(f"Turbulence_CMP alarm level: {level}")
    #
    # # 딕셔너리로 변환
    # result = config.to_dict()
    # print(result)