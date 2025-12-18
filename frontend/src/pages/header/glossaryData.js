// glossaryData.js - 용어 데이터 파일
// 이 파일에서 용어 설명과 이미지를 편집하세요.

/*
===============================================================================
  데이터 편집 가이드
===============================================================================

1. 각 항목의 필드 설명:
   - key: 고유 식별자 (수정하지 마세요)
   - label: 영어 제목
   - label_ko: 한국어 제목
   - description: 영어 설명
   - description_ko: 한국어 설명
   - image: 이미지 경로 (선택사항, 예: '/images/glossary/bearing.png')

2. 이미지 추가 방법:
   - /images 폴더에 이미지를 넣으세요
   - 항목에 image 필드를 추가하세요
   
   예시:
   { 
     key: 'bearing', 
     label: 'Bearing', 
     label_ko: '베어링',
     description: '...',
     description_ko: '...',
     image: '/glossary/bearing.png',
   }

===============================================================================
*/

export const equipmentData = [
  {
    key: 'compressorFan',
    label: 'Compressor/Fan',
    items: [
      { 
        key: 'turbulence', 
        label: 'Turbulence', 
        label_ko: '난류',
        description: 'Adjust fan operating parameters to reduce turbulence. This may include changing the fan speed, modifying the blade angle, or improving inlet/outlet duct design to promote smoother airflow.',
        description_ko: '난류를 줄이려면 팬 작동 매개변수를 조정하십시오. 여기에는 팬 속도 변경, 날개 각도 조정, 흡입/배출 덕트 설계 개선 등이 포함될 수 있습니다.',
        image: '/glossary/device.png',  // 이미지 경로 (선택사항)
      },
      { 
        key: 'blade', 
        label: 'Blade', 
        label_ko: '팬 블레이드',
        description: 'Perform a detailed inspection of the fan blades for any signs of damage, wear, or accumulation of debris.',
        description_ko: '팬 날개에 손상, 마모 또는 이물질 축적 흔적이 있는지 자세히 검사하십시오.',
      },
      { 
        key: 'mechanicalUnbalance', 
        label: 'Mechanical Unbalance', 
        label_ko: '기계적 불균형',
        description: 'Perform a detailed inspection of the equipment to identify sources of mechanical unbalance, such as misalignment, wear, or foreign objects.',
        description_ko: '정렬 불량, 마모, 이물질 등 기계적 불균형의 원인을 파악하기 위해 장비를 정밀 검사하십시오.',
      },
      { 
        key: 'softFoot', 
        label: 'Soft Foot', 
        label_ko: '소프트 풋',
        description: 'Conduct a thorough inspection of the equipment base and mounting points to identify any soft foot conditions.',
        description_ko: '설비 바닥과 장착 지점을 면밀히 검사하여 소프트 풋 상태가 있는지 확인하십시오.',
      },
      { 
        key: 'torqueRipple', 
        label: 'Torque Ripple', 
        label_ko: '토크 리플',
        description: 'The motor is experiencing periodic torque fluctuations, which may cause vibration, noise, or mechanical wear.',
        description_ko: '모터에서 주기적인 토크 변동이 발생하고 있으며, 이는 진동, 소음 또는 기계적 마모를 유발할 수 있습니다.',
      },
      { 
        key: 'load', 
        label: 'Load', 
        label_ko: '부하',
        description: 'Check the load of the equipment.',
        description_ko: '설비의 부하를 확인하세요.',
      },
      { 
        key: 'cableConnection', 
        label: 'Cable Connection', 
        label_ko: '케이블 연결',
        description: 'Check for loose, corroded, or damaged terminals.',
        description_ko: '단자가 느슨하거나 부식되었거나 손상되었는지 확인하십시오.',
      },
      { 
        key: 'noiseVibration', 
        label: 'Noise/Vibration', 
        label_ko: '소음/진동',
        description: 'Inspect the equipment for noise and vibration.',
        description_ko: '장비의 소음 및 진동을 점검하십시오.',
      },
      { 
        key: 'heat', 
        label: 'Heat', 
        label_ko: '열',
        description: 'Elevated harmonic stress detected, indicating increased heat generation.',
        description_ko: '고조파 스트레스가 상승하여 열 발생이 증가했습니다.',
      },
      { 
        key: 'incomingVoltage', 
        label: 'Incoming Voltage', 
        label_ko: '입력 전압',
        description: 'Check the power supply. The rms voltage is outside the acceptable range.',
        description_ko: '전원 공급 장치를 확인하세요. RMS 전압이 허용 범위를 벗어났습니다.',
      },
      { 
        key: 'rotor', 
        label: 'Rotor', 
        label_ko: '회전자',
        description: 'Inspect the rotor alignment, check for physical damage, and conduct vibration analysis.',
        description_ko: '회전자 정렬을 검사하고, 물리적 손상이 있는지 확인하고, 진동 분석을 수행합니다.',
      },
      { 
        key: 'stator', 
        label: 'Stator', 
        label_ko: '고정자',
        description: 'Check the temperature of the equipment and noise coming from the motor.',
        description_ko: '모터의 온도와 소음을 확인하세요.',
      },
      { 
        key: 'bearing', 
        label: 'Bearing', 
        label_ko: '베어링',
        description: 'Conduct a thorough inspection of the bearings for signs of wear, damage, or inadequate lubrication.',
        description_ko: '베어링에 마모, 손상 또는 윤활 부족 징후가 있는지 철저히 검사하십시오.',
      },
      { 
        key: 'dcLink', 
        label: 'DC Link', 
        label_ko: 'DC 링크',
        description: 'Check for voltage ripple, capacitor swelling, or overheating.',
        description_ko: '전압 리플, 커패시터 팽창 또는 과열을 확인하세요.',
      },
    ]
  },
  {
    key: 'pump',
    label: 'Pump',
    items: [
      { 
        key: 'cavitation', 
        label: 'Cavitation', 
        label_ko: '캐비테이션',
        description: 'Modify pump operating conditions to ensure optimal flow and pressure levels.',
        description_ko: '최적의 유량 및 압력 수준을 확보하기 위해 펌프 작동 조건을 조정하십시오.',
      },
      { 
        key: 'vane', 
        label: 'Vane', 
        label_ko: '베인',
        description: 'Conduct a thorough inspection of the pump vane assembly for wear, damage, or blockages.',
        description_ko: '펌프 베인 어셈블리의 마모, 손상 또는 막힘 여부를 철저히 검사하십시오.',
      },
      { 
        key: 'mechanicalUnbalance', 
        label: 'Mechanical Unbalance', 
        label_ko: '기계적 불균형',
        description: 'Perform a detailed inspection of the equipment to identify sources of mechanical unbalance.',
        description_ko: '기계적 불균형의 원인을 파악하기 위해 장비를 정밀 검사하십시오.',
      },
      { 
        key: 'softFoot', 
        label: 'Soft Foot', 
        label_ko: '소프트 풋',
        description: 'Conduct a thorough inspection of the equipment base and mounting points.',
        description_ko: '설비 바닥과 장착 지점을 면밀히 검사하십시오.',
      },
      { 
        key: 'torqueRipple', 
        label: 'Torque Ripple', 
        label_ko: '토크 리플',
        description: 'The motor is experiencing periodic torque fluctuations.',
        description_ko: '모터에서 주기적인 토크 변동이 발생하고 있습니다.',
      },
      { 
        key: 'load', 
        label: 'Load', 
        label_ko: '부하',
        description: 'Check the load of the equipment.',
        description_ko: '설비의 부하를 확인하세요.',
      },
      { 
        key: 'cableConnection', 
        label: 'Cable Connection', 
        label_ko: '케이블 연결',
        description: 'Check for loose, corroded, or damaged terminals.',
        description_ko: '단자가 느슨하거나 부식되었거나 손상되었는지 확인하십시오.',
      },
      { 
        key: 'noiseVibration', 
        label: 'Noise/Vibration', 
        label_ko: '소음/진동',
        description: 'Inspect the equipment for noise and vibration.',
        description_ko: '장비의 소음 및 진동을 점검하십시오.',
      },
      { 
        key: 'heat', 
        label: 'Heat', 
        label_ko: '열',
        description: 'Elevated harmonic stress detected.',
        description_ko: '고조파 스트레스가 상승하여 열 발생이 증가했습니다.',
      },
      { 
        key: 'incomingVoltage', 
        label: 'Incoming Voltage', 
        label_ko: '입력 전압',
        description: 'Check the power supply.',
        description_ko: '전원 공급 장치를 확인하세요.',
      },
      { 
        key: 'rotor', 
        label: 'Rotor', 
        label_ko: '회전자',
        description: 'Inspect the rotor alignment.',
        description_ko: '회전자 정렬을 검사하십시오.',
      },
      { 
        key: 'stator', 
        label: 'Stator', 
        label_ko: '고정자',
        description: 'Check the temperature and noise.',
        description_ko: '모터의 온도와 소음을 확인하세요.',
      },
      { 
        key: 'bearing', 
        label: 'Bearing', 
        label_ko: '베어링',
        description: 'Inspect bearings for wear, damage, or inadequate lubrication.',
        description_ko: '베어링에 마모, 손상 또는 윤활 부족 징후가 있는지 검사하십시오.',
      },
      { 
        key: 'dcLink', 
        label: 'DC Link', 
        label_ko: 'DC 링크',
        description: 'Check for voltage ripple, capacitor swelling, or overheating.',
        description_ko: '전압 리플, 커패시터 팽창 또는 과열을 확인하세요.',
      },
    ]
  },
  {
    key: 'motor',
    label: 'Motor',
    items: [
      { 
        key: 'torqueRipple', 
        label: 'Torque Ripple', 
        label_ko: '토크 리플',
        description: 'The motor is experiencing periodic torque fluctuations.',
        description_ko: '모터에서 주기적인 토크 변동이 발생하고 있습니다.',
      },
      { 
        key: 'mechanicalUnbalance', 
        label: 'Mechanical Unbalance', 
        label_ko: '기계적 불균형',
        description: 'Perform a detailed inspection of the equipment.',
        description_ko: '기계적 불균형의 원인을 파악하기 위해 장비를 정밀 검사하십시오.',
      },
      { 
        key: 'softFoot', 
        label: 'Soft Foot', 
        label_ko: '소프트 풋',
        description: 'Conduct a thorough inspection of the equipment base.',
        description_ko: '설비 바닥과 장착 지점을 면밀히 검사하십시오.',
      },
      { 
        key: 'load', 
        label: 'Load', 
        label_ko: '부하',
        description: 'Check the load of the equipment.',
        description_ko: '설비의 부하를 확인하세요.',
      },
      { 
        key: 'cableConnection', 
        label: 'Cable Connection', 
        label_ko: '케이블 연결',
        description: 'Check for loose, corroded, or damaged terminals.',
        description_ko: '단자가 느슨하거나 부식되었거나 손상되었는지 확인하십시오.',
      },
      { 
        key: 'noiseVibration', 
        label: 'Noise/Vibration', 
        label_ko: '소음/진동',
        description: 'Inspect the equipment for noise and vibration.',
        description_ko: '장비의 소음 및 진동을 점검하십시오.',
      },
      { 
        key: 'heat', 
        label: 'Heat', 
        label_ko: '열',
        description: 'Elevated harmonic stress detected.',
        description_ko: '고조파 스트레스가 상승하여 열 발생이 증가했습니다.',
      },
      { 
        key: 'incomingVoltage', 
        label: 'Incoming Voltage', 
        label_ko: '입력 전압',
        description: 'Check the power supply.',
        description_ko: '전원 공급 장치를 확인하세요.',
      },
      { 
        key: 'rotor', 
        label: 'Rotor', 
        label_ko: '회전자',
        description: 'Inspect the rotor alignment.',
        description_ko: '회전자 정렬을 검사하십시오.',
      },
      { 
        key: 'stator', 
        label: 'Stator', 
        label_ko: '고정자',
        description: 'Check the temperature and noise.',
        description_ko: '모터의 온도와 소음을 확인하세요.',
      },
      { 
        key: 'bearing', 
        label: 'Bearing', 
        label_ko: '베어링',
        description: 'Conduct a thorough inspection of the bearings.',
        description_ko: '베어링에 마모, 손상 또는 윤활 부족 징후가 있는지 검사하십시오.',
      },
      { 
        key: 'dcLink', 
        label: 'DC Link', 
        label_ko: 'DC 링크',
        description: 'Check for voltage ripple, capacitor swelling, or overheating.',
        description_ko: '전압 리플, 커패시터 팽창 또는 과열을 확인하세요.',
      },
    ]
  },
  {
    key: 'motorFeed',
    label: 'Motor Feed',
    items: [
      { key: 'load', label: 'Load', label_ko: '부하', description: 'Check the load of the equipment.', description_ko: '설비의 부하를 확인하세요.' },
      { key: 'cableConnection', label: 'Cable Connection', label_ko: '케이블 연결', description: 'Check for loose, corroded, or damaged terminals.', description_ko: '단자가 느슨하거나 부식되었거나 손상되었는지 확인하십시오.' },
      { key: 'noiseVibration', label: 'Noise/Vibration', label_ko: '소음/진동', description: 'Inspect the equipment for noise and vibration.', description_ko: '장비의 소음 및 진동을 점검하십시오.' },
      { key: 'heat', label: 'Heat', label_ko: '열', description: 'Elevated harmonic stress detected.', description_ko: '고조파 스트레스가 상승하여 열 발생이 증가했습니다.' },
      { key: 'incomingVoltage', label: 'Incoming Voltage', label_ko: '입력 전압', description: 'Check the power supply.', description_ko: '전원 공급 장치를 확인하세요.' },
      { key: 'dcLink', label: 'DC Link', label_ko: 'DC 링크', description: 'Check for voltage ripple, capacitor swelling, or overheating.', description_ko: '전압 리플, 커패시터 팽창 또는 과열을 확인하세요.' },
    ]
  },
  {
    key: 'powerSupply',
    label: 'Power Supply',
    items: [
      { key: 'noiseVibration', label: 'Noise/Vibration', label_ko: '소음/진동', description: 'Inspect the equipment for noise and vibration.', description_ko: '장비의 소음 및 진동을 점검하십시오.' },
      { key: 'heat', label: 'Heat', label_ko: '열', description: 'Elevated harmonic stress detected.', description_ko: '고조파 스트레스가 상승하여 열 발생이 증가했습니다.' },
      { key: 'incomingVoltage', label: 'Incoming Voltage', label_ko: '입력 전압', description: 'Check the power supply.', description_ko: '전원 공급 장치를 확인하세요.' },
      { key: 'rectifier', label: 'Rectifier', label_ko: '정류기', description: 'Inspect for diode failure, unbalanced output, or heat damage.', description_ko: '다이오드 고장, 출력 불균형 또는 열 손상 여부를 점검하십시오.' },
      { key: 'switching', label: 'Switching', label_ko: '스위칭', description: 'Monitor for noise, EMI, or overheating.', description_ko: '노이즈, EMI 또는 과열을 모니터링하세요.' },
    ]
  },
  {
    key: 'transformer',
    label: 'Transformer',
    items: [
      { key: 'core', label: 'Core', label_ko: '코어', description: 'Inspect the core for signs of lamination damage, core loosening, or localized overheating.', description_ko: '코어에 적층 손상, 코어 느슨해짐 또는 국부 과열 징후가 있는지 검사하십시오.' },
      { key: 'load', label: 'Load', label_ko: '부하', description: 'Verify that the transformer is not operating under sustained overload conditions.', description_ko: '변압기가 지속적인 과부하 조건에서 작동하지 않는지 확인하십시오.' },
      { key: 'groundFault', label: 'Ground Fault', label_ko: '지락', description: 'Inspect grounding and unbalanced loads.', description_ko: '접지 및 불평형 부하를 점검하십시오.' },
      { key: 'capacitor', label: 'Capacitor', label_ko: '캐패시터', description: 'Inspect capacitors for signs of bulging, leakage, or dielectric failure.', description_ko: '커패시터에 팽창, 누설 또는 유전체 고장 징후가 있는지 검사하십시오.' },
      { key: 'tapChanger', label: 'Tap Changer', label_ko: '탭 체인저', description: 'Inspect the tap changer for contact wear, carbon buildup, or mechanical misalignment.', description_ko: '탭 체인저의 접점 마모, 탄소 축적 또는 기계적 정렬 불량을 검사하십시오.' },
      { key: 'bushings', label: 'Bushings', label_ko: '부싱', description: 'Inspect transformer bushings for oil leakage, cracks, or contamination.', description_ko: '변압기 부싱에 오일 누출, 균열 또는 오염이 있는지 검사하십시오.' },
      { key: 'stress', label: 'Stress', label_ko: '스트레스', description: 'Monitor for electrical stress on the transformer.', description_ko: '변압기에 발생하는 전기적 스트레스를 모니터링하십시오.' },
      { key: 'loadUnbalance', label: 'Load Unbalance', label_ko: '부하 불평형', description: 'Unbalance indicates uneven voltage or current across phases.', description_ko: '불평형은 상간 전압 또는 전류의 불균형을 나타냅니다.' },
      { key: 'cableConnection', label: 'Cable Connection', label_ko: '케이블 연결', description: 'Check for loose, corroded, or damaged terminals.', description_ko: '단자가 느슨하거나 부식되었거나 손상되었는지 확인하십시오.' },
      { key: 'winding', label: 'Winding', label_ko: '권선', description: 'Inspect the windings for insulation breakdown, shorted turns, or overheating.', description_ko: '권선의 절연 파괴, 단락 또는 과열 여부를 검사하십시오.' },
      { key: 'noiseVibration', label: 'Noise/Vibration', label_ko: '소음/진동', description: 'Inspect the equipment for noise and vibration.', description_ko: '장비의 소음 및 진동을 점검하십시오.' },
      { key: 'heat', label: 'Heat', label_ko: '열', description: 'Elevated harmonic stress detected.', description_ko: '고조파 스트레스가 상승하여 열 발생이 증가했습니다.' },
      { key: 'incomingVoltage', label: 'Incoming Voltage', label_ko: '입력 전압', description: 'Check the power supply.', description_ko: '전원 공급 장치를 확인하세요.' },
    ]
  },
  {
    key: 'primaryTransformer',
    label: 'Primary Transformer',
    items: [
      { key: 'capacitor', label: 'Capacitor', label_ko: '캐패시터', description: 'Inspect capacitors for signs of bulging, leakage, or dielectric failure.', description_ko: '커패시터에 팽창, 누설 또는 유전체 고장 징후가 있는지 검사하십시오.' },
      { key: 'tapChanger', label: 'Tap Changer', label_ko: '탭 체인저', description: 'Inspect the tap changer for contact wear.', description_ko: '탭 체인저의 접점 마모를 검사하십시오.' },
      { key: 'bushings', label: 'Bushings', label_ko: '부싱', description: 'Inspect transformer bushings for oil leakage, cracks, or contamination.', description_ko: '변압기 부싱에 오일 누출, 균열 또는 오염이 있는지 검사하십시오.' },
      { key: 'stress', label: 'Stress', label_ko: '스트레스', description: 'Monitor for electrical stress on the transformer.', description_ko: '변압기에 발생하는 전기적 스트레스를 모니터링하십시오.' },
      { key: 'loadUnbalance', label: 'Load Unbalance', label_ko: '부하 불평형', description: 'Unbalance indicates uneven voltage or current across phases.', description_ko: '불평형은 상간 전압 또는 전류의 불균형을 나타냅니다.' },
      { key: 'cableConnection', label: 'Cable Connection', label_ko: '케이블 연결', description: 'Check for loose, corroded, or damaged terminals.', description_ko: '단자가 느슨하거나 부식되었거나 손상되었는지 확인하십시오.' },
      { key: 'winding', label: 'Winding', label_ko: '권선', description: 'Inspect the windings for insulation breakdown.', description_ko: '권선의 절연 파괴 여부를 검사하십시오.' },
      { key: 'noiseVibration', label: 'Noise/Vibration', label_ko: '소음/진동', description: 'Inspect the equipment for noise and vibration.', description_ko: '장비의 소음 및 진동을 점검하십시오.' },
      { key: 'heat', label: 'Heat', label_ko: '열', description: 'Elevated harmonic stress detected.', description_ko: '고조파 스트레스가 상승하여 열 발생이 증가했습니다.' },
      { key: 'incomingVoltage', label: 'Incoming Voltage', label_ko: '입력 전압', description: 'Check the power supply.', description_ko: '전원 공급 장치를 확인하세요.' },
    ]
  },
]

