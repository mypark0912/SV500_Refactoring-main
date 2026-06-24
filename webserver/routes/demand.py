"""
수요전력(Demand) 트렌드: InfluxDB Task 생성 + FastAPI 라우터

기존 다운샘플링 패턴:
  - InfluxDB Task API로 등록
  - aggregateWindow offset으로 로컬 자정 기준 보정
  - 결과를 ntek_1h, ntek_1d 버킷에 저장
  - Flux to()는 Task 내부에서만 사용

기존 DemandDataProcessor 저장 구조:
  - bucket: "ntek"
  - measurement: "demand"
  - tags: {"channel": "..."}
  - fields: flatten_demand() 결과 (CD_P_import, CD_S, MD_P_import_value 등)
"""

import logging
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel

from states.global_state import influx_state, aesState

router = APIRouter()

BUCKET = "ntek"
BUCKET_1H = "ntek_1h"
BUCKET_1D = "ntek_1d"
MEASUREMENT = "demand"

setting_timeout = httpx.Timeout(30.0, connect=10.0)


# =============================================================================
# 1. InfluxDB 다운샘플링 Task 생성
# =============================================================================

async def create_demand_downsampling_tasks():
    """Demand 다운샘플링 Task 생성 (기존 패턴과 동일)"""
    try:
        config = aesState.getInflux()
        token = aesState.decrypt(config["cipher"])
        org_name = "ntek"

        # 로컬 타임존 UTC offset 자동 계산
        local_now = datetime.now().astimezone()
        utc_offset_hours = int(local_now.utcoffset().total_seconds() / 3600)

        # aggregateWindow offset (UTC 자정 → 로컬 자정)
        agg_offset = f"-{utc_offset_hours}h" if utc_offset_hours > 0 else f"{abs(utc_offset_hours)}h"

        # cron 실행 시간 (로컬 자정 = UTC 몇 시?)
        cron_hour = (24 - utc_offset_hours) % 24

        logging.info(
            f"🕐 [Demand] Local UTC offset: +{utc_offset_hours}h, "
            f"agg_offset: {agg_offset}, cron_hour: {cron_hour} UTC"
        )

        tasks = [
            # Task 1: demand 15분 → 1시간 (MAX, AVG)
            {
                "name": "downsample_demand_to_1h",
                "flux": f'''
option task = {{name: "downsample_demand_to_1h", every: 1h, offset: 5m}}

base = from(bucket: "ntek")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "demand")

// CD_P_import MAX (유효전력 피크)
p_max = base
  |> filter(fn: (r) => r["_field"] == "CD_P_import")
  |> aggregateWindow(every: 1h, fn: max, createEmpty: false)
  |> set(key: "_field", value: "demand_p_max")

// CD_P_import AVG (유효전력 평균 — 디맨드 부하율용)
p_avg = base
  |> filter(fn: (r) => r["_field"] == "CD_P_import")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> set(key: "_field", value: "demand_p_avg")

// CD_S MAX (피상전력 피크 — Peak Load Rate용)
s_max = base
  |> filter(fn: (r) => r["_field"] == "CD_S")
  |> aggregateWindow(every: 1h, fn: max, createEmpty: false)
  |> set(key: "_field", value: "demand_s_max")

// CD_Q_import MAX (무효전력)
q_max = base
  |> filter(fn: (r) => r["_field"] == "CD_Q_import")
  |> aggregateWindow(every: 1h, fn: max, createEmpty: false)
  |> set(key: "_field", value: "demand_q_max")

union(tables: [p_max, p_avg, s_max, q_max])
  |> set(key: "_measurement", value: "demand")
  |> to(bucket: "ntek_1h", org: "{org_name}")
''',
                "every": "1h",
                "description": "Downsample demand to 1h (max, avg)"
            },

            # Task 2: demand 1시간 → 1일 (MAX, AVG, 로컬 자정 기준)
            {
                "name": "downsample_demand_to_1d",
                "flux": f'''
option task = {{name: "downsample_demand_to_1d", cron: "25 {cron_hour} * * *"}}

base = from(bucket: "ntek_1h")
  |> range(start: -1d)
  |> filter(fn: (r) => r["_measurement"] == "demand")

// demand_p_max의 일별 MAX (하루 중 가장 높은 피크)
p_max = base
  |> filter(fn: (r) => r["_field"] == "demand_p_max")
  |> aggregateWindow(every: 1d, fn: max, createEmpty: false, offset: {agg_offset})
  |> set(key: "_field", value: "demand_p_max")

// demand_p_avg의 일별 AVG (하루 평균)
p_avg = base
  |> filter(fn: (r) => r["_field"] == "demand_p_avg")
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false, offset: {agg_offset})
  |> set(key: "_field", value: "demand_p_avg")

// demand_s_max의 일별 MAX
s_max = base
  |> filter(fn: (r) => r["_field"] == "demand_s_max")
  |> aggregateWindow(every: 1d, fn: max, createEmpty: false, offset: {agg_offset})
  |> set(key: "_field", value: "demand_s_max")

// demand_q_max의 일별 MAX
q_max = base
  |> filter(fn: (r) => r["_field"] == "demand_q_max")
  |> aggregateWindow(every: 1d, fn: max, createEmpty: false, offset: {agg_offset})
  |> set(key: "_field", value: "demand_q_max")

union(tables: [p_max, p_avg, s_max, q_max])
  |> set(key: "_measurement", value: "demand")
  |> to(bucket: "ntek_1d", org: "{org_name}")
''',
                "cron": f"25 {cron_hour} * * *",
                "description": "Downsample demand to 1d (max, avg, local TZ)"
            },
        ]

        results = []

        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            # ⚠️ InfluxDB POST /api/v2/tasks 는 이름 중복을 막지 않음(매번 새 ID 생성).
            #    422 가정만으로는 재실행 때마다 누적됨 → 선조회 후 없을 때만 생성.
            existing_names = set()
            try:
                list_resp = await client.get(
                    f"http://127.0.0.1:8086/api/v2/tasks",
                    headers={"Authorization": f"Token {token}"},
                    params={"orgID": config['org_id']}
                )
                if list_resp.status_code == 200:
                    existing_names = {t["name"] for t in list_resp.json().get("tasks", [])}
            except Exception as e:
                logging.warning(f"⚠️ 기존 task 목록 조회 실패(중복체크 생략): {e}")

            for task_info in tasks:
                if task_info["name"] in existing_names:
                    logging.info(f"ℹ️ Demand Task '{task_info['name']}' already exists (skip)")
                    results.append({"task": task_info["name"], "success": True, "existed": True})
                    continue

                task_data = {
                    "orgID": config['org_id'],
                    "org": org_name,
                    "name": task_info["name"],
                    "description": task_info["description"],
                    "status": "active",
                    "flux": task_info["flux"]
                }

                response = await client.post(
                    f"http://127.0.0.1:8086/api/v2/tasks",
                    headers={"Authorization": f"Token {token}"},
                    json=task_data
                )

                if response.status_code == 201:
                    task_id = response.json().get("id")
                    logging.info(f"✅ Demand Task '{task_info['name']}' created (ID: {task_id})")
                    results.append({"task": task_info["name"], "success": True, "id": task_id})
                elif response.status_code == 422:
                    logging.info(f"ℹ️ Demand Task '{task_info['name']}' already exists")
                    results.append({"task": task_info["name"], "success": True, "existed": True})
                else:
                    error_msg = response.json().get("message", response.text)
                    logging.error(f"❌ Demand Task '{task_info['name']}' failed: {error_msg}")
                    results.append({"task": task_info["name"], "success": False, "error": error_msg})

        success_count = sum(1 for r in results if r["success"])
        return {
            "success": success_count > 0,
            "message": f"Demand tasks: {success_count}/{len(tasks)} created/verified",
            "results": results
        }

    except Exception as e:
        logging.error(f"❌ Demand downsampling tasks creation error: {e}")
        return {"success": False, "message": str(e)}


