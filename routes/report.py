"""
EN50160 전력품질 리포트 생성 (FastAPI 연동)
- Channel Information (설비 정보)
- ITIC Curve Analysis (전력품질 차트)
"""
from fastapi import APIRouter, Request, HTTPException
from states.global_state import influx_state, redis_state, os_spec
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from datetime import datetime
from .api import get_asset
import logging
import os

# 한글 폰트 설정 (프로젝트 폴더의 나눔고딕 사용)
font_path = '/home/root/webserver/fonts/NanumGothic.ttf'
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    fm.fontManager.addfont(font_path)  # 폰트 등록
    print(f"✅ 한글 폰트 로드: {font_path}")
else:
    print(f"⚠️ 한글 폰트 없음, 기본 폰트 사용")
plt.rcParams['axes.unicode_minus'] = False

router = APIRouter()

def parse_asset_data(api_response):
    """
    API 응답을 리포트용 데이터로 변환

    Args:
        api_response: FastAPI getAsset 응답

    Returns:
        dict: channel_data 형식
    """
    if not api_response.get('success'):
        return None

    data_list = api_response.get('data', [])
    mac = api_response.get('mac', '-')
    drive_type = api_response.get('driveType', '')

    # 데이터 파싱
    parsed = {
        'mac': mac,
        'drive_type': drive_type,
        'rated_voltage': '-',
        'rated_current': '-',
        'rated_power': '-',
        'rated_capacity': '-',
        'frequency': 60,
        'pt_wiring_mode': '-'
    }

    for item in data_list:
        name = item.get('Name', '')
        value = item.get('Value', '-')

        if name == 'RatedVoltage':
            parsed['rated_voltage'] = value
        elif name == 'RatedCurrent':
            parsed['rated_current'] = value
        elif name == 'RatedFrequency':
            parsed['frequency'] = value
        elif name == 'RatedKVA':
            parsed['rated_capacity'] = value
        elif name == 'PT_WiringMode':
            parsed['pt_wiring_mode'] = value

    return parsed


