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
        description: 'Irregular and chaotic flow phenomenon in fluids\nCauses\nInappropriate fan operating parameters\nInappropriate blade angle\nPoor inlet/outlet conditions\nPoor duct design\nEffects\nReduced efficiency\nIncreased noise\nIncreased vibration\nEnergy loss',
        description_ko: '유체의 불규칙하고 혼란스러운 흐름 현상\n원인\n팬 작동 매개변수 부적절\n날개 각도 부적절\n흡입/배출 조건 불량\n덕트 설계 불량\n영향\n효율 저하\n소음 증가\n진동 증가\n에너지 손실',
        //image: '/glossary/device.png',  // 이미지 경로 (선택사항)
      },
      { 
        key: 'blade', 
        label: 'Blade', 
        label_ko: '팬 블레이드',
        description: 'Rotating component used to move air or circulate fluids\nCauses\nBlade damage, wear, corrosion\nDebris and contaminant accumulation\nBlade imbalance\nManufacturing defects\nEffects\nExcessive vibration\nReduced efficiency\nIncreased noise\nMechanical stress on fan assembly and bearings',
        description_ko: '공기를 이동시키거나 유체를 순환시키는 데 사용되는 회전 부품\n원인\n블레이드 손상·마모·부식\n이물질 및 오염물 축적\n블레이드 불균형\n제조 결함\n영향\n과도한 진동 발생\n효율 저하\n소음 증가\n팬 어셈블리 및 베어링에 기계적 스트레스',
      },
      { 
        key: 'mechanicalUnbalance', 
        label: 'Mechanical Unbalance', 
        label_ko: '기계적 불균형',
        description: 'Phenomenon that occurs when the mass center of a rotating component does not coincide with its rotational axis\nCauses\nMisalignment\nUneven wear\nForeign object accumulation\nManufacturing defects\nComponent damage\nEffects\nExcessive vibration at rotational frequency (1x RPM)\nBearing wear\nSeal failure\nStructural fatigue',
        description_ko: '회전 부품의 질량 중심이 회전축과 일치하지 않을 때 발생하는 현상\n원인\n정렬 불량\n불균등 마모\n이물질 축적\n제조 결함\n부품 손상\n영향\n회전 주파수(1x RPM)에서 과도한 진동\n베어링 마모\n씰 고장\n구조적 피로',
      },
      { 
        key: 'softFoot', 
        label: 'Soft Foot', 
        label_ko: '소프트 풋',
        description: 'Condition where one or more machine feet do not make full contact with the baseplate, causing frame distortion when mounting bolts are tightened\nCauses\nPoor baseplate flatness\nMachine foot height mismatch\nPresence of debris or contaminants\nAlignment errors during installation\nEffects\nMisalignment\nIncreased vibration\nPremature bearing failure\nFrame distortion',
        description_ko: '장비의 하나 이상의 발이 베이스플레이트와 완전히 접촉하지 않아 마운팅 볼트를 조일 때 프레임이 변형되는 상태\n원인\n베이스플레이트 평탄도 불량\n장비 발의 높이 불일치\n이물질이나 오염물 존재\n설치 시 정렬 오류\n영향\n정렬 불량\n진동 증가\n조기 베어링 고장\n프레임 변형',
      },
      { 
        key: 'torqueRipple', 
        label: 'Torque Ripple', 
        label_ko: '토크 리플',
        description: 'Phenomenon where motor torque output is not constant and periodically fluctuates during rotation\nCauses\nAbnormal current waveforms (harmonics, PWM ripple)\nSlot/pole structure (cogging torque)\nNon-uniform flux distribution\nControl algorithm limitations (FOC resolution, sampling period, etc.)\nEffects\nIncreased vibration and noise\nSpeed instability at low speeds\nIncreased bearing and mechanical wear\nReduced precision control performance',
        description_ko: '모터가 회전할 때 출력 토크가 일정하지 않고 주기적으로 흔들리는 현상\n원인\n전류 파형의 비이상성(고조파, PWM 리플)\n슬롯·자극 구조(코깅 토크)\n자속 분포 불균형\n제어 알고리즘 한계(FOC 해상도, 샘플링 주기 등)\n영향\n진동·소음 증가\n저속에서 속도 불안정\n베어링·기계적 마모 증가\n정밀 제어 성능 저하',
      },
      { 
        key: 'load', 
        label: 'Load', 
        label_ko: '부하',
        description: 'Magnitude of power or torque delivered to equipment\nCauses\nOverload conditions\nUnbalanced load distribution\nExcessive single-phase load\nEffects\nOverheating\nMechanical stress\nPremature failure\nReduced efficiency',
        description_ko: '설비에 전달되는 전력이나 토크의 크기\n원인\n과부하 조건\n부하 분산 불균형\n단상 부하 과다\n영향\n과열\n기계적 스트레스\n조기 고장\n효율 저하',
      },
      { 
        key: 'cableConnection', 
        label: 'Cable Connection', 
        label_ko: '케이블 연결',
        description: 'Component that transmits power or signals through electrical connections\nCauses\nLoose terminals\nCorrosion, oxidation\nOverheating (discoloration)\nPhysical damage\nEffects\nHigh resistance\nVoltage drop\nLocalized heating\nArcing',
        description_ko: '전기적 연결을 통해 전력이나 신호를 전달하는 부품\n원인\n단자 느슨함\n부식·산화\n과열(변색)\n물리적 손상\n영향\n고저항\n전압 강하\n국부 가열\n아크 발생',
      },
      { 
        key: 'noiseVibration', 
        label: 'Noise/Vibration', 
        label_ko: '소음/진동',
        description: 'Important indicator of mechanical condition of equipment\nCauses\nBearing wear\nRotor imbalance\nMisalignment\nLoose components\nEffects\nAccelerated wear\nFatigue failure\nPotential for serious failure\nDeterioration of working environment',
        description_ko: '설비의 기계적 상태를 나타내는 중요한 지표\n원인\n베어링 마모\n회전자 불균형\n정렬 불량\n부품 느슨함\n영향\n마모 가속화\n피로 파괴\n심각한 고장으로 발전 가능\n작업 환경 악화',
      },
      { 
        key: 'heat', 
        label: 'Heat', 
        label_ko: '열',
        description: 'Temperature rise caused by electrical losses or mechanical friction during equipment operation\nCauses\nIncreased harmonic stress\nAdditional losses in conductors, transformers, and motors\nInsufficient cooling\nOverload\nEffects\nInsulation degradation\nReduced equipment lifespan\nThermal expansion issues\nReduced efficiency',
        description_ko: '설비 작동 중 전기적 손실이나 기계적 마찰로 인해 발생하는 온도 상승\n원인\n고조파 스트레스 증가\n도체·변압기·모터에서 추가 손실\n냉각 부족\n과부하\n영향\n절연 열화\n설비 수명 단축\n열팽창 문제\n효율 저하',
      },
      { 
        key: 'incomingVoltage', 
        label: 'Incoming Voltage', 
        label_ko: '입력 전압',
        description: 'Electrical potential difference supplied to equipment, a fundamental condition for normal equipment operation\nCauses\nUnstable power supply\nTransformer tap setting errors\nUnbalanced load distribution\nVoltage regulation equipment failure\nEffects\nEquipment malfunction\nOverheating\nReduced efficiency\nPremature failure',
        description_ko: '설비에 공급되는 전기적 전위차로, 설비의 정상 작동을 위한 기본 조건\n원인\n공급 전원 불안정\n변압기 탭 설정 오류\n부하 분산 불균형\n전압 조정 장치 고장\n영향\n설비 오작동\n과열\n효율 저하\n조기 고장',
      },
      { 
        key: 'rotor', 
        label: 'Rotor', 
        label_ko: '회전자',
        description: 'Rotating part of a motor or generator that interacts with magnetic flux to generate torque\nCauses\nMisalignment\nPhysical damage, cracks\nImbalance\nBar damage in squirrel cage rotors\nEffects\nExcessive vibration\nIncreased noise\nBearing wear\nMechanical stress',
        description_ko: '모터나 발전기에서 회전하는 부분으로, 자속과 상호작용하여 토크를 생성\n원인\n정렬 불량\n물리적 손상·균열\n불균형\n와전류형 회전자의 바 손상\n영향\n과도한 진동\n소음 증가\n베어링 마모\n기계적 스트레스',
      },
      { 
        key: 'stator', 
        label: 'Stator', 
        label_ko: '고정자',
        description: 'Stationary part of a motor or generator that includes windings to create a rotating magnetic field\nCauses\nInsulation breakdown\nShorted windings\nOverheating\nContamination\nEffects\nReduced efficiency\nOverheating\nPhase imbalance\nMotor failure',
        description_ko: '모터나 발전기에서 고정되어 있는 부분으로, 권선을 포함하여 회전 자기장을 생성\n원인\n절연 파괴\n단락 권선\n과열\n오염\n영향\n효율 저하\n과열\n상 불균형\n모터 고장',
      },
      { 
        key: 'bearing', 
        label: 'Bearing', 
        label_ko: '베어링',
        description: 'Mechanical component that supports rotating shafts and minimizes friction to enable smooth rotational motion\nCauses\nWear, pitting, brinelling\nOverheating (discoloration)\nExcessive play\nInadequate lubrication\nContamination\nEffects\nRotor contact\nWinding damage\nCatastrophic failure\nMost common cause of motor failure',
        description_ko: '회전 축을 지지하고 마찰을 최소화하여 회전 운동을 원활하게 하는 기계 부품\n원인\n마모·피팅·브리넬링\n과열(변색)\n과도한 플레이\n윤활 부족\n오염물질\n영향\n회전자 접촉\n권선 손상\n치명적 고장\n모터 고장의 가장 흔한 원인',
      },
      { 
        key: 'dcLink', 
        label: 'DC Link', 
        label_ko: 'DC 링크',
        description: 'Circuit that smooths DC power and stores energy in inverters or converters\nCauses\nCapacitor performance degradation\nCapacitor swelling, leakage\nOverheating\nPoor connections\nEffects\nVoltage instability\nIncreased harmonics\nInverter tripping\nReduced motor performance',
        description_ko: '인버터나 컨버터에서 직류 전원을 평활화하고 에너지를 저장하는 회로\n원인\n커패시터 성능 저하\n커패시터 팽창·누설\n과열\n연결 불량\n영향\n전압 불안정\n고조파 증가\n인버터 트립\n모터 성능 저하',
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
        description: 'Phenomenon where pressure at the pump inlet drops below the vapor pressure of the liquid, causing vapor bubbles to form and collapse violently\nCauses\nInsufficient NPSH (Net Positive Suction Head)\nExcessive flow rate\nSuction line restrictions\nInsufficient liquid level in source tank\nExcessive pump speed\nEffects\nIncreased noise and vibration\nErosion of impeller blades\nReduced efficiency\nPremature pump failure',
        description_ko: '펌프 흡입구에서 압력이 액체의 증기압보다 낮아져 증기 기포가 형성되고 폭발적으로 붕괴되는 현상\n원인\nNPSH(순흡입양정) 부족\n유량 과다\n흡입 라인 제한\n원천 탱크의 액체 레벨 부족\n펌프 속도 과다\n영향\n소음·진동 증가\n임펠러 블레이드 침식\n효율 저하\n조기 펌프 고장',
      },
      { 
        key: 'vane', 
        label: 'Vane', 
        label_ko: '베인',
        description: 'Rotating blade component inside a pump that moves fluid\nCauses\nWear, erosion, cavitation damage\nCracks\nBlockages from debris or contaminants\nManufacturing defects\nEffects\nReduced pump efficiency\nFlow imbalance\nIncreased vibration\nComplete pump failure',
        description_ko: '펌프 내부에서 유체를 이동시키는 회전 날개 부품\n원인\n마모·침식·캐비테이션 손상\n균열\n이물질이나 오염물로 인한 차단\n제조 결함\n영향\n펌프 효율 저하\n유량 불균형\n진동 증가\n완전한 펌프 고장',
      },
      { 
        key: 'mechanicalUnbalance', 
        label: 'Mechanical Unbalance', 
        label_ko: '기계적 불균형',
        description: 'Phenomenon that occurs when the mass center of a rotating component does not coincide with its rotational axis\nCauses\nMisalignment\nUneven wear\nForeign object accumulation\nManufacturing defects\nComponent damage\nEffects\nExcessive vibration at rotational frequency (1x RPM)\nBearing wear\nSeal failure\nStructural fatigue',
        description_ko: '회전 부품의 질량 중심이 회전축과 일치하지 않을 때 발생하는 현상\n원인\n정렬 불량\n불균등 마모\n이물질 축적\n제조 결함\n부품 손상\n영향\n회전 주파수(1x RPM)에서 과도한 진동\n베어링 마모\n씰 고장\n구조적 피로',
      },
      { 
        key: 'softFoot', 
        label: 'Soft Foot', 
        label_ko: '소프트 풋',
        description: 'Condition where one or more machine feet do not make full contact with the baseplate, causing frame distortion when mounting bolts are tightened\nCauses\nPoor baseplate flatness\nMachine foot height mismatch\nPresence of debris or contaminants\nAlignment errors during installation\nEffects\nMisalignment\nIncreased vibration\nPremature bearing failure\nFrame distortion',
        description_ko: '장비의 하나 이상의 발이 베이스플레이트와 완전히 접촉하지 않아 마운팅 볼트를 조일 때 프레임이 변형되는 상태\n원인\n베이스플레이트 평탄도 불량\n장비 발의 높이 불일치\n이물질이나 오염물 존재\n설치 시 정렬 오류\n영향\n정렬 불량\n진동 증가\n조기 베어링 고장\n프레임 변형',
      },
      { 
        key: 'torqueRipple', 
        label: 'Torque Ripple', 
        label_ko: '토크 리플',
        description: 'Phenomenon where motor torque output is not constant and periodically fluctuates during rotation\nCauses\nAbnormal current waveforms (harmonics, PWM ripple)\nSlot/pole structure (cogging torque)\nNon-uniform flux distribution\nControl algorithm limitations (FOC resolution, sampling period, etc.)\nEffects\nIncreased vibration and noise\nSpeed instability at low speeds\nIncreased bearing and mechanical wear\nReduced precision control performance',
        description_ko: '모터가 회전할 때 출력 토크가 일정하지 않고 주기적으로 흔들리는 현상\n원인\n전류 파형의 비이상성(고조파, PWM 리플)\n슬롯·자극 구조(코깅 토크)\n자속 분포 불균형\n제어 알고리즘 한계(FOC 해상도, 샘플링 주기 등)\n영향\n진동·소음 증가\n저속에서 속도 불안정\n베어링·기계적 마모 증가\n정밀 제어 성능 저하',
      },
      { 
        key: 'load', 
        label: 'Load', 
        label_ko: '부하',
        description: 'Magnitude of power or torque delivered to equipment\nCauses\nOverload conditions\nUnbalanced load distribution\nExcessive single-phase load\nEffects\nOverheating\nMechanical stress\nPremature failure\nReduced efficiency',
        description_ko: '설비에 전달되는 전력이나 토크의 크기\n원인\n과부하 조건\n부하 분산 불균형\n단상 부하 과다\n영향\n과열\n기계적 스트레스\n조기 고장\n효율 저하',
      },
      { 
        key: 'cableConnection', 
        label: 'Cable Connection', 
        label_ko: '케이블 연결',
        description: 'Component that transmits power or signals through electrical connections\nCauses\nLoose terminals\nCorrosion, oxidation\nOverheating (discoloration)\nPhysical damage\nEffects\nHigh resistance\nVoltage drop\nLocalized heating\nArcing',
        description_ko: '전기적 연결을 통해 전력이나 신호를 전달하는 부품\n원인\n단자 느슨함\n부식·산화\n과열(변색)\n물리적 손상\n영향\n고저항\n전압 강하\n국부 가열\n아크 발생',
      },
      { 
        key: 'noiseVibration', 
        label: 'Noise/Vibration', 
        label_ko: '소음/진동',
        description: 'Important indicator of mechanical condition of equipment\nCauses\nBearing wear\nRotor imbalance\nMisalignment\nLoose components\nEffects\nAccelerated wear\nFatigue failure\nPotential for serious failure\nDeterioration of working environment',
        description_ko: '설비의 기계적 상태를 나타내는 중요한 지표\n원인\n베어링 마모\n회전자 불균형\n정렬 불량\n부품 느슨함\n영향\n마모 가속화\n피로 파괴\n심각한 고장으로 발전 가능\n작업 환경 악화',
      },
      { 
        key: 'heat', 
        label: 'Heat', 
        label_ko: '열',
        description: 'Temperature rise caused by electrical losses or mechanical friction during equipment operation\nCauses\nIncreased harmonic stress\nAdditional losses in conductors, transformers, and motors\nInsufficient cooling\nOverload\nEffects\nInsulation degradation\nReduced equipment lifespan\nThermal expansion issues\nReduced efficiency',
        description_ko: '설비 작동 중 전기적 손실이나 기계적 마찰로 인해 발생하는 온도 상승\n원인\n고조파 스트레스 증가\n도체·변압기·모터에서 추가 손실\n냉각 부족\n과부하\n영향\n절연 열화\n설비 수명 단축\n열팽창 문제\n효율 저하',
      },
      { 
        key: 'incomingVoltage', 
        label: 'Incoming Voltage', 
        label_ko: '입력 전압',
        description: 'Electrical potential difference supplied to equipment, a fundamental condition for normal equipment operation\nCauses\nUnstable power supply\nTransformer tap setting errors\nUnbalanced load distribution\nVoltage regulation equipment failure\nEffects\nEquipment malfunction\nOverheating\nReduced efficiency\nPremature failure',
        description_ko: '설비에 공급되는 전기적 전위차로, 설비의 정상 작동을 위한 기본 조건\n원인\n공급 전원 불안정\n변압기 탭 설정 오류\n부하 분산 불균형\n전압 조정 장치 고장\n영향\n설비 오작동\n과열\n효율 저하\n조기 고장',
      },
      { 
        key: 'rotor', 
        label: 'Rotor', 
        label_ko: '회전자',
        description: 'Rotating part of a motor or generator that interacts with magnetic flux to generate torque\nCauses\nMisalignment\nPhysical damage, cracks\nImbalance\nBar damage in squirrel cage rotors\nEffects\nExcessive vibration\nIncreased noise\nBearing wear\nMechanical stress',
        description_ko: '모터나 발전기에서 회전하는 부분으로, 자속과 상호작용하여 토크를 생성\n원인\n정렬 불량\n물리적 손상·균열\n불균형\n와전류형 회전자의 바 손상\n영향\n과도한 진동\n소음 증가\n베어링 마모\n기계적 스트레스',
      },
      { 
        key: 'stator', 
        label: 'Stator', 
        label_ko: '고정자',
        description: 'Stationary part of a motor or generator that includes windings to create a rotating magnetic field\nCauses\nInsulation breakdown\nShorted windings\nOverheating\nContamination\nEffects\nReduced efficiency\nOverheating\nPhase imbalance\nMotor failure',
        description_ko: '모터나 발전기에서 고정되어 있는 부분으로, 권선을 포함하여 회전 자기장을 생성\n원인\n절연 파괴\n단락 권선\n과열\n오염\n영향\n효율 저하\n과열\n상 불균형\n모터 고장',
      },
      { 
        key: 'bearing', 
        label: 'Bearing', 
        label_ko: '베어링',
        description: 'Mechanical component that supports rotating shafts and minimizes friction to enable smooth rotational motion\nCauses\nWear, pitting, brinelling\nOverheating (discoloration)\nExcessive play\nInadequate lubrication\nContamination\nEffects\nRotor contact\nWinding damage\nCatastrophic failure\nMost common cause of motor failure',
        description_ko: '회전 축을 지지하고 마찰을 최소화하여 회전 운동을 원활하게 하는 기계 부품\n원인\n마모·피팅·브리넬링\n과열(변색)\n과도한 플레이\n윤활 부족\n오염물질\n영향\n회전자 접촉\n권선 손상\n치명적 고장\n모터 고장의 가장 흔한 원인',
      },
      { 
        key: 'dcLink', 
        label: 'DC Link', 
        label_ko: 'DC 링크',
        description: 'Circuit that smooths DC power and stores energy in inverters or converters\nCauses\nCapacitor performance degradation\nCapacitor swelling, leakage\nOverheating\nPoor connections\nEffects\nVoltage instability\nIncreased harmonics\nInverter tripping\nReduced motor performance',
        description_ko: '인버터나 컨버터에서 직류 전원을 평활화하고 에너지를 저장하는 회로\n원인\n커패시터 성능 저하\n커패시터 팽창·누설\n과열\n연결 불량\n영향\n전압 불안정\n고조파 증가\n인버터 트립\n모터 성능 저하',
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
        description: 'Phenomenon where motor torque output is not constant and periodically fluctuates during rotation\nCauses\nAbnormal current waveforms (harmonics, PWM ripple)\nSlot/pole structure (cogging torque)\nNon-uniform flux distribution\nControl algorithm limitations (FOC resolution, sampling period, etc.)\nEffects\nIncreased vibration and noise\nSpeed instability at low speeds\nIncreased bearing and mechanical wear\nReduced precision control performance',
        description_ko: '모터가 회전할 때 출력 토크가 일정하지 않고 주기적으로 흔들리는 현상\n원인\n전류 파형의 비이상성(고조파, PWM 리플)\n슬롯·자극 구조(코깅 토크)\n자속 분포 불균형\n제어 알고리즘 한계(FOC 해상도, 샘플링 주기 등)\n영향\n진동·소음 증가\n저속에서 속도 불안정\n베어링·기계적 마모 증가\n정밀 제어 성능 저하',
      },
      { 
        key: 'mechanicalUnbalance', 
        label: 'Mechanical Unbalance', 
        label_ko: '기계적 불균형',
        description: 'Phenomenon that occurs when the mass center of a rotating component does not coincide with its rotational axis\nCauses\nMisalignment\nUneven wear\nForeign object accumulation\nManufacturing defects\nComponent damage\nEffects\nExcessive vibration at rotational frequency (1x RPM)\nBearing wear\nSeal failure\nStructural fatigue',
        description_ko: '회전 부품의 질량 중심이 회전축과 일치하지 않을 때 발생하는 현상\n원인\n정렬 불량\n불균등 마모\n이물질 축적\n제조 결함\n부품 손상\n영향\n회전 주파수(1x RPM)에서 과도한 진동\n베어링 마모\n씰 고장\n구조적 피로',
      },
      { 
        key: 'softFoot', 
        label: 'Soft Foot', 
        label_ko: '소프트 풋',
        description: 'Condition where one or more machine feet do not make full contact with the baseplate, causing frame distortion when mounting bolts are tightened\nCauses\nPoor baseplate flatness\nMachine foot height mismatch\nPresence of debris or contaminants\nAlignment errors during installation\nEffects\nMisalignment\nIncreased vibration\nPremature bearing failure\nFrame distortion',
        description_ko: '장비의 하나 이상의 발이 베이스플레이트와 완전히 접촉하지 않아 마운팅 볼트를 조일 때 프레임이 변형되는 상태\n원인\n베이스플레이트 평탄도 불량\n장비 발의 높이 불일치\n이물질이나 오염물 존재\n설치 시 정렬 오류\n영향\n정렬 불량\n진동 증가\n조기 베어링 고장\n프레임 변형',
      },
      { 
        key: 'load', 
        label: 'Load', 
        label_ko: '부하',
        description: 'Magnitude of power or torque delivered to equipment\nCauses\nOverload conditions\nUnbalanced load distribution\nExcessive single-phase load\nEffects\nOverheating\nMechanical stress\nPremature failure\nReduced efficiency',
        description_ko: '설비에 전달되는 전력이나 토크의 크기\n원인\n과부하 조건\n부하 분산 불균형\n단상 부하 과다\n영향\n과열\n기계적 스트레스\n조기 고장\n효율 저하',
      },
      { 
        key: 'cableConnection', 
        label: 'Cable Connection', 
        label_ko: '케이블 연결',
        description: 'Component that transmits power or signals through electrical connections\nCauses\nLoose terminals\nCorrosion, oxidation\nOverheating (discoloration)\nPhysical damage\nEffects\nHigh resistance\nVoltage drop\nLocalized heating\nArcing',
        description_ko: '전기적 연결을 통해 전력이나 신호를 전달하는 부품\n원인\n단자 느슨함\n부식·산화\n과열(변색)\n물리적 손상\n영향\n고저항\n전압 강하\n국부 가열\n아크 발생',
      },
      { 
        key: 'noiseVibration', 
        label: 'Noise/Vibration', 
        label_ko: '소음/진동',
        description: 'Important indicator of mechanical condition of equipment\nCauses\nBearing wear\nRotor imbalance\nMisalignment\nLoose components\nEffects\nAccelerated wear\nFatigue failure\nPotential for serious failure\nDeterioration of working environment',
        description_ko: '설비의 기계적 상태를 나타내는 중요한 지표\n원인\n베어링 마모\n회전자 불균형\n정렬 불량\n부품 느슨함\n영향\n마모 가속화\n피로 파괴\n심각한 고장으로 발전 가능\n작업 환경 악화',
      },
      { 
        key: 'heat', 
        label: 'Heat', 
        label_ko: '열',
        description: 'Temperature rise caused by electrical losses or mechanical friction during equipment operation\nCauses\nIncreased harmonic stress\nAdditional losses in conductors, transformers, and motors\nInsufficient cooling\nOverload\nEffects\nInsulation degradation\nReduced equipment lifespan\nThermal expansion issues\nReduced efficiency',
        description_ko: '설비 작동 중 전기적 손실이나 기계적 마찰로 인해 발생하는 온도 상승\n원인\n고조파 스트레스 증가\n도체·변압기·모터에서 추가 손실\n냉각 부족\n과부하\n영향\n절연 열화\n설비 수명 단축\n열팽창 문제\n효율 저하',
      },
      { 
        key: 'incomingVoltage', 
        label: 'Incoming Voltage', 
        label_ko: '입력 전압',
        description: 'Electrical potential difference supplied to equipment, a fundamental condition for normal equipment operation\nCauses\nUnstable power supply\nTransformer tap setting errors\nUnbalanced load distribution\nVoltage regulation equipment failure\nEffects\nEquipment malfunction\nOverheating\nReduced efficiency\nPremature failure',
        description_ko: '설비에 공급되는 전기적 전위차로, 설비의 정상 작동을 위한 기본 조건\n원인\n공급 전원 불안정\n변압기 탭 설정 오류\n부하 분산 불균형\n전압 조정 장치 고장\n영향\n설비 오작동\n과열\n효율 저하\n조기 고장',
      },
      { 
        key: 'rotor', 
        label: 'Rotor', 
        label_ko: '회전자',
        description: 'Rotating part of a motor or generator that interacts with magnetic flux to generate torque\nCauses\nMisalignment\nPhysical damage, cracks\nImbalance\nBar damage in squirrel cage rotors\nEffects\nExcessive vibration\nIncreased noise\nBearing wear\nMechanical stress',
        description_ko: '모터나 발전기에서 회전하는 부분으로, 자속과 상호작용하여 토크를 생성\n원인\n정렬 불량\n물리적 손상·균열\n불균형\n와전류형 회전자의 바 손상\n영향\n과도한 진동\n소음 증가\n베어링 마모\n기계적 스트레스',
      },
      { 
        key: 'stator', 
        label: 'Stator', 
        label_ko: '고정자',
        description: 'Stationary part of a motor or generator that includes windings to create a rotating magnetic field\nCauses\nInsulation breakdown\nShorted windings\nOverheating\nContamination\nEffects\nReduced efficiency\nOverheating\nPhase imbalance\nMotor failure',
        description_ko: '모터나 발전기에서 고정되어 있는 부분으로, 권선을 포함하여 회전 자기장을 생성\n원인\n절연 파괴\n단락 권선\n과열\n오염\n영향\n효율 저하\n과열\n상 불균형\n모터 고장',
      },
      { 
        key: 'bearing', 
        label: 'Bearing', 
        label_ko: '베어링',
        description: 'Mechanical component that supports rotating shafts and minimizes friction to enable smooth rotational motion\nCauses\nWear, pitting, brinelling\nOverheating (discoloration)\nExcessive play\nInadequate lubrication\nContamination\nEffects\nRotor contact\nWinding damage\nCatastrophic failure\nMost common cause of motor failure',
        description_ko: '회전 축을 지지하고 마찰을 최소화하여 회전 운동을 원활하게 하는 기계 부품\n원인\n마모·피팅·브리넬링\n과열(변색)\n과도한 플레이\n윤활 부족\n오염물질\n영향\n회전자 접촉\n권선 손상\n치명적 고장\n모터 고장의 가장 흔한 원인',
      },
      { 
        key: 'dcLink', 
        label: 'DC Link', 
        label_ko: 'DC 링크',
        description: 'Circuit that smooths DC power and stores energy in inverters or converters\nCauses\nCapacitor performance degradation\nCapacitor swelling, leakage\nOverheating\nPoor connections\nEffects\nVoltage instability\nIncreased harmonics\nInverter tripping\nReduced motor performance',
        description_ko: '인버터나 컨버터에서 직류 전원을 평활화하고 에너지를 저장하는 회로\n원인\n커패시터 성능 저하\n커패시터 팽창·누설\n과열\n연결 불량\n영향\n전압 불안정\n고조파 증가\n인버터 트립\n모터 성능 저하',
      },
    ]
  },
  {
    key: 'motorFeed',
    label: 'Motor Feed',
    items: [
      { key: 'load', label: 'Load', label_ko: '부하', description: 'Magnitude of power or torque delivered to equipment\nCauses\nOverload conditions\nUnbalanced load distribution\nExcessive single-phase load\nEffects\nOverheating\nMechanical stress\nPremature failure\nReduced efficiency', description_ko: '설비에 전달되는 전력이나 토크의 크기\n원인\n과부하 조건\n부하 분산 불균형\n단상 부하 과다\n영향\n과열\n기계적 스트레스\n조기 고장\n효율 저하' },
      { key: 'cableConnection', label: 'Cable Connection', label_ko: '케이블 연결', description: 'Component that transmits power or signals through electrical connections\nCauses\nLoose terminals\nCorrosion, oxidation\nOverheating (discoloration)\nPhysical damage\nEffects\nHigh resistance\nVoltage drop\nLocalized heating\nArcing', description_ko: '전기적 연결을 통해 전력이나 신호를 전달하는 부품\n원인\n단자 느슨함\n부식·산화\n과열(변색)\n물리적 손상\n영향\n고저항\n전압 강하\n국부 가열\n아크 발생' },
      { key: 'noiseVibration', label: 'Noise/Vibration', label_ko: '소음/진동', description: 'Important indicator of mechanical condition of equipment\nCauses\nBearing wear\nRotor imbalance\nMisalignment\nLoose components\nEffects\nAccelerated wear\nFatigue failure\nPotential for serious failure\nDeterioration of working environment', description_ko: '설비의 기계적 상태를 나타내는 중요한 지표\n원인\n베어링 마모\n회전자 불균형\n정렬 불량\n부품 느슨함\n영향\n마모 가속화\n피로 파괴\n심각한 고장으로 발전 가능\n작업 환경 악화' },
      { key: 'heat', label: 'Heat', label_ko: '열', description: 'Temperature rise caused by electrical losses or mechanical friction during equipment operation\nCauses\nIncreased harmonic stress\nAdditional losses in conductors, transformers, and motors\nInsufficient cooling\nOverload\nEffects\nInsulation degradation\nReduced equipment lifespan\nThermal expansion issues\nReduced efficiency', description_ko: '설비 작동 중 전기적 손실이나 기계적 마찰로 인해 발생하는 온도 상승\n원인\n고조파 스트레스 증가\n도체·변압기·모터에서 추가 손실\n냉각 부족\n과부하\n영향\n절연 열화\n설비 수명 단축\n열팽창 문제\n효율 저하' },
      { key: 'incomingVoltage', label: 'Incoming Voltage', label_ko: '입력 전압', description: 'Electrical potential difference supplied to equipment, a fundamental condition for normal equipment operation\nCauses\nUnstable power supply\nTransformer tap setting errors\nUnbalanced load distribution\nVoltage regulation equipment failure\nEffects\nEquipment malfunction\nOverheating\nReduced efficiency\nPremature failure', description_ko: '설비에 공급되는 전기적 전위차로, 설비의 정상 작동을 위한 기본 조건\n원인\n공급 전원 불안정\n변압기 탭 설정 오류\n부하 분산 불균형\n전압 조정 장치 고장\n영향\n설비 오작동\n과열\n효율 저하\n조기 고장' },
      { key: 'dcLink', label: 'DC Link', label_ko: 'DC 링크', description: 'Circuit that smooths DC power and stores energy in inverters or converters\nCauses\nCapacitor performance degradation\nCapacitor swelling, leakage\nOverheating\nPoor connections\nEffects\nVoltage instability\nIncreased harmonics\nInverter tripping\nReduced motor performance', description_ko: '인버터나 컨버터에서 직류 전원을 평활화하고 에너지를 저장하는 회로\n원인\n커패시터 성능 저하\n커패시터 팽창·누설\n과열\n연결 불량\n영향\n전압 불안정\n고조파 증가\n인버터 트립\n모터 성능 저하' },
    ]
  },
  {
    key: 'powerSupply',
    label: 'Power Supply',
    items: [
      { key: 'noiseVibration', label: 'Noise/Vibration', label_ko: '소음/진동', description: 'Important indicator of mechanical condition of equipment\nCauses\nBearing wear\nRotor imbalance\nMisalignment\nLoose components\nEffects\nAccelerated wear\nFatigue failure\nPotential for serious failure\nDeterioration of working environment', description_ko: '설비의 기계적 상태를 나타내는 중요한 지표\n원인\n베어링 마모\n회전자 불균형\n정렬 불량\n부품 느슨함\n영향\n마모 가속화\n피로 파괴\n심각한 고장으로 발전 가능\n작업 환경 악화' },
      { key: 'heat', label: 'Heat', label_ko: '열', description: 'Temperature rise caused by electrical losses or mechanical friction during equipment operation\nCauses\nIncreased harmonic stress\nAdditional losses in conductors, transformers, and motors\nInsufficient cooling\nOverload\nEffects\nInsulation degradation\nReduced equipment lifespan\nThermal expansion issues\nReduced efficiency', description_ko: '설비 작동 중 전기적 손실이나 기계적 마찰로 인해 발생하는 온도 상승\n원인\n고조파 스트레스 증가\n도체·변압기·모터에서 추가 손실\n냉각 부족\n과부하\n영향\n절연 열화\n설비 수명 단축\n열팽창 문제\n효율 저하' },
      { key: 'incomingVoltage', label: 'Incoming Voltage', label_ko: '입력 전압', description: 'Electrical potential difference supplied to equipment, a fundamental condition for normal equipment operation\nCauses\nUnstable power supply\nTransformer tap setting errors\nUnbalanced load distribution\nVoltage regulation equipment failure\nEffects\nEquipment malfunction\nOverheating\nReduced efficiency\nPremature failure', description_ko: '설비에 공급되는 전기적 전위차로, 설비의 정상 작동을 위한 기본 조건\n원인\n공급 전원 불안정\n변압기 탭 설정 오류\n부하 분산 불균형\n전압 조정 장치 고장\n영향\n설비 오작동\n과열\n효율 저하\n조기 고장' },
      { key: 'rectifier', label: 'Rectifier', label_ko: '정류기', description: 'Circuit that converts AC to DC\nCauses\nDiode failure (open or short circuit)\nUnbalanced output voltage/current\nExcessive heat damage\nPoor heat sinking\nEffects\nIncreased output ripple\nReduced efficiency\nComplete power supply failure\nPhase problems', description_ko: '교류를 직류로 변환하는 회로\n원인\n다이오드 고장(개방 또는 단락)\n출력 전압/전류 불균형\n과도한 열 손상\n방열 처리 불량\n영향\n출력 리플 증가\n효율 저하\n전원 공급 장치 완전 고장\n위상 문제' },
      { key: 'switching', label: 'Switching', label_ko: '스위칭', description: 'Operation of turning switches on and off for power conversion\nCauses\nExcessive switching losses\nInsufficient cooling\nComponent performance degradation\nPoor EMI filtering\nEffects\nOverheating\nElectromagnetic interference (EMI)\nInterference with other equipment\nIncreased losses', description_ko: '전력 변환을 위해 스위치를 켜고 끄는 동작\n원인\n과도한 스위칭 손실\n냉각 부족\n부품 성능 저하\nEMI 필터링 불량\n영향\n과열\n전자기 간섭(EMI)\n다른 설비 간섭\n손실 증가' },
    ]
  },
  {
    key: 'transformer',
    label: 'Transformer',
    items: [
      { key: 'core', label: 'Core', label_ko: '코어', description: 'Magnetic material in a transformer that forms magnetic flux and transfers energy through electromagnetic induction\nCauses\nLamination damage (bent, broken, or delaminated sheets)\nCore loosening\nLocalized overheating (hot spots)\nMagnetic saturation\nEffects\nIncreased core losses\nExcessive heating\nIncreased magnetizing current\nReduced transformer efficiency', description_ko: '변압기에서 자속을 형성하고 전자기 유도를 통해 에너지를 전달하는 자성 재료\n원인\n적층 손상(휘거나 깨지거나 박리된 시트)\n코어 느슨해짐\n국부 과열(핫스팟)\n자성 포화\n영향\n코어 손실 증가\n과도한 가열\n여자 전류 증가\n변압기 효율 저하' },
      { key: 'load', label: 'Load', label_ko: '부하', description: 'Magnitude of power delivered to the transformer\nCauses\nContinuous overload\nUnbalanced load distribution\nExcessive single-phase load\nEffects\nExcessive temperature rise\nInsulation degradation\nReduced transformer life\nThermal failure', description_ko: '변압기에 전달되는 전력의 크기\n원인\n지속적인 과부하\n부하 분산 불균형\n단상 부하 과다\n영향\n과도한 온도 상승\n절연 열화\n변압기 수명 단축\n열적 고장' },
      { key: 'groundFault', label: 'Ground Fault', label_ko: '지락', description: 'Phenomenon where an energized conductor makes contact with ground or grounded equipment, causing current to flow to ground\nCauses\nInsulation breakdown\nPoor grounding system\nUnbalanced load\nCable damage\nEffects\nEquipment damage\nElectrical shock hazards\nSystem instability\nProtective device operation', description_ko: '활선 도체가 접지 또는 접지된 설비와 접촉하여 전류가 지면으로 흐르는 현상\n원인\n절연 파괴\n접지 시스템 불량\n불평형 부하\n케이블 손상\n영향\n설비 손상\n감전 위험\n시스템 불안정\n보호 장치 작동' },
      { key: 'capacitor', label: 'Capacitor', label_ko: '캐패시터', description: 'Electrical component that stores charge and compensates for reactive power\nCauses\nBulging\nLeakage\nDielectric failure\nOverheating\nEffects\nReduced power factor\nIncreased power losses\nSystem instability\nEquipment failure', description_ko: '전하를 저장하고 무효 전력을 보상하는 전기 부품\n원인\n팽창\n누설\n유전체 고장\n과열\n영향\n역률 저하\n전력 손실 증가\n시스템 불안정\n설비 고장' },
      { key: 'tapChanger', label: 'Tap Changer', label_ko: '탭 체인저', description: 'Device that changes the winding ratio of a transformer to adjust voltage\nCauses\nContact wear (pitting, burning, or excessive wear)\nCarbon buildup (from arcing)\nMechanical misalignment\nOil contamination\nEffects\nVoltage regulation problems\nContact failure\nTransformer damage\nSystem instability', description_ko: '변압기의 권선 비를 변경하여 전압을 조정하는 장치\n원인\n접점 마모(피팅, 소손, 과도한 마모)\n탄소 축적(아크 발생)\n기계적 정렬 불량\n오일 오염\n영향\n전압 조정 문제\n접점 고장\n변압기 손상\n시스템 불안정' },
      { key: 'bushings', label: 'Bushings', label_ko: '부싱', description: 'Component that insulates and supports high-voltage conductors in transformers\nCauses\nOil leakage\nCracks\nContamination\nAging\nEffects\nInsulation breakdown\nElectrical discharge\nTransformer failure\nSafety hazards', description_ko: '변압기의 고전압 도체를 절연하고 지지하는 부품\n원인\n오일 누출\n균열\n오염\n노화\n영향\n절연 파괴\n전기적 방전\n변압기 고장\n안전 위험' },
      { key: 'stress', label: 'Stress', label_ko: '스트레스', description: 'Electrical, thermal, and mechanical loads applied to equipment or components\nCauses\nOvervoltage\nOverload\nHarmonics\nTemperature rise\nEffects\nInsulation degradation\nReduced component lifespan\nIncreased failure risk\nPerformance degradation', description_ko: '설비나 부품에 가해지는 전기적, 열적, 기계적 부하\n원인\n과전압\n과부하\n고조파\n온도 상승\n영향\n절연 열화\n부품 수명 단축\n고장 위험 증가\n성능 저하' },
      { key: 'loadUnbalance', label: 'Load Unbalance', label_ko: '부하 불평형', description: 'State where loads on each phase in a three-phase system are not equal\nCauses\nExcessive single-phase load\nUnbalanced load distribution\nPhase connection errors\nEffects\nInter-phase voltage/current imbalance\nNegative sequence current\nIncreased heating\nReduced efficiency', description_ko: '3상 시스템에서 각 상에 걸리는 부하가 균등하지 않은 상태\n원인\n단상 부하 과다\n부하 분산 불균형\n위상 연결 오류\n영향\n상간 전압·전류 불균형\n역상 전류 발생\n가열 증가\n효율 저하' },
      { key: 'cableConnection', label: 'Cable Connection', label_ko: '케이블 연결', description: 'Component that transmits power or signals through electrical connections\nCauses\nLoose terminals\nCorrosion, oxidation\nOverheating (discoloration)\nPhysical damage\nEffects\nHigh resistance\nVoltage drop\nLocalized heating\nArcing', description_ko: '전기적 연결을 통해 전력이나 신호를 전달하는 부품\n원인\n단자 느슨함\n부식·산화\n과열(변색)\n물리적 손상\n영향\n고저항\n전압 강하\n국부 가열\n아크 발생' },
      { key: 'winding', label: 'Winding', label_ko: '권선', description: 'Coil windings in a transformer that create magnetic fields and transfer energy\nCauses\nInsulation breakdown (reduced insulation resistance)\nShorted turns (causing increased losses and heating)\nOverheating (discoloration or thermal damage)\nPhysical damage\nContamination\nEffects\nComplete transformer failure\nSystem outages\nSignificant damage\nReduced transformer efficiency', description_ko: '변압기에서 자기장을 생성하고 에너지를 전달하는 권선\n원인\n절연 파괴(절연 저항 감소)\n단락 권선(손실 및 가열 증가)\n과열(변색 또는 열 손상)\n물리적 손상\n오염\n영향\n변압기 완전 고장\n시스템 정전\n상당한 손상\n변압기 효율 저하' },
      { key: 'noiseVibration', label: 'Noise/Vibration', label_ko: '소음/진동', description: 'Important indicator of mechanical condition of equipment\nCauses\nBearing wear\nRotor imbalance\nMisalignment\nLoose components\nEffects\nAccelerated wear\nFatigue failure\nPotential for serious failure\nDeterioration of working environment', description_ko: '설비의 기계적 상태를 나타내는 중요한 지표\n원인\n베어링 마모\n회전자 불균형\n정렬 불량\n부품 느슨함\n영향\n마모 가속화\n피로 파괴\n심각한 고장으로 발전 가능\n작업 환경 악화' },
      { key: 'heat', label: 'Heat', label_ko: '열', description: 'Temperature rise caused by electrical losses or mechanical friction during equipment operation\nCauses\nIncreased harmonic stress\nAdditional losses in conductors, transformers, and motors\nInsufficient cooling\nOverload\nEffects\nInsulation degradation\nReduced equipment lifespan\nThermal expansion issues\nReduced efficiency', description_ko: '설비 작동 중 전기적 손실이나 기계적 마찰로 인해 발생하는 온도 상승\n원인\n고조파 스트레스 증가\n도체·변압기·모터에서 추가 손실\n냉각 부족\n과부하\n영향\n절연 열화\n설비 수명 단축\n열팽창 문제\n효율 저하' },
      { key: 'incomingVoltage', label: 'Incoming Voltage', label_ko: '입력 전압', description: 'Electrical potential difference supplied to equipment, a fundamental condition for normal equipment operation\nCauses\nUnstable power supply\nTransformer tap setting errors\nUnbalanced load distribution\nVoltage regulation equipment failure\nEffects\nEquipment malfunction\nOverheating\nReduced efficiency\nPremature failure', description_ko: '설비에 공급되는 전기적 전위차로, 설비의 정상 작동을 위한 기본 조건\n원인\n공급 전원 불안정\n변압기 탭 설정 오류\n부하 분산 불균형\n전압 조정 장치 고장\n영향\n설비 오작동\n과열\n효율 저하\n조기 고장' },
    ]
  },
  {
    key: 'primaryTransformer',
    label: 'Primary Transformer',
    items: [
      { key: 'capacitor', label: 'Capacitor', label_ko: '캐패시터', description: 'Electrical component that stores charge and compensates for reactive power\nCauses\nBulging\nLeakage\nDielectric failure\nOverheating\nEffects\nReduced power factor\nIncreased power losses\nSystem instability\nEquipment failure', description_ko: '전하를 저장하고 무효 전력을 보상하는 전기 부품\n원인\n팽창\n누설\n유전체 고장\n과열\n영향\n역률 저하\n전력 손실 증가\n시스템 불안정\n설비 고장' },
      { key: 'tapChanger', label: 'Tap Changer', label_ko: '탭 체인저', description: 'Device that changes the winding ratio of a transformer to adjust voltage\nCauses\nContact wear (pitting, burning, or excessive wear)\nCarbon buildup (from arcing)\nMechanical misalignment\nOil contamination\nEffects\nVoltage regulation problems\nContact failure\nTransformer damage\nSystem instability', description_ko: '변압기의 권선 비를 변경하여 전압을 조정하는 장치\n원인\n접점 마모(피팅, 소손, 과도한 마모)\n탄소 축적(아크 발생)\n기계적 정렬 불량\n오일 오염\n영향\n전압 조정 문제\n접점 고장\n변압기 손상\n시스템 불안정' },
      { key: 'bushings', label: 'Bushings', label_ko: '부싱', description: 'Component that insulates and supports high-voltage conductors in transformers\nCauses\nOil leakage\nCracks\nContamination\nAging\nEffects\nInsulation breakdown\nElectrical discharge\nTransformer failure\nSafety hazards', description_ko: '변압기의 고전압 도체를 절연하고 지지하는 부품\n원인\n오일 누출\n균열\n오염\n노화\n영향\n절연 파괴\n전기적 방전\n변압기 고장\n안전 위험' },
      { key: 'stress', label: 'Stress', label_ko: '스트레스', description: 'Electrical, thermal, and mechanical loads applied to equipment or components\nCauses\nOvervoltage\nOverload\nHarmonics\nTemperature rise\nEffects\nInsulation degradation\nReduced component lifespan\nIncreased failure risk\nPerformance degradation', description_ko: '설비나 부품에 가해지는 전기적, 열적, 기계적 부하\n원인\n과전압\n과부하\n고조파\n온도 상승\n영향\n절연 열화\n부품 수명 단축\n고장 위험 증가\n성능 저하' },
      { key: 'loadUnbalance', label: 'Load Unbalance', label_ko: '부하 불평형', description: 'State where loads on each phase in a three-phase system are not equal\nCauses\nExcessive single-phase load\nUnbalanced load distribution\nPhase connection errors\nEffects\nInter-phase voltage/current imbalance\nNegative sequence current\nIncreased heating\nReduced efficiency', description_ko: '3상 시스템에서 각 상에 걸리는 부하가 균등하지 않은 상태\n원인\n단상 부하 과다\n부하 분산 불균형\n위상 연결 오류\n영향\n상간 전압·전류 불균형\n역상 전류 발생\n가열 증가\n효율 저하' },
      { key: 'cableConnection', label: 'Cable Connection', label_ko: '케이블 연결', description: 'Component that transmits power or signals through electrical connections\nCauses\nLoose terminals\nCorrosion, oxidation\nOverheating (discoloration)\nPhysical damage\nEffects\nHigh resistance\nVoltage drop\nLocalized heating\nArcing', description_ko: '전기적 연결을 통해 전력이나 신호를 전달하는 부품\n원인\n단자 느슨함\n부식·산화\n과열(변색)\n물리적 손상\n영향\n고저항\n전압 강하\n국부 가열\n아크 발생' },
      { key: 'winding', label: 'Winding', label_ko: '권선', description: 'Coil windings in a transformer that create magnetic fields and transfer energy\nCauses\nInsulation breakdown (reduced insulation resistance)\nShorted turns (causing increased losses and heating)\nOverheating (discoloration or thermal damage)\nPhysical damage\nContamination\nEffects\nComplete transformer failure\nSystem outages\nSignificant damage\nReduced transformer efficiency', description_ko: '변압기에서 자기장을 생성하고 에너지를 전달하는 권선\n원인\n절연 파괴(절연 저항 감소)\n단락 권선(손실 및 가열 증가)\n과열(변색 또는 열 손상)\n물리적 손상\n오염\n영향\n변압기 완전 고장\n시스템 정전\n상당한 손상\n변압기 효율 저하' },
      { key: 'noiseVibration', label: 'Noise/Vibration', label_ko: '소음/진동', description: 'Important indicator of mechanical condition of equipment\nCauses\nBearing wear\nRotor imbalance\nMisalignment\nLoose components\nEffects\nAccelerated wear\nFatigue failure\nPotential for serious failure\nDeterioration of working environment', description_ko: '설비의 기계적 상태를 나타내는 중요한 지표\n원인\n베어링 마모\n회전자 불균형\n정렬 불량\n부품 느슨함\n영향\n마모 가속화\n피로 파괴\n심각한 고장으로 발전 가능\n작업 환경 악화' },
      { key: 'heat', label: 'Heat', label_ko: '열', description: 'Temperature rise caused by electrical losses or mechanical friction during equipment operation\nCauses\nIncreased harmonic stress\nAdditional losses in conductors, transformers, and motors\nInsufficient cooling\nOverload\nEffects\nInsulation degradation\nReduced equipment lifespan\nThermal expansion issues\nReduced efficiency', description_ko: '설비 작동 중 전기적 손실이나 기계적 마찰로 인해 발생하는 온도 상승\n원인\n고조파 스트레스 증가\n도체·변압기·모터에서 추가 손실\n냉각 부족\n과부하\n영향\n절연 열화\n설비 수명 단축\n열팽창 문제\n효율 저하' },
      { key: 'incomingVoltage', label: 'Incoming Voltage', label_ko: '입력 전압', description: 'Electrical potential difference supplied to equipment, a fundamental condition for normal equipment operation\nCauses\nUnstable power supply\nTransformer tap setting errors\nUnbalanced load distribution\nVoltage regulation equipment failure\nEffects\nEquipment malfunction\nOverheating\nReduced efficiency\nPremature failure', description_ko: '설비에 공급되는 전기적 전위차로, 설비의 정상 작동을 위한 기본 조건\n원인\n공급 전원 불안정\n변압기 탭 설정 오류\n부하 분산 불균형\n전압 조정 장치 고장\n영향\n설비 오작동\n과열\n효율 저하\n조기 고장' },
    ]
  },
]