export const pqData = [
  { key: 'voltageRMS', label: 'Voltage RMS', label_ko: '전압 RMS', description: 'Check the power supply. The rms voltage is outside the acceptable range.', description_ko: '전원 공급 장치를 확인하세요. RMS 전압이 허용 범위를 벗어났습니다.' },
  { key: 'voltagePhaseAngle', label: 'Voltage Phase Angle', label_ko: '전압 위상', description: 'Check phase unbalance and ensuring proper synchronization of equipment.', description_ko: '위상 불균형을 점검하고 장비의 적절한 동기화를 확인하십시오.' },
  { key: 'currentRMS', label: 'Current RMS', label_ko: '전류', description: 'Check the power supply. The rms current is outside the acceptable range.', description_ko: '전원 공급 장치를 확인하십시오. RMS 전류가 허용 범위를 벗어났습니다.' },
  { key: 'currentPhaseAngle', label: 'Current Phase Angle', label_ko: '전류 위상', description: 'Check phase unbalance and ensuring proper synchronization of equipment.', description_ko: '전류 위상 각도가 허용 범위를 벗어났습니다.' },
  { key: 'crestFactor', label: 'Crest Factor', label_ko: '크레스트 팩터', description: 'Check the power supply. Crest factor out of the acceptable range.', description_ko: '전원 공급 장치를 확인하십시오. 크레스트 팩터(CF)가 허용 범위를 벗어났습니다.' },
  { key: 'unbalance', label: 'Unbalance', label_ko: '불균형', description: 'Unbalance indicates uneven voltage or current across phases.', description_ko: '불평형은 상 간 전압 또는 전류의 불균형을 나타냅니다.' },
  { key: 'harmonics', label: 'Harmonics', label_ko: '고조파', description: 'Harmonics level is beyond the limits. Please check the power source.', description_ko: '고조파 레벨이 한계를 초과했습니다. 전원을 확인하십시오.' },
  { key: 'zeroSequence', label: 'Zero Sequence', label_ko: '영상분', description: 'Inspect grounding system and unbalanced loads.', description_ko: '접지 시스템과 불균형 부하를 점검하십시오.' },
  { key: 'negativeSequence', label: 'Negative Sequence', label_ko: '역상분', description: 'Check phase unbalance and load distribution.', description_ko: '상 불균형 및 부하 분포를 점검하십시오.' },
  { key: 'phaseAngle', label: 'Phase Angle', label_ko: '위상각', description: 'Low phase angle.', description_ko: '낮은 위상 각도 값' },
  { key: 'powerFactor', label: 'Power Factor', label_ko: '역률', description: 'The system is operating with a low power factor.', description_ko: '시스템이 낮은 역률로 작동하고 있습니다.' },
  { key: 'totalDemandDistortion', label: 'Total Demand Distortion (TDD)', label_ko: 'TDD', description: 'High TDD levels can indicate harmonic issues in the system.', description_ko: '높은 TDD 수치는 고조파 문제를 나타낼 수 있습니다.' },
  { key: 'power', label: 'Power', label_ko: '전력', description: 'Check the sources of excessive power.', description_ko: '과도한 전력의 원인을 확인하십시오.' },
  { key: 'dc', label: 'DC', label_ko: 'DC 전압', description: 'Inspect power supply circuits, verify component ratings.', description_ko: '전원 공급 회로를 점검하고, 부품 정격을 확인하십시오.' },
  { key: 'events', label: 'Events', label_ko: '이벤트', description: 'Power quality related events.', description_ko: '전력 품질 관련 이벤트 발생 정보입니다.' },
]

