<template>
  <div class="en50160-chart">
    <!-- 타이틀 -->
    <div class="chart-title" v-if="title">
      <h2>{{ title }}</h2>
    </div>

    <!-- 요약 테이블 -->
    <div class="summary-table" v-if="tableData && tableData.length">
      <table>
        <thead>
          <tr>
            <th v-for="col in tableColumns" :key="col.key">{{ col.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in tableData" :key="index" :class="row.rowClass">
            <td v-for="col in tableColumns" :key="col.key" :class="getCellClass(row, col.key)">
              {{ formatCell(row[col.key], col.format) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 시계열 차트 -->
    <div class="chart-section">
      <v-chart class="timeseries-chart" :option="chartOption" autoresize />
      <div class="chart-legend" v-if="legendItems && legendItems.length">
        <span 
          v-for="item in legendItems" 
          :key="item.name" 
          class="legend-item"
        >
          <span class="color-box" :style="{ background: item.color }"></span>
          {{ item.name }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, watch, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  MarkAreaComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  MarkAreaComponent
])

export default {
  name: 'EN50160Chart',
  components: { VChart },
  props: {
    // 차트 타이틀
    title: {
      type: String,
      default: ''
    },
    // 시계열 데이터 { labels: [], datasets: [{ name, data, color }] }
    timeseries: {
      type: Object,
      default: () => ({ labels: [], datasets: [] })
    },
    // Y축 설정 { name, min, max, formatter }
    yAxis: {
      type: Object,
      default: () => ({ name: '', min: null, max: null })
    },
    // 한계선 [{ value, color, label }]
    limitLines: {
      type: Array,
      default: () => []
    },
    // 영역 표시 [{ from, to, color }]
    markAreas: {
      type: Array,
      default: () => []
    },
    // 테이블 컬럼 [{ key, label, format }]
    tableColumns: {
      type: Array,
      default: () => []
    },
    // 테이블 데이터 [{ ...row, rowClass }]
    tableData: {
      type: Array,
      default: () => []
    },
    // 범례 아이템 [{ name, color }]
    legendItems: {
      type: Array,
      default: () => []
    },
    // 툴팁 포맷터
    tooltipFormatter: {
      type: Function,
      default: null
    },
    // 차트 높이
    chartHeight: {
      type: String,
      default: '300px'
    }
  },
  setup(props) {
    // 차트 옵션 생성
    const chartOption = computed(() => {
      const labels = props.timeseries?.labels || []
      
      // 데이터셋 생성
      const series = (props.timeseries?.datasets || []).map((ds, index) => {
        const seriesConfig = {
          name: ds.name || `Series ${index + 1}`,
          type: 'line',
          data: ds.data || [],
          symbol: 'none',
          lineStyle: {
            color: ds.color || '#008080',
            width: ds.lineWidth || 1.5
          }
        }

        // 영역 채우기
        if (ds.areaStyle !== false) {
          seriesConfig.areaStyle = {
            color: ds.areaColor || (ds.color ? `${ds.color}1A` : 'rgba(0, 128, 128, 0.1)')
          }
        }

        // 첫 번째 시리즈에 markLine, markArea 추가
        if (index === 0) {
          // 한계선
          if (props.limitLines && props.limitLines.length) {
            seriesConfig.markLine = {
              silent: true,
              symbol: 'none',
              lineStyle: { width: 2 },
              data: props.limitLines.map(line => ({
                yAxis: line.value,
                lineStyle: { 
                  color: line.color || '#f44336',
                  type: line.type || 'solid'
                },
                label: { show: false }
              }))
            }
          }

          // 영역 표시
          if (props.markAreas && props.markAreas.length) {
            seriesConfig.markArea = {
              silent: true,
              data: props.markAreas.map(area => ([
                {
                  yAxis: area.from,
                  itemStyle: { color: area.color || 'rgba(255, 255, 200, 0.3)' }
                },
                { yAxis: area.to }
              ]))
            }
          }
        }

        return seriesConfig
      })

      // 기본 툴팁 포맷터
      const defaultTooltipFormatter = (params) => {
        if (!Array.isArray(params)) params = [params]
        let result = `${params[0]?.name || ''}<br/>`
        params.forEach(p => {
          const value = typeof p.value === 'number' ? p.value.toFixed(3) : p.value
          result += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${value}</b><br/>`
        })
        return result
      }

      return {
        grid: {
          left: 70,
          right: 20,
          top: 30,
          bottom: 40
        },
        tooltip: {
          trigger: 'axis',
          formatter: props.tooltipFormatter || defaultTooltipFormatter
        },
        xAxis: {
          type: 'category',
          data: labels,
          axisLabel: {
            rotate: 0,
            interval: Math.floor(labels.length / 7) || 1
          }
        },
        yAxis: {
          type: 'value',
          name: props.yAxis?.name || '',
          nameLocation: 'middle',
          nameGap: 45,
          min: props.yAxis?.min ?? undefined,
          max: props.yAxis?.max ?? undefined,
          axisLabel: {
            formatter: props.yAxis?.formatter || '{value}'
          }
        },
        series: series
      }
    })

    // 셀 클래스 결정
    const getCellClass = (row, key) => {
      const value = row[key]
      if (value === 'PASS') return 'result-pass'
      if (value === 'FAIL') return 'result-fail'
      return ''
    }

    // 셀 포맷팅
    const formatCell = (value, format) => {
      if (value === null || value === undefined) return '-'
      if (format === 'percent') return `${value}%`
      if (format === 'hz') return `${value} Hz`
      if (format === 'volt') return `${value} V`
      return value
    }

    return {
      chartOption,
      getCellClass,
      formatCell
    }
  }
}
</script>

<style scoped>
.en50160-chart {
  padding: 16px;
  background: #fff;
}

.chart-title {
  margin-bottom: 16px;
  text-align: center;
}

.chart-title h2 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.summary-table {
  margin-bottom: 20px;
  overflow-x: auto;
}

.summary-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.summary-table th,
.summary-table td {
  border: 1px solid #ddd;
  padding: 10px 12px;
  text-align: center;
}

.summary-table th {
  background: #f5f5f5;
  font-weight: 600;
}

.summary-table .row-99-5,
.summary-table .row-warning {
  background: #fffde7;
}

.summary-table .row-100,
.summary-table .row-critical {
  background: #fff8e1;
}

.result-pass {
  color: #2e7d32;
  font-weight: bold;
}

.result-fail {
  color: #c62828;
  font-weight: bold;
}

.chart-section {
  margin-bottom: 16px;
}

.timeseries-chart {
  width: 100%;
  height: v-bind(chartHeight);
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 8px;
  font-size: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.color-box {
  width: 20px;
  height: 12px;
  display: inline-block;
  border: 1px solid #ddd;
}
</style>
