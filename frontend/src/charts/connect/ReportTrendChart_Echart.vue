<template>
  <div ref="chartRef" class="w-full h-[400px]"></div>
</template>

<script>
import { onMounted, onBeforeUnmount, ref, watch, inject } from "vue";  // ✅ inject 추가
import * as echarts from "echarts";
import { useDark } from "@vueuse/core";
import { chartColors } from "../ChartjsConfig";
import { useI18n } from "vue-i18n";

export default {
  name: "LineChart",
  props: {
    chartData: {
      type: Array,
      required: true,
    },
    chartLabels: {
      type: Array,
      required: true,
    },
    title:String,
  },
  setup(props) {
    // ✅ PDF 모드 inject
    const isPdfMode = inject('isPdfMode', false)
    
    const { t, locale } = useI18n();
    const chartRef = ref(null);
    let chartInstance = null;

    const darkMode = useDark();
    const { textColor, gridColor } = chartColors;
    
    // ✅ 텍스트 색상 계산 (PDF 모드일 때는 항상 검정)
    const getTextColor = () => {
      if (isPdfMode) return '#000000'
      return darkMode.value ? textColor.dark : textColor.light
    }
    
    const thresholdColorMap = {
      warning: "#ffff00",
      repair: "#ff0000",
      inspect: "#ff7f00",
    };
    
    const getLineColor = (index) => {
      const colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
      ];
      return colors[index % colors.length];
    };

    const buildSeriesAndLegends = () => {
      let thresholdCounter = 0;
      const normalSeries = [];
      const thresholdSeries = [];
      const normalLegendNames = [];
      const thresholdLegendNames = [];

      props.chartData.forEach((dataset, index) => {
        if (dataset.isThreshold) {
          const color =
            thresholdColorMap[dataset.name.toLowerCase()] ??
          thresholdCounter++;
          thresholdSeries.push({
            name: dataset.name,
            type: "line",
            data: dataset.data,
            smooth: true,
            symbol: "none",
            lineStyle: { width: 1, type: "dashed" },
            itemStyle: { color },
            label: {
              show: true,
              position: "end",
              formatter: function (params) {
                const rawDate = new Date(params.name);
                const yyyy = rawDate.getFullYear();
                const MM = String(rawDate.getMonth() + 1).padStart(2, "0");
                const dd = String(rawDate.getDate()).padStart(2, "0");
                const HH = String(rawDate.getHours()).padStart(2, "0");
                const mm = String(rawDate.getMinutes()).padStart(2, "0");
                const ss = String(rawDate.getSeconds()).padStart(2, "0");
                return `${yyyy}-${MM}-${dd} ${HH}:${mm}:${ss}`;
              },
              color,
            },
          });
          thresholdLegendNames.push(dataset.name);
        } else {
          normalSeries.push({
            name: dataset.name,
            type: "line",
            data: dataset.data,
            smooth: true,
            lineStyle: { width: 2 },
            itemStyle: { color: getLineColor(index) },
          });
          normalLegendNames.push(dataset.name);
        }
      });

      const allSeries = [...normalSeries, ...thresholdSeries];

      const legends = [
        {
          data: normalLegendNames,
          bottom: 15,
          textStyle: {
            color: getTextColor(),  // ✅ 동적 텍스트 색상
          },
        },
      ];

      return { allSeries, legends };
    };

    const getYAxisRange = (seriesList) => {
      const allValues = seriesList.flatMap(s =>
        s.data.filter(v => typeof v === "number" && !isNaN(v))
      );

      if (allValues.length === 0) return [0, 1];

      const min = Math.min(...allValues);
      const max = Math.max(...allValues);

      return [Math.floor(Math.min(min, 0)), Math.ceil(max)];
    };

    const initChart = () => {
      if (chartRef.value) {
        chartInstance = echarts.init(chartRef.value);

        const { allSeries, legends } = buildSeriesAndLegends();

        const [minY, maxY] = getYAxisRange(allSeries);

        const isEmpty =
          props.chartData.length === 0 ||
          allSeries.every((s) => s.data.length === 0);

        chartInstance.setOption({
          title: {
            text: props.title,
            left: "center",
            top: 0,
            textStyle: {
              fontSize: 16,
              fontWeight: "bold",
              color: getTextColor(),  // ✅ 동적 텍스트 색상
            },
          },
          tooltip: {
            trigger: "axis",
            // ✅ PDF 모드일 때 툴팁 배경/텍스트 색상
            backgroundColor: isPdfMode ? 'rgba(255, 255, 255, 0.95)' : undefined,
            textStyle: {
              color: isPdfMode ? '#000000' : undefined,
            },
            formatter: function (params) {
              const rawDate = new Date(params[0].axisValue);
              const yyyy = rawDate.getFullYear();
              const MM = String(rawDate.getMonth() + 1).padStart(2, "0");
              const dd = String(rawDate.getDate()).padStart(2, "0");
              const HH = String(rawDate.getHours()).padStart(2, "0");
              const mm = String(rawDate.getMinutes()).padStart(2, "0");
              const ss = String(rawDate.getSeconds()).padStart(2, "0");
              const formattedTime = `${yyyy}-${MM}-${dd} ${HH}:${mm}:${ss}`;
              let result = formattedTime + "<br/>";

              const sorted = [...params].sort((a, b) => {
                const va = typeof a.data === "number" ? a.data : -Infinity;
                const vb = typeof b.data === "number" ? b.data : -Infinity;
                return vb - va;
              });

              sorted.forEach((item) => {
                const rawValue =
                  typeof item.data === "number" ? item.data : item.value;
                const formatted =
                  typeof rawValue === "number" ? rawValue.toFixed(2) : rawValue;
                result += `${item.marker} ${item.seriesName}: ${formatted}<br/>`;
              });

              return result;
            },
          },
          legend: {
             show: false,
          },
          grid: {
            top: 60,
            left: "3%",
            right: "4%",
            bottom: 30,
            containLabel: true,
          },
          xAxis: {
            type: "category",
            data: props.chartLabels,
            axisLine: { 
              lineStyle: { 
                color: isPdfMode ? '#cccccc' : '#ccc'  // ✅ 축 라인 색상
              } 
            },
            axisLabel: {
              color: getTextColor(),  // ✅ 동적 텍스트 색상
              formatter: function (value) {
                const date = new Date(value);
                const yyyy = date.getFullYear();
                const MM = String(date.getMonth() + 1).padStart(2, "0");
                const dd = String(date.getDate()).padStart(2, "0");
                const HH = String(date.getHours()).padStart(2, "0");
                const mm = String(date.getMinutes()).padStart(2, "0");
                const ss = String(date.getSeconds()).padStart(2, "0");
                return `${yyyy}-${MM}-${dd} ${HH}:${mm}:${ss}`;
              },
            },
          },
          yAxis: {
            type: "value",
            min: minY,
            max: maxY,
            axisLine: { 
              lineStyle: { 
                color: isPdfMode ? '#cccccc' : '#ccc'  // ✅ 축 라인 색상
              } 
            },
            splitLine: { 
              lineStyle: { 
                color: isPdfMode ? '#e5e5e5' : '#eee'  // ✅ 그리드 라인 색상
              } 
            },
            axisLabel: {
              color: getTextColor(),  // ✅ 동적 텍스트 색상
            },
          },
          series: allSeries,
          graphic: isEmpty
            ? [
                {
                  type: "text",
                  left: "center",
                  top: "middle",
                  style: {
                    text: t("trend.Linechart.nodata"),
                    fontSize: 20,
                    fill: isPdfMode ? '#000000' : '#999',  // ✅ No Data 텍스트 색상
                  },
                },
              ]
            : [],
        });
      }
    };

    const disposeChart = () => {
      if (chartInstance) {
        chartInstance.dispose();
        chartInstance = null;
      }
    };

    const resizeChart = () => {
      if (chartInstance) {
        chartInstance.resize();
      }
    };

    onMounted(() => {
      initChart();
      window.addEventListener("resize", resizeChart);
    });

    onBeforeUnmount(() => {
      disposeChart();
      window.removeEventListener("resize", resizeChart);
    });

    watch(
      () => [props.chartData, props.chartLabels],
      () => {
        disposeChart();
        setTimeout(() => {
          initChart();
        }, 0);
      },
      { deep: true }
    );

    watch(locale, () => {
      disposeChart();
      setTimeout(() => {
        initChart();
      }, 0);
    });

    // ✅ PDF 모드나 다크모드 변경 시 차트 다시 그리기 (PDF 모드일 때는 다크모드 변화 무시)
    watch(
      () => [darkMode.value, isPdfMode],
      () => {
        if (!isPdfMode) {  // PDF 모드가 아닐 때만 다크모드 반응
          disposeChart();
          setTimeout(() => {
            initChart();
          }, 0);
        }
      }
    );

    return {
      chartRef,
      t,
    };
  },
};
</script>

<style scoped></style>