export const faultData = [
  { key: 'phaseOrder', label: 'Phase Order', label_ko: '상순서', description: 'Phase sequence error detected.', description_ko: '3상 전원의 상 순서 이상(역상)이 감지되었습니다.' },
  { key: 'noLoad', label: 'No Load', label_ko: '무부하', description: 'No load condition detected.', description_ko: '무부하 상태가 감지되었습니다.' },
  { key: 'overCurrent', label: 'Over Current', label_ko: '과전류', description: 'Current exceeds rated value.', description_ko: '정격 이상의 전류가 흐르고 있습니다.' },
  { key: 'cf', label: 'CF (Crest Factor)', label_ko: '파고율', description: 'Crest factor exceeds acceptable limits.', description_ko: '파형 왜곡으로 인한 파고율이 허용치를 초과했습니다.' },
  { key: 'noPower', label: 'No Power', label_ko: '무전원', description: 'No power supply detected.', description_ko: '전원이 공급되지 않는 상태입니다.' },
  { key: 'overVoltage', label: 'Over Voltage', label_ko: '과전압', description: 'Voltage exceeds rated value.', description_ko: '정격 이상의 전압이 인가되었습니다.' },
  { key: 'underVoltage', label: 'Under Voltage', label_ko: '저전압', description: 'Voltage below rated value.', description_ko: '정격 이하의 전압이 인가되었습니다.' },
  { key: 'lowFrequency', label: 'Low Frequency', label_ko: '저주파수', description: 'Frequency below rated value.', description_ko: '정격 이하의 주파수가 감지되었습니다.' },
  { key: 'vf', label: 'VF (Voltage/Frequency)', label_ko: 'V/F', description: 'Voltage/Frequency ratio abnormal.', description_ko: '전압/주파수 비율이 비정상입니다.' },
]

