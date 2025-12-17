<template>
    <div class="histogram-container">
      <div ref="chartRef" :style="{ height: chartHeight, width: '100%' }"></div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, watch, onBeforeUnmount, computed } from 'vue'
  import * as echarts from 'echarts'
  
  export default {
    name: 'EN50160Histogram',
    props: {
      // 히스토그램 데이터 (백엔드에서 받은 형식)
      histogramData: {
        type: Object,
        default: () => ({
          bins: [],
          counts: [],
          percentages: [],
          bin_labels: [],
          bin_centers: []
        })
      },
      // 차트 제목
      title: {
        type: String,
        default: 'Distribution'
      },
      // 단위 (Hz, V, % 등)
      unit: {
        type: String,
        default: ''
      },
      // 바 색상
      barColor: {
        type: String,
        default: '#5470c6'
      },
      // 한계선 (단일 값)
      limitValue: {
        type: Number,
        default: null
      },
      // 한계 범위 (min/max)
      limitMin: {
        type: Number,
        default: null
      },
      limitMax: {
        type: Number,
        default: null
      },
      // 차트 높이
      chartHeight: {
        type: String,
        default: '200px'
      },
      // X축 라벨 표시 간격
      labelInterval: {
        type: Number,
        default: null
      },
      // 범위 초과 색상
      outOfRangeColor: {
        type: String,
        default: '#ef4444'
      },
      // 범위 내 강조 색상
      inRangeHighlightColor: {
        type: String,
        default: null
      }
    },
    setup(props) {
      const chartRef = ref(null)
      let chartInstance = null
  
      // X축 라벨 간격 자동 계산
      const calculatedLabelInterval = computed(() => {
        if (props.labelInterval !== null) return props.labelInterval
        const binCount = props.histogramData?.bin_labels?.length || 0
        if (binCount <= 10) return 0
        if (binCount <= 20) return 1
        if (binCount <= 30) return 2
        return Math.floor(binCount / 10)
      })
  
      // 바 색상 결정 함수
      const getBarColor = (index) => {
        const bins = props.histogramData?.bins || []
        if (bins.length < 2) return props.barColor
  
        const binStart = bins[index]
        const binEnd = bins[index + 1]
  
        // 범위 밖이면 빨간색
        if (props.limitMin !== null && binEnd <= props.limitMin) {
          return props.outOfRangeColor
        }
        if (props.limitMax !== null && binStart >= props.limitMax) {
          return props.outOfRangeColor
        }
        if (props.limitValue !== null && binStart >= props.limitValue) {
          return props.outOfRangeColor
        }
  
        // 범위 내 강조색이 있으면 사용
        if (props.inRangeHighlightColor) {
          if (props.limitMin !== null && props.limitMax !== null) {
            if (binStart >= props.limitMin && binEnd <= props.limitMax) {
              return props.inRangeHighlightColor
            }
          }
        }
  
        return props.barColor
      }
  
      const initChart = () => {
        if (!chartRef.value) return
        
        const { counts, bin_labels, percentages, bin_centers } = props.histogramData || {}
        
        if (!counts || counts.length === 0) {
          // 데이터 없으면 빈 차트
          if (chartInstance) {
            chartInstance.dispose()
            chartInstance = null
          }
          return
        }
  
        if (chartInstance) {
          chartInstance.dispose()
        }
  
        chartInstance = echarts.init(chartRef.value)
  
        // 바 색상 배열 생성
        const barColors = counts.map((_, index) => getBarColor(index))
  
        const option = {
          title: {
            text: props.title,
            left: 'center',
            top: 5,
            textStyle: {
              fontSize: 13,
              fontWeight: 'normal',
              color: '#374151'
            }
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            },
            formatter: (params) => {
              const idx = params[0].dataIndex
              const label = bin_labels[idx] || ''
              const count = counts[idx] || 0
              const pct = percentages[idx] || 0
              return `
                <div style="font-size: 12px;">
                  <div style="font-weight: bold; margin-bottom: 4px;">${label}${props.unit}</div>
                  <div>Count: <b>${count}</b></div>
                  <div>Percentage: <b>${pct}%</b></div>
                </div>
              `
            }
          },
          grid: {
            left: '8%',
            right: '5%',
            bottom: '18%',
            top: '18%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: bin_centers || bin_labels,
            axisLabel: {
              rotate: 45,
              fontSize: 10,
              interval: calculatedLabelInterval.value,
              formatter: (value) => {
                if (typeof value === 'number') {
                  return value.toFixed(2)
                }
                // bin_labels 형식이면 중간값만 표시
                if (typeof value === 'string' && value.includes('-')) {
                  const parts = value.split('-')
                  return parseFloat(parts[0]).toFixed(2)
                }
                return value
              },
              color: '#6b7280'
            },
            axisLine: {
              lineStyle: { color: '#e5e7eb' }
            },
            axisTick: {
              alignWithLabel: true,
              lineStyle: { color: '#e5e7eb' }
            },
            name: props.unit,
            nameLocation: 'end',
            nameTextStyle: {
              fontSize: 11,
              color: '#6b7280'
            }
          },
          yAxis: {
            type: 'value',
            name: 'Count',
            nameTextStyle: {
              fontSize: 11,
              color: '#6b7280'
            },
            axisLabel: {
              fontSize: 10,
              color: '#6b7280'
            },
            axisLine: {
              show: true,
              lineStyle: { color: '#e5e7eb' }
            },
            splitLine: {
              lineStyle: {
                color: '#f3f4f6',
                type: 'dashed'
              }
            }
          },
          series: [
            {
              type: 'bar',
              data: counts.map((value, index) => ({
                value: value,
                itemStyle: {
                  color: barColors[index]
                }
              })),
              barWidth: '85%',
              itemStyle: {
                borderRadius: [2, 2, 0, 0]
              }
            }
          ]
        }
  
        // 한계선 추가
        const markLines = []
        
        if (props.limitMin !== null) {
          // limitMin에 해당하는 x축 인덱스 찾기
          const bins = props.histogramData?.bins || []
          let xAxisIndex = 0
          for (let i = 0; i < bins.length - 1; i++) {
            if (bins[i] <= props.limitMin && bins[i + 1] > props.limitMin) {
              xAxisIndex = i
              break
            }
          }
          markLines.push({
            xAxis: xAxisIndex,
            lineStyle: { color: '#f44336', type: 'dashed', width: 2 },
            label: {
              formatter: `Min: ${props.limitMin}${props.unit}`,
              position: 'start',
              fontSize: 10
            }
          })
        }
  
        if (props.limitMax !== null) {
          const bins = props.histogramData?.bins || []
          let xAxisIndex = bins.length - 2
          for (let i = 0; i < bins.length - 1; i++) {
            if (bins[i] <= props.limitMax && bins[i + 1] > props.limitMax) {
              xAxisIndex = i
              break
            }
          }
          markLines.push({
            xAxis: xAxisIndex,
            lineStyle: { color: '#f44336', type: 'dashed', width: 2 },
            label: {
              formatter: `Max: ${props.limitMax}${props.unit}`,
              position: 'end',
              fontSize: 10
            }
          })
        }
  
        if (props.limitValue !== null) {
          const bins = props.histogramData?.bins || []
          let xAxisIndex = bins.length - 2
          for (let i = 0; i < bins.length - 1; i++) {
            if (bins[i] <= props.limitValue && bins[i + 1] > props.limitValue) {
              xAxisIndex = i
              break
            }
          }
          markLines.push({
            xAxis: xAxisIndex,
            lineStyle: { color: '#f44336', type: 'dashed', width: 2 },
            label: {
              formatter: `Limit: ${props.limitValue}${props.unit}`,
              position: 'end',
              fontSize: 10
            }
          })
        }
  
        if (markLines.length > 0) {
          option.series[0].markLine = {
            silent: true,
            symbol: 'none',
            data: markLines
          }
        }
  
        chartInstance.setOption(option)
      }
  
      // 리사이즈 핸들러
      const handleResize = () => {
        chartInstance?.resize()
      }
  
      onMounted(() => {
        initChart()
        window.addEventListener('resize', handleResize)
      })
  
      watch(
        () => props.histogramData,
        () => {
          initChart()
        },
        { deep: true }
      )
  
      watch(
        () => [props.limitMin, props.limitMax, props.limitValue],
        () => {
          initChart()
        }
      )
  
      onBeforeUnmount(() => {
        window.removeEventListener('resize', handleResize)
        if (chartInstance) {
          chartInstance.dispose()
          chartInstance = null
        }
      })
  
      return {
        chartRef
      }
    }
  }
  </script>
  
  <style scoped>
  .histogram-container {
    width: 100%;
    background: transparent;
  }
  </style>