# =============================================================================
# 2. FastAPI 라우터
# =============================================================================

class TimeRangeEnum(str, Enum):
    hourly = "hourly"
    daily = "daily"
    monthly = "monthly"


class DemandTrendItem(BaseModel):
    time: str
    demand_max: float            # 피크 디맨드 kW
    demand_avg: float            # 평균 디맨드 kW
    demand_load_factor: float    # 디맨드 부하율 % (AVG/MAX*100)


class DemandSummary(BaseModel):
    peak_demand: float           # 피크 디맨드 kW
    peak_demand_time: str        # 피크 발생 시각
    average_demand: float        # 평균 디맨드 kW
    demand_load_factor: float    # 디맨드 부하율 %
    peak_load_rate: Optional[float] = None  # 변압기 용량 대비 %


class DemandTrendResponse(BaseModel):
    summary: DemandSummary
    trend: List[DemandTrendItem]


class DemandHeatmapItem(BaseModel):
    day: int       # 0=Mon ~ 6=Sun
    hour: int      # 0~23
    value: float   # 평균 디맨드 kW


class DemandHeatmapResponse(BaseModel):
    data: List[DemandHeatmapItem]
    max_value: float


class DemandLoadFactorMonthlyItem(BaseModel):
    month: str
    load_factor: float
    peak_demand: float
    average_demand: float