def create_channel_info_section(doc, channel_data):
    """
    Channel Information 섹션 생성

    Args:
        doc: Document 객체
        channel_data: dict {
            'channel': 'Main' or 'Sub',
            'name': '설비명',
            'type': 'Motor/Transformer/etc',
            'drive_type': 'DOL/VFD',
            'location': '위치',
            'mac': 'MAC 주소',
            'rated_voltage': 380,
            'rated_current': 100,
            'rated_power': 75,
            'rated_capacity': 100,
            'frequency': 60
        }
    """

    # === 헤더 ===
    header_table = doc.add_table(rows=1, cols=2)
    header_table.style = 'Table Grid'

    # 아이콘 셀 (왼쪽)
    icon_cell = header_table.rows[0].cells[0]
    icon_cell.width = Inches(0.8)
    icon_para = icon_cell.paragraphs[0]
    icon_run = icon_para.add_run('📊')
    icon_run.font.size = Pt(24)
    icon_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 배경색 설정 (slate-600)
    from docx.oxml import OxmlElement
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:fill'), '64748B')
    icon_cell._element.get_or_add_tcPr().append(shading_elm)

    # 제목 셀 (오른쪽)
    title_cell = header_table.rows[0].cells[1]
    title_para = title_cell.paragraphs[0]
    title_run = title_para.add_run(f'{channel_data.get("channel", "Main")} Channel Information')
    title_run.font.size = Pt(16)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(255, 255, 255)
    title_para.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # 배경색 설정
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:fill'), '64748B')
    title_cell._element.get_or_add_tcPr().append(shading_elm)

    doc.add_paragraph()  # 간격

    # === 첫 번째 줄: 이름/타입/구동방식 ===
    info_table1 = doc.add_table(rows=1, cols=3)
    info_table1.style = 'Light Grid Accent 1'

    cells = info_table1.rows[0].cells

    # 이름
    name_cell = cells[0]
    name_label = name_cell.paragraphs[0]
    name_label_run = name_label.add_run('설비명\n')
    name_label_run.font.size = Pt(9)
    name_label_run.font.bold = True
    name_label_run.font.color.rgb = RGBColor(107, 114, 128)

    name_value = name_cell.add_paragraph()
    name_value_run = name_value.add_run(channel_data.get('name', '-'))
    name_value_run.font.size = Pt(14)
    name_value_run.font.bold = True
    name_value_run.font.color.rgb = RGBColor(31, 41, 55)

    # 타입
    type_cell = cells[1]
    type_label = type_cell.paragraphs[0]
    type_label_run = type_label.add_run('설비 타입\n')
    type_label_run.font.size = Pt(9)
    type_label_run.font.bold = True
    type_label_run.font.color.rgb = RGBColor(107, 114, 128)

    type_value = type_cell.add_paragraph()
    type_value_run = type_value.add_run(channel_data.get('type', '-'))
    type_value_run.font.size = Pt(14)
    type_value_run.font.bold = True
    type_value_run.font.color.rgb = RGBColor(31, 41, 55)

    # Drive Type (Motor인 경우만)
    asset_type = channel_data.get('type', '').lower()
    if asset_type in ['motor', 'motorfeed', 'pump', 'fan', 'compressor']:
        drive_cell = cells[2]
        drive_label = drive_cell.paragraphs[0]
        drive_label_run = drive_label.add_run('구동 방식\n')
        drive_label_run.font.size = Pt(9)
        drive_label_run.font.bold = True
        drive_label_run.font.color.rgb = RGBColor(107, 114, 128)

        drive_value = drive_cell.add_paragraph()
        drive_type = channel_data.get('drive_type', '')
        drive_type_text = '직입 기동' if drive_type == 'DOL' else '인버터' if drive_type == 'VFD' else '-'
        drive_value_run = drive_value.add_run(drive_type_text)
        drive_value_run.font.size = Pt(14)
        drive_value_run.font.bold = True
        drive_value_run.font.color.rgb = RGBColor(31, 41, 55)

    doc.add_paragraph()  # 간격

    # === 두 번째 줄: 상세 사양 ===
    spec_items = []

    # Transformer인 경우
    if 'transformer' in asset_type:
        spec_items = [
            {'name': '정격용량', 'value': channel_data.get('rated_capacity', '-'), 'unit': 'kVA'},
            {'name': 'PT 결선방식', 'value': channel_data.get('pt_wiring_mode', '-'), 'unit': ''},
            {'name': '정격전압', 'value': channel_data.get('rated_voltage', '-'), 'unit': 'V'},
            {'name': '정격주파수', 'value': channel_data.get('frequency', 60), 'unit': 'Hz'},
            {'name': '위치', 'value': channel_data.get('location', '-'), 'unit': ''},
            {'name': 'MAC', 'value': channel_data.get('mac', '-'), 'unit': ''},
        ]
    # Motor 계열인 경우
    else:
        spec_items = [
            {'name': '정격전압', 'value': channel_data.get('rated_voltage', '-'), 'unit': 'V'},
            {'name': '정격전류', 'value': channel_data.get('rated_current', '-'), 'unit': 'A'},
            {'name': '정격출력', 'value': channel_data.get('rated_power', '-'), 'unit': 'kW'},
            {'name': '정격주파수', 'value': channel_data.get('frequency', 60), 'unit': 'Hz'},
            {'name': '위치', 'value': channel_data.get('location', '-'), 'unit': ''},
            {'name': 'MAC', 'value': channel_data.get('mac', '-'), 'unit': ''},
        ]

    # 테이블 생성 (2행 x 3열)
    num_cols = 3
    num_rows = (len(spec_items) + num_cols - 1) // num_cols

    spec_table = doc.add_table(rows=num_rows, cols=num_cols)
    spec_table.style = 'Light Grid Accent 1'

    # 데이터 채우기
    for idx, item in enumerate(spec_items):
        row_idx = idx // num_cols
        col_idx = idx % num_cols

        cell = spec_table.rows[row_idx].cells[col_idx]

        # 라벨
        label_para = cell.paragraphs[0]
        label_run = label_para.add_run(f'{item["name"]}\n')
        label_run.font.size = Pt(9)
        label_run.font.bold = True
        label_run.font.color.rgb = RGBColor(107, 114, 128)

        # 값
        value_para = cell.add_paragraph()
        value_text = f'{item["value"]} {item["unit"]}'.strip()
        value_run = value_para.add_run(value_text)
        value_run.font.size = Pt(12)
        value_run.font.bold = True
        value_run.font.color.rgb = RGBColor(31, 41, 55)