export const eventData = [
  { key: 'transientCurrentEvent', label: 'Transient Current Event', label_ko: '과도 전류 이벤트', description: 'Momentary current surge detected.', description_ko: '순간적인 전류 급변 현상이 감지되었습니다.' },
  { key: 'overCurrentEvent', label: 'Over Current Event', label_ko: '과전류 이벤트', description: 'Current exceeded threshold.', description_ko: '설정값 이상의 전류가 발생했습니다.' },
  { key: 'underCurrentEvent', label: 'Under Current Event', label_ko: '저전류 이벤트', description: 'Current dropped below threshold.', description_ko: '설정값 이하의 전류가 감지되었습니다.' },
  { key: 'sagEvent', label: 'Sag Event', label_ko: '순간전압강하 이벤트', description: 'Temporary voltage reduction detected.', description_ko: '전압이 일시적으로 저하되는 현상이 감지되었습니다.' },
  { key: 'swellEvent', label: 'Swell Event', label_ko: '순간전압상승 이벤트', description: 'Temporary voltage increase detected.', description_ko: '전압이 일시적으로 상승하는 현상이 감지되었습니다.' },
  { key: 'interruptionEvent', label: 'Interruption Event', label_ko: '순간정전 이벤트', description: 'Temporary power loss detected.', description_ko: '전압이 일시적으로 소실되는 현상이 감지되었습니다.' },
  { key: 'transientVoltageEvent', label: 'Transient Voltage Event', label_ko: '과도 전압 이벤트', description: 'Momentary voltage surge detected.', description_ko: '순간적인 전압 급변 현상이 감지되었습니다.' },
]