class DemandLoadFactorMonthlyResponse(BaseModel):
    data: List[DemandLoadFactorMonthlyItem]


# --- 의존성 ---

def get_transformer_capacity(channel: str) -> Optional[float]:
    """
    변압기 용량(kVA) 조회.
    실제 프로젝트의 device_registry 또는 설정에서 가져오도록 교체.
    """
    # 예: device_registry.get_device(channel).get("transformer_capacity_kva")
    return None


# --- 헬퍼 ---

def _parse_time_range(
    start: Optional[str],
    stop: Optional[str],
    range_type: TimeRangeEnum,
) -> tuple:
    """시작/종료 시각 파싱. 미지정 시 range_type에 따라 기본값."""
    if start and stop:
        return start, stop

    now = datetime.now(timezone.utc)
    defaults = {
        TimeRangeEnum.hourly: timedelta(hours=24),
        TimeRangeEnum.daily: timedelta(days=30),
        TimeRangeEnum.monthly: timedelta(days=365),
    }
    start_dt = now - defaults[range_type]
    return start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), now.strftime("%Y-%m-%dT%H:%M:%SZ")


def _get_demand_bucket(start_str: str, stop_str: str) -> tuple:
    """기간에 따라 버킷과 필드명 선택.
    Returns: (bucket, max_field, avg_field, need_agg)
      - 7일 이하: ntek (raw) → CD_P_import, aggregateWindow 필요
      - 90일 이하: ntek_1h → demand_p_max/demand_p_avg, 이미 집계됨
      - 그 이상: ntek_1d → demand_p_max/demand_p_avg, 이미 집계됨
    """
    try:
        start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        stop = datetime.fromisoformat(stop_str.replace('Z', '+00:00'))
        duration = stop - start

        if duration <= timedelta(days=7):
            return BUCKET, "CD_P_import", "CD_P_import", True
        elif duration <= timedelta(days=90):
            return BUCKET_1H, "demand_p_max", "demand_p_avg", False
        else:
            return BUCKET_1D, "demand_p_max", "demand_p_avg", False
    except:
        return BUCKET, "CD_P_import", "CD_P_import", True


def _calc_load_factor(avg: float, peak: float) -> float:
    return round(avg / peak * 100, 1) if peak > 0 else 0.0


def _execute_flux(query: str) -> list:
    """Flux 쿼리 실행 후 레코드 리스트 반환"""
    query_api = influx_state.query_api
    tables = query_api.query(query)

    records = []
    for table in tables:
        for record in table.records:
            records.append(record.values)
    return records


# --- Endpoints ---