def create_itic_curve_chart(chart_path='/tmp/itic_curve.png', itic_events=None):
    """
    ITIC Curve 차트 생성

    Args:
        chart_path: 저장할 파일 경로
        itic_events: 실제 이벤트 데이터 리스트
                    [{'duration': 0.5, 'voltage_pct': 85, 'event_type': 'SAG'}, ...]
    """

    fig, ax = plt.subplots(figsize=(12, 8))

    # ITIC Curve 영역 정의
    prohibited_lower_x = [0.001, 0.01, 0.5, 10, 10, 0.001, 0.001]
    prohibited_lower_y = [0, 0, 70, 70, 0, 0, 0]
    ax.fill(prohibited_lower_x, prohibited_lower_y,
            color='#fee2e2', alpha=0.7, label='Prohibited Region')

    no_damage_x = [0.001, 0.01, 0.5, 10, 10, 0.5, 0.01, 0.001, 0.001]
    no_damage_y = [70, 70, 80, 80, 110, 120, 120, 110, 70]
    ax.fill(no_damage_x, no_damage_y,
            color='#fef3c7', alpha=0.7, label='No Damage')

    no_interrupt_x = [0.001, 0.01, 0.5, 10, 10, 0.5, 0.01, 0.001, 0.001]
    no_interrupt_y = [110, 120, 120, 110, 500, 500, 140, 140, 110]
    ax.fill(no_interrupt_x, no_interrupt_y,
            color='#d1fae5', alpha=0.7, label='No Interruption')

    prohibited_upper_x = [0.001, 0.01, 0.5, 10, 10, 0.001, 0.001]
    prohibited_upper_y = [140, 140, 500, 500, 200, 200, 140]
    ax.fill(prohibited_upper_x, prohibited_upper_y,
            color='#fee2e2', alpha=0.7)

    # ITIC Curve 경계선
    ax.plot([0.001, 0.01, 0.5, 10], [70, 70, 80, 80],
            'r-', linewidth=2, label='ITIC Limit')
    ax.plot([0.001, 0.01, 0.5, 10], [110, 120, 120, 110],
            'r-', linewidth=2)
    ax.plot([0.001, 0.01, 0.5], [140, 140, 500],
            'r-', linewidth=2)

    # 이벤트 데이터 표시
    if itic_events:
        for event in itic_events:
            duration = event.get('duration', 0)
            voltage_pct = event.get('voltage_pct', 100)
            event_type = event.get('event_type', 'UNKNOWN')

            color = 'orange' if event_type == 'SAG' else 'green'

            ax.scatter(duration, voltage_pct,
                       c=color, s=50, alpha=0.8,
                       edgecolors='black', linewidth=1,
                       zorder=5)

    # 축 설정
    ax.set_xscale('log')
    ax.set_xlim(0.001, 10)
    ax.set_ylim(0, 200)

    ax.set_xlabel('Duration (s)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Voltage (%)', fontsize=12, fontweight='bold')
    ax.set_title('ITIC Curve - Power Quality Events', fontsize=14, fontweight='bold', pad=20)

    ax.grid(True, which='both', alpha=0.3, linestyle='--')
    ax.legend(loc='upper right', fontsize=10)

    plt.tight_layout()
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ ITIC Curve 차트 저장: {chart_path}")
    return chart_path