export const pqData = [
  { key: 'voltageRMS', label: 'Voltage RMS', label_ko: '전압 RMS', description: 'Measurement value representing the effective value of AC voltage\nCauses\nUnstable power supply\nTransformer tap setting errors\nUnbalanced load distribution\nVoltage regulation equipment failure\nEffects\nEquipment malfunction\nOverheating\nReduced efficiency\nPremature failure', description_ko: '교류 전압의 유효 값을 나타내는 측정값\n원인\n공급 전원 불안정\n변압기 탭 설정 오류\n부하 분산 불균형\n전압 조정 장치 고장\n영향\n설비 오작동\n과열\n효율 저하\n조기 고장' },
  { key: 'voltagePhaseAngle', label: 'Voltage Phase Angle', label_ko: '전압 위상', description: 'Phase difference between voltage waveforms of each phase in a three-phase system\nCauses\nPhase unbalance\nSynchronization problems\nPhase sequence errors\nUnbalanced load distribution\nEffects\nUnbalance\nIncreased losses\nMotor heating\nEquipment malfunction', description_ko: '3상 시스템에서 각 상의 전압 파형 간 위상 차이\n원인\n위상 불균형\n동기화 문제\n위상 순서 오류\n부하 분산 불균형\n영향\n불균형\n손실 증가\n모터 가열\n설비 오작동' },
  { key: 'currentRMS', label: 'Current RMS', label_ko: '전류', description: 'Measurement value representing the effective value of AC current\nCauses\nOverload\nShort circuit\nGround fault\nEquipment malfunction\nEffects\nOverheating\nEquipment damage\nInsulation breakdown\nSafety hazards', description_ko: '교류 전류의 유효 값을 나타내는 측정값\n원인\n과부하\n단락\n지락\n설비 오작동\n영향\n과열\n설비 손상\n절연 파괴\n안전 위험' },
  { key: 'currentPhaseAngle', label: 'Current Phase Angle', label_ko: '전류 위상', description: 'Phase difference between current waveforms of each phase in a three-phase system\nCauses\nPhase unbalance\nLoad distribution problems\nSynchronization problems\nPhase sequence errors\nEffects\nNegative sequence current\nIncreased heating\nReduced efficiency\nMotor torque pulsation', description_ko: '3상 시스템에서 각 상의 전류 파형 간 위상 차이\n원인\n위상 불균형\n부하 분산 문제\n동기화 문제\n위상 순서 오류\n영향\n역상 전류\n가열 증가\n효율 저하\n모터 토크 맥동' },
  { key: 'crestFactor', label: 'Crest Factor', label_ko: '크레스트 팩터', description: 'Indicator representing waveform shape as the ratio of peak value to RMS value\nCauses\nWaveform distortion\nHarmonic content\nNon-linear loads\nEffects\nEquipment stress\nIncreased losses\nOverheating\nReduced efficiency', description_ko: '피크 값 대 RMS 값의 비율로 파형의 형태를 나타내는 지표\n원인\n파형 왜곡\n고조파 함량\n비선형 부하\n영향\n설비 스트레스\n손실 증가\n과열\n효율 저하' },
  { key: 'unbalance', label: 'Unbalance', label_ko: '불균형', description: 'State where voltage or current across the three phases is not equal in a three-phase system\nCauses\nExcessive single-phase load\nUnbalanced load distribution\nPhase connection errors\nEffects\nNegative sequence current\nIncreased heating in motors and transformers\nReduced efficiency\nTorque pulsation', description_ko: '3상 시스템에서 각 상의 전압이나 전류가 균등하지 않은 상태\n원인\n단상 부하 과다\n부하 분산 불균형\n위상 연결 오류\n영향\n역상 전류\n모터·변압기 가열 증가\n효율 저하\n토크 맥동' },
  { key: 'harmonics', label: 'Harmonics', label_ko: '고조파', description: 'Current/voltage components that are integer multiples of the fundamental frequency, caused by non-linear loads\nCauses\nNon-linear loads (VFDs, rectifiers, electronic loads)\nPoor harmonic filtering equipment\nPoor grounding\nEffects\nOverheating\nIncreased losses\nEquipment malfunction\nCommunication interference\nPremature failure', description_ko: '기본 주파수의 정수 배 주파수로, 비선형 부하에서 발생하는 전류/전압 성분\n원인\n비선형 부하(VFD, 정류기, 전자 부하)\n고조파 필터링 장비 불량\n접지 불량\n영향\n과열\n손실 증가\n설비 오작동\n통신 간섭\n조기 고장' },
  { key: 'zeroSequence', label: 'Zero Sequence', label_ko: '영상분', description: 'Current or voltage components with the same magnitude and phase in all three phases\nCauses\nGround fault\nInsulation failure\nUnbalanced conditions\nGrounding system problems\nPoor neutral conductor sizing or connections\nEffects\nOverheating\nTransformer heating\nSafety hazards\nNeutral conductor overload', description_ko: '세 상 모두에서 동일한 크기와 위상을 가진 전류나 전압 성분\n원인\n지락\n절연 파괴\n불균형 조건\n접지 시스템 문제\n중성선 크기 또는 연결 불량\n영향\n과열\n변압기 가열\n안전 위험\n중성선 과부하' },
  { key: 'negativeSequence', label: 'Negative Sequence', label_ko: '역상분', description: 'Current/voltage components indicating phase unbalance or phase sequence reversal\nCauses\nPhase unbalance\nPhase sequence reversal (ACB)\nUnbalanced load distribution\nPhase connection errors\nEffects\nIncreased heating\nReduced efficiency\nTorque pulsation\nReverse rotating magnetic fields in motors and transformers', description_ko: '위상 불균형이나 위상 순서 반전을 나타내는 전류/전압 성분\n원인\n위상 불균형\n위상 순서 반전(ACB)\n부하 분산 불균형\n위상 연결 오류\n영향\n가열 증가\n효율 저하\n토크 맥동\n모터·변압기 역회전 자기장' },
  { key: 'phaseAngle', label: 'Phase Angle', label_ko: '위상각', description: 'Indicator representing power factor as the angular difference between voltage and current waveforms\nCauses\nPoor power factor\nReactive power issues\nVoltage-current phase relationship problems\nExcessive inductive loads\nPoor power factor correction equipment\nEffects\nIncreased losses\nReduced system capacity\nHigher utility costs\nIncreased reactive power consumption', description_ko: '전압과 전류 파형 간의 각도 차이로 역률을 나타내는 지표\n원인\n역률 저하\n무효 전력 문제\n전압·전류 위상 관계 문제\n과도한 유도 부하\n역률 개선 장치 불량\n영향\n손실 증가\n시스템 용량 감소\n높은 전기 요금\n무효 전력 소비 증가' },
  { key: 'powerFactor', label: 'Power Factor', label_ko: '역률', description: 'Indicator representing energy efficiency as the ratio of active power to apparent power\nCauses\nExcessive inductive loads\nPoor power factor correction equipment\nPoor capacitor bank operation\nIncreased reactive power consumption\nEffects\nIncreased line losses\nReduced system capacity\nVoltage drops\nHigher utility costs\nInefficient energy use', description_ko: '유효 전력과 피상 전력의 비율로, 에너지 효율을 나타내는 지표\n원인\n과도한 유도 부하\n역률 개선 장치 불량\n커패시터 뱅크 작동 불량\n무효 전력 소비 증가\n영향\n선로 손실 증가\n시스템 용량 감소\n전압 강하\n높은 전기 요금\n비효율적 에너지 사용' },
  { key: 'totalDemandDistortion', label: 'Total Demand Distortion (TDD)', label_ko: 'TDD', description: 'Indicator representing the ratio of harmonic distortion relative to the maximum demand load\nCauses\nHarmonic sources\nPoor harmonic filtering equipment\nResonance conditions\nAbsence or inadequacy of harmonic mitigation equipment\nEffects\nEquipment overheating\nInterference\nIncreased losses\nSystem instability', description_ko: '최대 수요 부하 대비 고조파 왜곡의 비율을 나타내는 지표\n원인\n고조파 발생원\n고조파 필터링 장비 불량\n공진 조건\n고조파 완화 장비 부재 또는 부적절\n영향\n설비 과열\n간섭\n손실 증가\n시스템 불안정' },
  { key: 'power', label: 'Power', label_ko: '전력', description: 'Energy consumed per unit time, divided into active power and reactive power\nCauses\nInefficient operation\nEquipment malfunction\nOverload conditions\nLoad imbalance\nEffects\nIncreased energy consumption\nIncreased costs\nReduced equipment lifespan\nIncreased system load', description_ko: '단위 시간당 소비되는 에너지로, 유효 전력과 무효 전력으로 구분\n원인\n비효율적 운전\n설비 오작동\n과부하 조건\n부하 불균형\n영향\n에너지 소비 증가\n비용 증가\n설비 수명 단축\n시스템 부하 증가' },
  { key: 'dc', label: 'DC', label_ko: 'DC 전압', description: 'DC component mixed into AC systems\nCauses\nRectification problems\nTransformer saturation\nGround fault problems\nPower supply circuit problems\nEffects\nTransformer core saturation\nIncreased losses\nOverheating\nEquipment malfunction', description_ko: '교류 시스템에 혼입된 직류 성분\n원인\n정류 문제\n변압기 포화\n지락 문제\n전원 공급 회로 문제\n영향\n변압기 코어 포화\n손실 증가\n과열\n설비 오작동' },
  { key: 'events', label: 'Events', label_ko: '이벤트', description: 'Power quality abnormalities including voltage sags, swells, interruptions, transients, etc.\nCauses\nLightning\nSwitching operations\nFaults\nProtective device operation\nEffects\nEquipment malfunction\nData loss\nProcess interruptions\nEquipment damage', description_ko: '전력 품질 이상 현상으로 전압 강하, 상승, 순간 정전, 과도현상 등을 포함\n원인\n낙뢰\n스위칭 작동\n고장\n보호 장치 작동\n영향\n설비 오작동\n데이터 손실\n공정 중단\n설비 손상' },
]