@router.get("/trend/{channel}", response_model=DemandTrendResponse)
async def get_demand_trend(
    channel: str,
    range_type: TimeRangeEnum = Query(TimeRangeEnum.hourly),
    start: Optional[str] = Query(None, description="시작 시각 ISO format"),
    stop: Optional[str] = Query(None, description="종료 시각 ISO format"),
):
    """
    Chart 1: Demand Power Trend
    - 바 차트: 시간별/일별/월별 피크 디맨드 (kW)
    - 라인: 디맨드 부하율 (%)
    - 요약: Peak / Avg / Load Factor / Peak Load Rate
    """
    start_str, stop_str = _parse_time_range(start, stop, range_type)
    bucket, max_field, avg_field, need_agg = _get_demand_bucket(start_str, stop_str)

    local_now = datetime.now().astimezone()
    utc_offset_hours = int(local_now.utcoffset().total_seconds() / 3600)
    agg_offset = f"-{utc_offset_hours}h" if utc_offset_hours > 0 else f"{abs(utc_offset_hours)}h"

    agg_windows = {
        TimeRangeEnum.hourly: "1h",
        TimeRangeEnum.daily: "1d",
        TimeRangeEnum.monthly: "1mo",
    }
    every = agg_windows[range_type]
    offset_param = "" if range_type == TimeRangeEnum.hourly else f", offset: {agg_offset}"

    if need_agg:
        # raw 버킷 → aggregateWindow로 집계
        query = f'''
        base = from(bucket: "{bucket}")
            |> range(start: {start_str}, stop: {stop_str})
            |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
            |> filter(fn: (r) => r["channel"] == "{channel}")
            |> filter(fn: (r) => r["_field"] == "{max_field}")

        p_max = base
            |> aggregateWindow(every: {every}, fn: max, createEmpty: false{offset_param})
            |> set(key: "_field", value: "demand_p_max")

        p_avg = base
            |> aggregateWindow(every: {every}, fn: mean, createEmpty: false{offset_param})
            |> set(key: "_field", value: "demand_p_avg")

        union(tables: [p_max, p_avg])
            |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"])
        '''
    else:
        # 다운샘플링 버킷 → 이미 집계됨, 재집계만 (monthly) 또는 그대로 조회
        if range_type == TimeRangeEnum.monthly:
            query = f'''
            base = from(bucket: "{bucket}")
                |> range(start: {start_str}, stop: {stop_str})
                |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
                |> filter(fn: (r) => r["channel"] == "{channel}")

            p_max = base
                |> filter(fn: (r) => r["_field"] == "{max_field}")
                |> aggregateWindow(every: 1mo, fn: max, createEmpty: false{offset_param})
                |> set(key: "_field", value: "demand_p_max")

            p_avg = base
                |> filter(fn: (r) => r["_field"] == "{avg_field}")
                |> aggregateWindow(every: 1mo, fn: mean, createEmpty: false{offset_param})
                |> set(key: "_field", value: "demand_p_avg")

            union(tables: [p_max, p_avg])
                |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"])
            '''
        else:
            query = f'''
            from(bucket: "{bucket}")
                |> range(start: {start_str}, stop: {stop_str})
                |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
                |> filter(fn: (r) => r["channel"] == "{channel}")
                |> filter(fn: (r) =>
                    r["_field"] == "{max_field}" or
                    r["_field"] == "{avg_field}"
                )
                |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"])
            '''

    results = _execute_flux(query)
    logging.info(f"[Demand Trend] range_type={range_type}, results count={len(results)}")

    trend = []
    all_max = []
    all_avg = []

    for row in results:
        d_max = float(row.get("demand_p_max", 0) or 0)
        d_avg = float(row.get("demand_p_avg", 0) or 0)

        time_val = row.get("_time")
        time_str = time_val.isoformat() if hasattr(time_val, "isoformat") else str(time_val)

        trend.append(DemandTrendItem(
            time=time_str,
            demand_max=round(d_max, 2),
            demand_avg=round(d_avg, 2),
            demand_load_factor=_calc_load_factor(d_avg, d_max),
        ))
        all_max.append(d_max)
        all_avg.append(d_avg)

    # 요약
    period_peak = max(all_max) if all_max else 0.0
    period_avg = sum(all_avg) / len(all_avg) if all_avg else 0.0

    peak_time = ""
    if all_max and trend:
        peak_idx = all_max.index(period_peak)
        peak_time = trend[peak_idx].time

    capacity = get_transformer_capacity(channel)
    peak_load_rate = round(period_peak / capacity * 100, 1) if capacity else None

    return DemandTrendResponse(
        summary=DemandSummary(
            peak_demand=round(period_peak, 2),
            peak_demand_time=peak_time,
            average_demand=round(period_avg, 2),
            demand_load_factor=_calc_load_factor(period_avg, period_peak),
            peak_load_rate=peak_load_rate,
        ),
        trend=trend,
    )


