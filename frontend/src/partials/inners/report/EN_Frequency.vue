<template>
    <div class="en50160-frequency-chart">
      <!-- 요약 테이블 -->
      <div class="summary-table">
        <table>
          <thead>
            <tr>
              <th>EN50160 Requirement</th>
              <th>Measured Frequency</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            <tr class="row-99-5">
              <td>99.5% of the week: {{ limits.limit_99_5?.min }}Hz - {{ limits.limit_99_5?.max }}Hz</td>
              <td>{{ statistics.min }}Hz ~ {{ statistics.max }}Hz</td>
              <td :class="getResultClass(statistics.result_99_5)">{{ statistics.result_99_5 }}</td>
            </tr>
            <tr class="row-100">
              <td>100% of the week: {{ limits.limit_100?.min }}Hz - {{ limits.limit_100?.max }}Hz</td>
              <td>{{ statistics.min }}Hz ~ {{ statistics.max }}Hz</td>
              <td :class="getResultClass(statistics.result_100)">{{ statistics.result_100 }}</td>
            </tr>
          </tbody>
        </table>
      </div>
  
      <!-- 시계열 차트 -->
      <div class="chart-section">
        <h3>Frequency</h3>
        <v-chart class="timeseries-chart" :option="timeseriesOption" autoresize />
        <div class="chart-legend">
          <span class="legend-item flagged"><span class="color-box"></span> Flagged Data</span>
          <span class="legend-item frequency"><span class="color-box"></span> Frequency</span>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, computed, watch } from 'vue'
  import VChart from 'vue-echarts'
  import { use } from 'echarts/core'
  import { CanvasRenderer } from 'echarts/renderers'
  import { LineChart } from 'echarts/charts'
  import {
    TooltipComponent,
    GridComponent,
    MarkLineComponent,
    MarkAreaComponent
  } from 'echarts/components'
  
  use([
    CanvasRenderer,
    LineChart,
    TooltipComponent,
    GridComponent,
    MarkLineComponent,
    MarkAreaComponent
  ])
  
  export default {
    name: 'EN50160FrequencyChart',
    components: { VChart },
    props: {
      data: {
        type: Object,
        default: null
      }
    },
    setup(props) {
      const timeseries = ref({ labels: [], data: [] })
      const statistics = ref({})
      const limits = ref({})
  
      const getResultClass = (result) => ({
        'result-pass': result === 'PASS',
        'result-fail': result === 'FAIL'
      })
  
      // 시계열 차트 옵션
      const timeseriesOption = computed(() => ({
        grid: {
          left: 60,
          right: 20,
          top: 20,
          bottom: 40
        },
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const p = params[0]
            return `${p.name}<br/>Frequency: <b>${p.value?.toFixed(3)} Hz</b>`
          }
        },
        xAxis: {
          type: 'category',
          data: timeseries.value.labels,
          axisLabel: {
            rotate: 0,
            interval: Math.floor(timeseries.value.labels.length / 7) || 1
          }
        },
        yAxis: {
          type: 'value',
          name: '[Hz]',
          min: 56,
          max: 63,
          axisLabel: {
            formatter: '{value}'
          }
        },
        series: [{
          name: 'Frequency',
          type: 'line',
          data: timeseries.value.data,
          symbol: 'none',
          lineStyle: {
            color: '#008080',
            width: 1.5
          },
          areaStyle: {
            color: 'rgba(0, 128, 128, 0.1)'
          },
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { width: 2 },
            data: [
              // 100% 한계 (빨간선)
              { yAxis: limits.value.limit_100?.max || 62.4, lineStyle: { color: '#f44336' }, label: { show: false } },
              { yAxis: limits.value.limit_100?.min || 56.4, lineStyle: { color: '#f44336' }, label: { show: false } },
              // 99.5% 한계 (노란선)
              { yAxis: limits.value.limit_99_5?.max || 60.6, lineStyle: { color: '#ffc107' }, label: { show: false } },
              { yAxis: limits.value.limit_99_5?.min || 59.4, lineStyle: { color: '#ffc107' }, label: { show: false } }
            ]
          },
          markArea: {
            silent: true,
            data: [
              // 99.5% 범위 내 영역 (연한 노랑)
              [{
                yAxis: limits.value.limit_99_5?.min || 59.4,
                itemStyle: { color: 'rgba(255, 255, 200, 0.3)' }
              }, {
                yAxis: limits.value.limit_99_5?.max || 60.6
              }]
            ]
          }
        }]
      }))
  
      // 데이터 업데이트
      watch(() => props.data, (newData) => {
        if (newData) {
          timeseries.value = newData.timeseries || { labels: [], data: [] }
          statistics.value = newData.statistics || {}
          limits.value = newData.limits || {}
        }
      }, { immediate: true, deep: true })
  
      return {
        timeseries,
        statistics,
        limits,
        timeseriesOption,
        getResultClass
      }
    }
  }
  </script>
  
  <style scoped>
  .en50160-frequency-chart {
    padding: 16px;
    background: #fff;
  }
  
  .summary-table {
    margin-bottom: 20px;
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
  
  .summary-table .row-99-5 {
    background: #fffde7;
  }
  
  .summary-table .row-100 {
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
    margin-bottom: 24px;
  }
  
  .chart-section h3 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    text-align: center;
  }
  
  .timeseries-chart {
    width: 100%;
    height: 300px;
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
  }
  
  .legend-item.flagged .color-box {
    background: rgba(255, 255, 200, 0.8);
    border: 1px solid #ccc;
  }
  
  .legend-item.frequency .color-box {
    background: #008080;
  }
  </style>
  