export const faultData = [
  { key: 'phaseOrder', label: 'Phase Order', label_ko: '상순서', description: 'Sequence in which voltage of each phase occurs in a three-phase system\nCauses\nPhase connection errors\nReversed phase sequence (ACB)\nWiring errors\nEffects\nMotor reverse rotation\nEquipment malfunction\nSystem instability', description_ko: '3상 시스템에서 각 상의 전압이 발생하는 순서\n원인\n위상 연결 오류\n역상 순서(ACB)\n배선 오류\n영향\n모터 역방향 회전\n설비 오작동\n시스템 불안정' },
  { key: 'noLoad', label: 'No Load', label_ko: '무부하', description: 'State where equipment is not consuming significant current or power\nCauses\nDisconnected loads\nEquipment failure\nOpen circuits\nMeasurement issues\nOpen circuit breakers or switches\nEffects\nAbnormal equipment operation\nProcess interruption\nUnable to measure\nSystem abnormalities', description_ko: '설비가 상당한 전류나 전력을 소비하지 않는 상태\n원인\n부하 연결 해제\n설비 고장\n개방 회로\n측정 문제\n차단기 또는 스위치 개방\n영향\n설비 비정상 작동\n공정 중단\n측정 불가\n시스템 이상' },
  { key: 'overCurrent', label: 'Over Current', label_ko: '과전류', description: 'Current state exceeding rated values\nCauses\nOverload\nShort circuit\nGround fault\nEquipment malfunction\nMotor starting inrush current\nEffects\nEquipment damage\nInsulation breakdown\nOverheating\nSafety hazards', description_ko: '정격값을 초과하는 전류 상태\n원인\n과부하\n단락\n지락\n설비 오작동\n모터 기동 과도 전류\n영향\n설비 손상\n절연 파괴\n과열\n안전 위험' },
  { key: 'cf', label: 'CF (Crest Factor)', label_ko: '파고율', description: 'Indicator representing waveform shape as the ratio of peak value to RMS value\nCauses\nHarmonic distortion\nNon-linear loads\nWaveform anomalies\nEffects\nEquipment stress\nIncreased losses\nOverheating\nReduced efficiency', description_ko: '피크 값 대 RMS 값의 비율로 파형 형태를 나타내는 지표\n원인\n고조파 왜곡\n비선형 부하\n파형 이상\n영향\n설비 스트레스\n손실 증가\n과열\n효율 저하' },
  { key: 'noPower', label: 'No Power', label_ko: '무전원', description: 'State where power supply is completely cut off\nCauses\nPower outages\nCircuit breaker trips\nFuse failures\nEquipment failures\nDisconnected power sources\nEffects\nEquipment shutdown\nProcess interruption\nData loss\nOperational shutdown', description_ko: '전원 공급이 완전히 차단된 상태\n원인\n정전\n차단기 트립\n퓨즈 고장\n설비 고장\n전원 연결 해제\n영향\n설비 중단\n공정 중단\n데이터 손실\n운영 중단' },
  { key: 'overVoltage', label: 'Over Voltage', label_ko: '과전압', description: 'Voltage state exceeding rated values (typically >110%)\nCauses\nUtility voltage regulation issues\nTransformer tap setting errors\nLoad rejection\nSystem faults\nPoor voltage regulation equipment\nEffects\nEquipment damage\nInsulation breakdown\nOverheating\nPremature component failure\nSafety hazards', description_ko: '정격값(일반적으로 >110%)을 초과하는 전압 상태\n원인\n공급 전원 전압 조정 문제\n변압기 탭 설정 오류\n부하 제거\n시스템 고장\n전압 조정 장치 불량\n영향\n설비 손상\n절연 파괴\n과열\n부품 조기 고장\n안전 위험' },
  { key: 'underVoltage', label: 'Under Voltage', label_ko: '저전압', description: 'Voltage state below rated values (typically <90%)\nCauses\nUtility voltage drops\nHigh line impedance\nOverload conditions\nTransformer tap setting errors\nEffects\nEquipment malfunction\nReduced efficiency\nMotor overheating\nPoor performance\nEquipment failure', description_ko: '정격값(일반적으로 <90%) 미만의 전압 상태\n원인\n공급 전원 전압 강하\n높은 선로 임피던스\n과부하 조건\n변압기 탭 설정 오류\n영향\n설비 오작동\n효율 저하\n모터 과열\n성능 저하\n설비 고장' },
  { key: 'lowFrequency', label: 'Low Frequency', label_ko: '저주파수', description: 'Frequency state below rated values (60Hz systems <59Hz, 50Hz systems <49Hz)\nCauses\nUtility generation problems\nSystem overload\nGrid instability\nGenerator operation problems\nEffects\nMotor speed reduction\nGenerator problems\nEquipment malfunction\nSystem instability', description_ko: '정격값(60Hz 시스템 <59Hz, 50Hz 시스템 <49Hz) 미만의 주파수 상태\n원인\n공급 전원 발전 문제\n시스템 과부하\n전력망 불안정\n발전기 작동 문제\n영향\n모터 속도 감소\n발전기 문제\n설비 오작동\n시스템 불안정' },
  { key: 'vf', label: 'VF (Voltage/Frequency)', label_ko: 'V/F', description: 'Proportional relationship between voltage and frequency\nCauses\nVoltage regulation problems\nFrequency regulation problems\nSystem instability\nPoor voltage/frequency regulation equipment\nEffects\nMotor performance issues\nEquipment malfunction\nOverheating\nReduced efficiency', description_ko: '전압과 주파수의 비례 관계\n원인\n전압 조정 문제\n주파수 조정 문제\n시스템 불안정\n전압·주파수 조정 장치 불량\n영향\n모터 성능 문제\n설비 오작동\n과열\n효율 저하' },
]