@router.get("/heatmap/{channel}", response_model=DemandHeatmapResponse)
async def get_demand_heatmap(
    channel: str,
    start: Optional[str] = Query(None),
    stop: Optional[str] = Query(None),
):
    """
    Chart 2: Demand Pattern Analysis (Day × Hour 히트맵)
    요일 × 시간대별 평균 디맨드 분포
    ntek_1h 버킷 사용 (시간별 demand_p_max 기준)
    """
    start_str, stop_str = _parse_time_range(start, stop, TimeRangeEnum.daily)
    bucket, max_field, _, need_agg = _get_demand_bucket(start_str, stop_str)

    # 로컬 타임존 offset 계산
    local_now = datetime.now().astimezone()
    utc_offset_hours = int(local_now.utcoffset().total_seconds() / 3600)
    offset_duration = f"{utc_offset_hours}h"

    # raw 버킷이면 1h 집계 필요, 다운샘플링 버킷이면 이미 시간별 집계됨
    agg_step = '|> aggregateWindow(every: 1h, fn: max, createEmpty: false)' if need_agg else ''

    query = f'''
    import "date"
    import "timezone"

    option location = timezone.fixed(offset: {offset_duration})

    from(bucket: "{bucket}")
        |> range(start: {start_str}, stop: {stop_str})
        |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
        |> filter(fn: (r) => r["channel"] == "{channel}")
        |> filter(fn: (r) => r["_field"] == "{max_field}")
        {agg_step}
        |> map(fn: (r) => ({{
            r with
            dow: date.weekDay(t: r._time),
            hour: date.hour(t: r._time)
        }}))
        |> group(columns: ["dow", "hour"])
        |> mean()
        |> group()
        |> sort(columns: ["dow", "hour"])
    '''

    results = _execute_flux(query)
    logging.info(f"[Demand Heatmap] results count={len(results)}")

    data = []
    max_val = 0.0

    for row in results:
        val = round(float(row.get("_value", 0) or 0), 2)
        # Flux date.weekDay: 0=Sunday → 프론트 0=Monday 변환
        dow_sun = int(row.get("dow", 0))
        dow_mon = (dow_sun - 1) % 7  # Sun(0)→6, Mon(1)→0, ..., Sat(6)→5
        data.append(DemandHeatmapItem(
            day=dow_mon,
            hour=int(row.get("hour", 0)),
            value=val,
        ))
        max_val = max(max_val, val)

    return DemandHeatmapResponse(data=data, max_value=max_val)


@router.get("/load-factor-monthly/{channel}",
            response_model=DemandLoadFactorMonthlyResponse)
async def get_demand_load_factor_monthly(
    channel: str,
    months: int = Query(12, ge=1, le=36),
):
    """
    Chart 3: Demand Load Factor Monthly Trend
    월별 디맨드 부하율 추이 (AVG/MAX × 100)
    ntek_1d 버킷에서 월별 재집계
    """
    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(days=months * 31)

    start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    stop_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    bucket, max_field, avg_field, need_agg = _get_demand_bucket(start_str, stop_str)

    local_now = datetime.now().astimezone()
    utc_offset_hours = int(local_now.utcoffset().total_seconds() / 3600)
    agg_offset = f"-{utc_offset_hours}h" if utc_offset_hours > 0 else f"{abs(utc_offset_hours)}h"

    if need_agg:
        # raw 버킷 → 월별 직접 집계
        query = f'''
        base = from(bucket: "{bucket}")
            |> range(start: {start_str}, stop: {stop_str})
            |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
            |> filter(fn: (r) => r["channel"] == "{channel}")
            |> filter(fn: (r) => r["_field"] == "{max_field}")

        max_m = base
            |> aggregateWindow(every: 1mo, fn: max, createEmpty: false, offset: {agg_offset})
            |> set(key: "_field", value: "monthly_max")

        avg_m = base
            |> aggregateWindow(every: 1mo, fn: mean, createEmpty: false, offset: {agg_offset})
            |> set(key: "_field", value: "monthly_avg")

        union(tables: [max_m, avg_m])
            |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"])
        '''
    else:
        # 다운샘플링 버킷 → 월별 재집계
        query = f'''
        base = from(bucket: "{bucket}")
            |> range(start: {start_str}, stop: {stop_str})
            |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
            |> filter(fn: (r) => r["channel"] == "{channel}")

        max_m = base
            |> filter(fn: (r) => r["_field"] == "{max_field}")
            |> aggregateWindow(every: 1mo, fn: max, createEmpty: false, offset: {agg_offset})
            |> set(key: "_field", value: "monthly_max")

        avg_m = base
            |> filter(fn: (r) => r["_field"] == "{avg_field}")
            |> aggregateWindow(every: 1mo, fn: mean, createEmpty: false, offset: {agg_offset})
            |> set(key: "_field", value: "monthly_avg")

        union(tables: [max_m, avg_m])
            |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"])
        '''

    results = _execute_flux(query)
    logging.info(f"[Demand Monthly] results count={len(results)}")

    items = []
    for row in results:
        m_max = float(row.get("monthly_max", 0) or 0)
        m_avg = float(row.get("monthly_avg", 0) or 0)

        time_val = row.get("_time")
        if hasattr(time_val, "astimezone"):
            month_str = time_val.astimezone().strftime("%Y-%m")
        elif hasattr(time_val, "strftime"):
            month_str = time_val.strftime("%Y-%m")
        else:
            month_str = str(time_val)[:7]

        items.append(DemandLoadFactorMonthlyItem(
            month=month_str,
            load_factor=_calc_load_factor(m_avg, m_max),
            peak_demand=round(m_max, 2),
            average_demand=round(m_avg, 2),
        ))

    return DemandLoadFactorMonthlyResponse(data=items)