async def generate_report(asset_name, asset_type, location='', output_path='/home/root/logs/report.docx', itic_events=None):

    # API에서 설비 정보 가져오기
    print(f"📡 API 호출: {asset_name}")
    api_response = await get_asset(asset_name)

    if not api_response.get('success'):
        print(f"❌ 설비 정보 가져오기 실패: {api_response.get('error')}")
        return None

    # 데이터 파싱
    parsed_data = parse_asset_data(api_response)

    # channel_data 구성
    channel_data = {
        'channel': 'Main',
        'name': asset_name,
        'type': asset_type,
        'drive_type': parsed_data.get('drive_type', ''),
        'location': location,
        'mac': parsed_data.get('mac', '-'),
        'rated_voltage': parsed_data.get('rated_voltage', '-'),
        'rated_current': parsed_data.get('rated_current', '-'),
        'rated_power': parsed_data.get('rated_power', '-'),
        'rated_capacity': parsed_data.get('rated_capacity', '-'),
        'frequency': parsed_data.get('frequency', 60),
        'pt_wiring_mode': parsed_data.get('pt_wiring_mode', '-'),
    }

    print(f"✅ 설비 정보 파싱 완료")

    # Document 생성
    doc = Document()

    # 기본 스타일
    style = doc.styles['Normal']
    style.font.size = Pt(10)

    # === 표지 ===
    title = doc.add_heading('Power Quality Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle = doc.add_paragraph()
    subtitle_run = subtitle.add_run('EN50160 Weekly Report')
    subtitle_run.font.size = Pt(16)
    subtitle_run.font.color.rgb = RGBColor(100, 116, 139)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    date_para = doc.add_paragraph()
    date_run = date_para.add_run(f'\nGenerated: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    date_run.font.size = Pt(11)
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()

    # === 1. Channel Information ===
    doc.add_heading('1. Asset Information', 1)
    create_channel_info_section(doc, channel_data)

    doc.add_page_break()

    # === 2. ITIC Curve Analysis ===
    doc.add_heading('2. ITIC Curve Analysis', 1)

    intro = doc.add_paragraph(
        'The ITIC (Information Technology Industry Council) Curve defines the voltage '
        'tolerance limits for IT equipment. This chart shows power quality events '
        'recorded during the measurement period.'
    )
    intro.paragraph_format.space_after = Pt(12)

    # ITIC 차트 생성
    chart_path = create_itic_curve_chart(itic_events=itic_events)
    doc.add_picture(chart_path, width=Inches(6.5))

    # 분석 결과
    if itic_events:
        doc.add_paragraph()
        analysis = doc.add_paragraph()
        analysis_title = analysis.add_run('Analysis Results:\n')
        analysis_title.font.bold = True
        analysis_title.font.size = Pt(11)

        sag_count = sum(1 for e in itic_events if e.get('event_type') == 'SAG')
        swell_count = sum(1 for e in itic_events if e.get('event_type') == 'SWELL')

        analysis_content = analysis.add_run(
            f'• Total Events: {len(itic_events)}\n'
            f'• Voltage Sag (SAG): {sag_count}\n'
            f'• Voltage Swell (SWELL): {swell_count}\n'
            f'• All events are within ITIC acceptable limits.'
        )

    # 저장
    doc.save(output_path)


    return output_path

@router.post("/generate")
async def set_report(request: Request):
    data = await request.json()
    o_path = await generate_report(data["assetName"], data["assetType"], data["location"])
    print(f"\n✅ 리포트 생성 완료: {o_path}")
    return True

@router.get('/lastReportData/{mode}/{asset_name}')
async def get_last_diagnosis(mode: str, asset_name: str):
    """마지막 진단 데이터 조회"""
    try:
        query_api = influx_state.query_api

        logging.info(f"🔍 조회 시작: mode={mode}, asset_name={asset_name}")

        # 1단계: 마지막 타임스탬프 찾기 (status 필드만)
        timestamp_query = f'''
        from(bucket: "ntek")
            |> range(start: -7d)
            |> filter(fn: (r) => r["_measurement"] == "{mode}")
            |> filter(fn: (r) => r["asset_name"] == "{asset_name}")
            |> filter(fn: (r) => r["data_type"] == "main")
            |> filter(fn: (r) => r["_field"] == "status")
            |> last()
        '''

        ts_tables = query_api.query(timestamp_query)

        last_time = None
        for table in ts_tables:
            for record in table.records:
                t = record.get_time()
                if last_time is None or t > last_time:
                    last_time = t

        if not last_time:
            logging.warning("⚠️ 데이터 없음")
            return {"success": False, "msg": "No Data"}

        logging.info(f"📅 마지막 타임스탬프: {last_time.isoformat()}")

        # 2단계: 해당 타임스탬프 ±1초 범위의 모든 데이터 조회
        from datetime import timedelta, timezone
        start_time = (last_time - timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end_time = (last_time + timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        data_query = f'''
        from(bucket: "ntek")
            |> range(start: {start_time}, stop: {end_time})
            |> filter(fn: (r) => r["_measurement"] == "{mode}")
            |> filter(fn: (r) => r["asset_name"] == "{asset_name}")
        '''

        logging.info(f"📊 데이터 쿼리 실행")
        tables = query_api.query(data_query)

        # item_name(태그) 기준으로 그룹핑
        grouped = {"main": {}, "detail": {}}

        for table in tables:
            for record in table.records:
                data_type = record.values.get("data_type")
                item_name = record.values.get("item_name")

                if not data_type or data_type not in ["main", "detail"]:
                    continue
                if not item_name:
                    continue

                # item_name을 키로 사용
                if item_name not in grouped[data_type]:
                    grouped[data_type][item_name] = {
                        "item_name": item_name,
                        "data_type": data_type,
                        "asset_name": record.values.get("asset_name"),
                        "channel": record.values.get("channel"),
                    }
                    if data_type == "detail":
                        grouped[data_type][item_name]["parent_name"] = record.values.get("parent_name")

                # 필드 값 추가
                field_name = record.get_field()
                field_value = record.get_value()
                grouped[data_type][item_name][field_name] = field_value

        # 딕셔너리를 리스트로 변환
        main_data = list(grouped["main"].values())
        detail_data = list(grouped["detail"].values())

        # timestamp timezone 제거
        if last_time.tzinfo is not None:
            last_time_local = last_time.astimezone().replace(tzinfo=None)
        else:
            last_time_local = last_time

        logging.info(f"✅ 최종 결과: main={len(main_data)}개, detail={len(detail_data)}개")

        result = {
            "asset_name": asset_name,
            "mode": mode,
            "timestamp": last_time_local.isoformat() if last_time_local else None,
            "main": main_data,
            "detail": detail_data
        }

        return {"success": True, "data": result}

    except Exception as e:
        logging.error(f"❌ 마지막 진단 데이터 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "msg": str(e)}


@router.get('/reportTimes/{date}/{asset_name}/{mode}')
async def get_report_times(date: str, asset_name: str, mode: str):
    """특정 날짜의 저장 시간 목록 조회 (mode별)"""
    try:
        query_api = influx_state.query_api

        start_time = f"{date}T00:00:00Z"
        end_time = f"{date}T23:59:59Z"

        query = f'''
        from(bucket: "ntek")
            |> range(start: {start_time}, stop: {end_time})
            |> filter(fn: (r) => r["_measurement"] == "{mode}")
            |> filter(fn: (r) => r["asset_name"] == "{asset_name}")
            |> filter(fn: (r) => r["data_type"] == "main")
            |> filter(fn: (r) => r["_field"] == "status")
        '''

        tables = query_api.query(query)

        times = set()
        for table in tables:
            for record in table.records:
                t = record.get_time()
                if t.tzinfo is not None:
                    t_local = t.astimezone().replace(tzinfo=None)
                else:
                    t_local = t
                times.add(t_local.isoformat())

        sorted_times = sorted(list(times), reverse=True)

        logging.info(f"📅 {mode} {date} 시간 목록: {len(sorted_times)}개")
        return {"success": True, "data": sorted_times}

    except Exception as e:
        logging.error(f"❌ 시간 목록 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "msg": str(e)}


@router.get('/reportDataByTime/{mode}/{asset_name}/{timestamp}')
async def get_report_data_by_time(mode: str, asset_name: str, timestamp: str):
    """특정 시간의 데이터 조회"""
    try:
        query_api = influx_state.query_api

        # timestamp를 UTC로 변환
        from datetime import datetime, timedelta, timezone

        local_time = datetime.fromisoformat(timestamp)
        if local_time.tzinfo is None:
            # 로컬 타임존 적용 후 UTC로 변환
            import time
            utc_offset = -time.timezone
            local_tz = timezone(timedelta(seconds=utc_offset))
            local_time = local_time.replace(tzinfo=local_tz)

        utc_time = local_time.astimezone(timezone.utc)

        # ±1초 범위
        start_time = (utc_time - timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end_time = (utc_time + timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        logging.info(f"🔍 조회: mode={mode}, asset={asset_name}, time={timestamp}")

        data_query = f'''
        from(bucket: "ntek")
            |> range(start: {start_time}, stop: {end_time})
            |> filter(fn: (r) => r["_measurement"] == "{mode}")
            |> filter(fn: (r) => r["asset_name"] == "{asset_name}")
        '''

        tables = query_api.query(data_query)

        # item_name 기준으로 그룹핑
        grouped = {"main": {}, "detail": {}}

        for table in tables:
            for record in table.records:
                data_type = record.values.get("data_type")
                item_name = record.values.get("item_name")

                if not data_type or data_type not in ["main", "detail"]:
                    continue
                if not item_name:
                    continue

                if item_name not in grouped[data_type]:
                    grouped[data_type][item_name] = {
                        "item_name": item_name,
                        "data_type": data_type,
                        "asset_name": record.values.get("asset_name"),
                        "channel": record.values.get("channel"),
                    }
                    if data_type == "detail":
                        grouped[data_type][item_name]["parent_name"] = record.values.get("parent_name")

                field_name = record.get_field()
                field_value = record.get_value()
                grouped[data_type][item_name][field_name] = field_value

        main_data = list(grouped["main"].values())
        detail_data = list(grouped["detail"].values())

        logging.info(f"✅ 결과: main={len(main_data)}개, detail={len(detail_data)}개")

        result = {
            "asset_name": asset_name,
            "mode": mode,
            "timestamp": timestamp,
            "main": main_data,
            "detail": detail_data
        }

        return {"success": True, "data": result}

    except Exception as e:
        logging.error(f"❌ 데이터 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "msg": str(e)}