export const eventData = [
  { key: 'transientCurrentEvent', label: 'Transient Current Event', label_ko: '과도 전류 이벤트', description: 'Momentary current surge phenomenon\nCauses\nMotor starting inrush current\nCapacitor switching\nLoad switching\nFault clearing\nEffects\nEquipment stress\nProtective device operation\nSystem disturbances', description_ko: '순간적인 전류 급변 현상\n원인\n모터 기동 과도 전류\n콘덴서 스위칭\n부하 스위칭\n고장 제거\n영향\n설비 스트레스\n보호 장치 작동\n시스템 교란' },
  { key: 'overCurrentEvent', label: 'Over Current Event', label_ko: '과전류 이벤트', description: 'Event triggered by current exceeding preset threshold values\nCauses\nOverload conditions\nShort circuits\nGround faults\nEquipment malfunction\nMotor starting inrush current\nEffects\nEquipment damage\nProtective device operation (breakers, fuses)\nSystem interruptions', description_ko: '설정 임계값을 초과하는 전류로 발생하는 이벤트\n원인\n과부하 조건\n단락\n지락\n설비 오작동\n모터 기동 과도 전류\n영향\n설비 손상\n보호 장치 작동(차단기, 퓨즈)\n시스템 중단' },
  { key: 'underCurrentEvent', label: 'Under Current Event', label_ko: '저전류 이벤트', description: 'Event triggered by current dropping below preset threshold values\nCauses\nLoad loss\nEquipment failure\nOpen circuits\nDisconnected loads\nMeasurement issues\nEffects\nEquipment operation problems\nProcess interruptions\nSystem abnormalities', description_ko: '설정 임계값 미만의 전류로 발생하는 이벤트\n원인\n부하 손실\n설비 고장\n개방 회로\n부하 연결 해제\n측정 문제\n영향\n설비 작동 문제\n공정 중단\n시스템 이상' },
  { key: 'sagEvent', label: 'Sag Event', label_ko: '순간전압강하 이벤트', description: 'Phenomenon where RMS voltage temporarily decreases (typically 10-90% of nominal) lasting from milliseconds to seconds\nCauses\nStarting large motors\nUtility faults\nLoad switching\nRemote faults on power system\nEffects\nEquipment malfunction\nProcess interruptions\nContactor dropouts\nData loss', description_ko: 'RMS 전압이 일시적으로 감소(일반적으로 정격의 10-90%)하는 현상으로 밀리초에서 수초 동안 지속\n원인\n대형 모터 기동\n공급 전원 고장\n부하 스위칭\n전력 시스템 원격 고장\n영향\n설비 오작동\n공정 중단\n접촉기 드롭아웃\n데이터 손실' },
  { key: 'swellEvent', label: 'Swell Event', label_ko: '순간전압상승 이벤트', description: 'Phenomenon where RMS voltage temporarily increases (typically 110-180% of nominal) lasting from milliseconds to seconds\nCauses\nLoad rejection\nCapacitor switching\nUtility voltage regulation issues\nSystem faults\nEffects\nEquipment damage\nInsulation stress\nPremature component failure\nEquipment malfunction', description_ko: 'RMS 전압이 일시적으로 증가(일반적으로 정격의 110-180%)하는 현상으로 밀리초에서 수초 동안 지속\n원인\n부하 제거\n콘덴서 스위칭\n공급 전원 전압 조정 문제\n시스템 고장\n영향\n설비 손상\n절연 스트레스\n부품 조기 고장\n설비 오작동' },
  { key: 'interruptionEvent', label: 'Interruption Event', label_ko: '순간정전 이벤트', description: 'Complete loss of voltage (typically <10% of nominal) occurring momentarily, temporarily, or sustained\nCauses\nUtility faults\nEquipment failures\nProtective device operations\nPlanned outages\nEffects\nEquipment shutdown\nProcess losses\nData loss\nSignificant operational impacts', description_ko: '전압의 완전한 손실(일반적으로 정격의 <10%)로 순간적, 일시적, 지속적으로 발생\n원인\n공급 전원 고장\n설비 고장\n보호 장치 작동\n계획된 정전\n영향\n설비 중단\n공정 손실\n데이터 손실\n중요한 운영 영향' },
  { key: 'transientVoltageEvent', label: 'Transient Voltage Event', label_ko: '과도 전압 이벤트', description: 'Very brief but significant voltage increase (often several times nominal voltage) lasting microseconds to milliseconds\nCauses\nLightning strikes\nCapacitor switching\nInductive load switching\nElectrostatic discharge\nEffects\nEquipment damage\nInsulation breakdown\nComponent failure\nData corruption', description_ko: '매우 짧지만 상당한 전압 증가(종종 정격의 여러 배)로 마이크로초에서 밀리초 동안 지속\n원인\n낙뢰\n콘덴서 스위칭\n유도 부하 스위칭\n정전기 방전\n영향\n설비 손상\n절연 파괴\n부품 고장\n데이터 손상' },
]