async def check_demand_downsampling_status():
    """Demand 다운샘플링 Task 존재 여부 확인"""
    try:
        config = aesState.getInflux()
        token = aesState.decrypt(config["cipher"])

        task_names = [
            "downsample_demand_to_1h",
            "downsample_demand_to_1d",
        ]

        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.get(
                "http://127.0.0.1:8086/api/v2/tasks",
                headers={"Authorization": f"Token {token}"},
                params={"orgID": config['org_id']}
            )

            if response.status_code == 200:
                all_tasks = response.json().get("tasks", [])
                existing = {t["name"] for t in all_tasks}
                return {"result": all(name in existing for name in task_names)}

        return {"result": False}

    except Exception as e:
        logging.error(f"❌ Demand 다운샘플링 상태 확인 실패: {e}")
        return {"result": False}



@router.get("/summary/{channel}", response_model=DemandSummary)
async def get_demand_summary(
    channel: str,
    start: Optional[str] = Query(None),
    stop: Optional[str] = Query(None),
):
    """
    리포트 요약 지표 (단독 조회용)
    - Peak Demand + 발생 시각
    - Average Demand
    - Demand Load Factor %
    - Peak Load Rate % (변압기 용량 대비)
    """
    start_str, stop_str = _parse_time_range(start, stop, TimeRangeEnum.daily)

    # Peak: raw 데이터(ntek)에서 CD_P_import max → 정확한 시각 확인
    peak_query = f'''
    from(bucket: "{BUCKET}")
        |> range(start: {start_str}, stop: {stop_str})
        |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
        |> filter(fn: (r) => r["channel"] == "{channel}")
        |> filter(fn: (r) => r["_field"] == "CD_P_import")
        |> max()
    '''

    avg_query = f'''
    from(bucket: "{BUCKET}")
        |> range(start: {start_str}, stop: {stop_str})
        |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
        |> filter(fn: (r) => r["channel"] == "{channel}")
        |> filter(fn: (r) => r["_field"] == "CD_P_import")
        |> mean()
    '''

    peak_results = _execute_flux(peak_query)
    avg_results = _execute_flux(avg_query)

    peak_demand = 0.0
    peak_time = ""
    avg_demand = 0.0

    for row in peak_results:
        peak_demand = round(float(row.get("_value", 0) or 0), 2)
        t = row.get("_time")
        peak_time = t.isoformat() if hasattr(t, "isoformat") else str(t)

    for row in avg_results:
        avg_demand = round(float(row.get("_value", 0) or 0), 2)

    capacity = get_transformer_capacity(channel)
    peak_load_rate = round(peak_demand / capacity * 100, 1) if capacity else None

    return DemandSummary(
        peak_demand=peak_demand,
        peak_demand_time=peak_time,
        average_demand=avg_demand,
        demand_load_factor=_calc_load_factor(avg_demand, peak_demand),
        peak_load_rate=peak_load_rate,
    )
