<template>
  <div class="grid grid-cols-12 gap-6">
    <div class="col-span-4 flex flex-col gap-6 h-auto">
      <div v-show="true" role="alert">
        <div
          class="flex flex-col w-full px-4 py-2 rounded-lg text-sm bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700/60 text-gray-600 dark:text-gray-400"
        >
          <div class="flex flex-col w-full gap-3">
            <!--div class="flex w-full justify-between items-start"-->
            <div class="flex items-start">
              <svg
                class="shrink-0 fill-current text-violet-500 mt-[3px] mr-3"
                width="16"
                height="16"
                viewBox="0 0 16 16"
              >
                <path
                  d="M8 0C3.6 0 0 3.6 0 8s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8zm1 12H7V7h2v5zM8 6c-.6 0-1-.4-1-1s.4-1 1-1 1 .4 1 1-.4 1-1 1z"
                />
              </svg>
              <div><slot />{{ t("trend.TrendTab.slot") }}.</div>
            </div>
          </div>
          <div class="text-right mt-1">
            <a
              v-if="tap == `Meter`"
              class="font-medium text-violet-500 hover:text-violet-600 dark:hover:text-violet-400"
              href="#0"
              :class="{ 'opacity-50 pointer-events-none': isLoading }"
              @click.prevent="drawMeterChart"
            >
              {{
                isLoading
                  ? t("trend.TrendTab.loading")
                  : t("trend.TrendTab.Plot")
              }}
            </a>
            <a
              v-else-if="tap == `Energy`"
              class="font-medium text-violet-500 hover:text-violet-600 dark:hover:text-violet-400"
              href="#0"
              :class="{ 'opacity-50 pointer-events-none': isLoading }"
              @click.prevent="drawEnergyChart"
            >
              {{
                isLoading
                  ? t("trend.TrendTab.loading")
                  : t("trend.TrendTab.Plot")
              }}
            </a>
            <a
              v-else
              class="font-medium text-violet-500 hover:text-violet-600 dark:hover:text-violet-400"
              href="#0"
              :class="{ 'opacity-50 pointer-events-none': isLoading }"
              @click.prevent="drawDiagnosisChart"
            >
              {{
                isLoading
                  ? t("trend.TrendTab.loading")
                  : t("trend.TrendTab.Plot")
              }}
            </a>
          </div>
        </div>
      </div>

      <Trend_treetable
        v-if="items.length > 0"
        :channel="channel"
        :data="items"
        :expanded="false"
        :checked-ids="checkedIds"
        :checked-names="checkedNames"
        @check-change="onCheckChange"
      />
    </div>

    <div class="col-span-8 relative">
      <div
        v-if="isLoading"
        class="absolute inset-0 bg-white/80 dark:bg-gray-900/80 flex items-center justify-center z-10 rounded-lg"
      >
        <div class="flex flex-col items-center gap-3">
          <svg
            class="animate-spin h-12 w-12 text-violet-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          <p class="text-lg font-medium text-gray-700 dark:text-gray-300">
            {{ t("trend.TrendTab.loading") }}
          </p>
        </div>
      </div>
      <LineChart
        v-if="tap == `Diagnosis`"
        :chart-data="option.lineData"
        :chart-labels="option.lineLabels"
        :chartLastDate="lastDate"
      />
      <LineChart
        v-if="tap == `Meter`"
        :chart-data="meterOption.lineData"
        :chart-labels="meterOption.lineLabels"
        :chartLastDate="lastDate"
      />
      <LineChart
        v-if="tap == `PowerQuality`"
        :chart-data="option.lineData"
        :chart-labels="option.lineLabels"
        :chartLastDate="lastDate"
      />
      <LineChart
        v-if="tap == `Parameters`"
        :chart-data="option.lineData"
        :chart-labels="option.lineLabels"
        :chartLastDate="lastDate"
      />
      <LineChart
        v-if="tap == `Energy`"
        :chart-data="energyOption.lineData"
        :chart-labels="energyOption.lineLabels"
        :chartLastDate="lastDate"
      />
    </div>
  </div>
</template>
<script>
import { ref, onMounted, watch } from "vue";
import axios from "axios";
import Trend_treetable from "./Trend_treetable.vue";
import LineChart from "../../../charts/connect/LineChart01_Echart.vue";
import Notification_origin from "./Notification_origin.vue";
import { useI18n } from "vue-i18n";
export default {
  name: "TrendTab",
  props: {
    startdate: {
      type: Object,
      default: null,
    },
    channel: {
      type: String,
      default: "",
    },
    tap: {
      type: String,
      default: "",
    },
    enddate: {
      type: Object,
      default: null,
    },
    asset: {
      type: String,
      default: "",
    },
  },
  components: {
    LineChart,
    Trend_treetable,
    Notification_origin,
  },
  setup(props) {
    const { t } = useI18n();
    const channel = ref(props.channel);
    const tap = ref(props.tap);
    const items = ref([]);
    const option = ref({
      lineLabels: [],
      lineData: [],
    });
    const meterOption = ref({ lineLabels: [], lineData: [] });
    const energyOption = ref({ lineLabels: [], lineData: [] });
    const pqOption = ref({ lineLabels: [], lineData: [] });
    const checkedIds = ref([]);
    const checkedNames = ref([]);
    const isLoading = ref(false); // ✅ 로딩 상태 추가
    const lastDate = ref("");
    // Meter 탭용 트리 데이터 (Energy 제외)
    const trendTreeData = [
      {
        ID: 1,
        Name: "Temp",
        Title: "Temperature",
        isParent: true,
      },
      { ID: 2, Name: "Freq", Title: "Frequency", isParent: true },
      {
        ID: 3,
        Name: "PF",
        Title: "Power Factor",
        isParent: true,
        children: [
          { ID: 4, Name: "PF1", Title: "Power Factor L1" },
          { ID: 5, Name: "PF2", Title: "Power Factor L2" },
          { ID: 6, Name: "PF3", Title: "Power Factor L3" },
        ],
      },
      {
        ID: 7,
        Name: "linevoltage",
        Title: "Line Voltage",
        isParent: true,
        children: [
          { ID: 8, Name: "Upp1", Title: "Line Voltage L12" },
          { ID: 9, Name: "Upp2", Title: "Line Voltage L23" },
          { ID: 10, Name: "Upp3", Title: "Line Voltage L31" },
          { ID: 11, Name: "Upp4", Title: "Line Voltage Average" },
        ],
      },
      {
        ID: 12,
        Name: "voltage",
        Title: "Phase Voltage",
        isParent: true,
        children: [
          { ID: 13, Name: "U1", Title: "Voltage L1" },
          { ID: 14, Name: "U2", Title: "Voltage L2" },
          { ID: 15, Name: "U3", Title: "Voltage L3" },
        ],
      },
      {
        ID: 16,
        Name: "current",
        Title: "Current",
        isParent: true,
        children: [
          { ID: 17, Name: "I1", Title: "Current L1" },
          { ID: 18, Name: "I2", Title: "Current L2" },
          { ID: 19, Name: "I3", Title: "Current L3" },
        ],
      },
      {
        ID: 20,
        Name: "unbalance",
        Title: "Unbalance",
        isParent: true,
        children: [
          { ID: 21, Name: "Ibal1", Title: "Current Unbalance" },
          { ID: 22, Name: "Ubal1", Title: "Voltage Unbalance" },
        ],
      },
      {
        ID: 23,
        Name: "Power",
        Title: "Power",
        isParent: true,
        children: [
          { ID: 24, Name: "P4", Title: "Active Power" },
          { ID: 25, Name: "Q4", Title: "Reactive Power" },
          { ID: 26, Name: "S4", Title: "Apparent Power" },
        ],
      },
      {
        ID: 31,
        Name: "THD",
        Title: "THD",
        isParent: true,
        children: [
          { ID: 32, Name: "THD_U1", Title: "THD Voltage L1" },
          { ID: 33, Name: "THD_U2", Title: "THD Voltage L2" },
          { ID: 34, Name: "THD_U3", Title: "THD Voltage L3" },
          { ID: 35, Name: "THD_Upp1", Title: "THD Voltage L12" },
          { ID: 36, Name: "THD_Upp2", Title: "THD Voltage L23" },
          { ID: 37, Name: "THD_Upp3", Title: "THD Voltage L31" },
          { ID: 38, Name: "THD_I1", Title: "THD Current L1" },
          { ID: 39, Name: "THD_I2", Title: "THD Current L2" },
          { ID: 40, Name: "THD_I3", Title: "THD Current L3" },
        ],
      },
      {
        ID: 41,
        Name: "TDD",
        Title: "TDD",
        isParent: true,
        children: [
          { ID: 42, Name: "TDD_I1", Title: "TDD Current L1" },
          { ID: 43, Name: "TDD_I2", Title: "TDD Current L2" },
          { ID: 44, Name: "TDD_I3", Title: "TDD Current L3" },
        ],
      },
    ];

    // Energy 탭 전용 트리 데이터
    const energyTreeData = [
      {
        ID: 27,
        Name: "Energy",
        Title: "Energy",
        isParent: true,
        children: [
          { ID: 28, Name: "kwh_import_consumption", Title: "Active Energy" },
          {
            ID: 29,
            Name: "kvarh_import_consumption",
            Title: "Reactive Energy",
          },
          { ID: 30, Name: "kvah_import_consumption", Title: "Apparent Energy" },
        ],
      },
    ];

    const meterParamMap = {
      Temperature: ["Temp"],
      Frequency: ["Freq"],
      "Phase Voltage": ["voltage"],
      "Line Voltage": ["linevoltage"],
      "Line Voltage L12": ["Upp1"],
      "Line Voltage L23": ["Upp2"],
      "Line Voltage L31": ["Upp3"],
      "Line Voltage Average": ["Upp4"],
      Current: ["current"],
      "Current L1": ["I1"],
      "Current L2": ["I2"],
      "Current L3": ["I3"],
      Power: ["Power"],
      "Active Power": ["P4"],
      "Reactive Power": ["Q4"],
      "Apparent Power": ["S4"],
      PF: ["PF"],
      Unbalance: ["unbalance"],
      "Current Unbalance": ["Ibal1"],
      "Voltage Unbalance": ["Ubal1"],
      THD: ["THD"],
      "THD Voltage L1": ["THD_U1"],
      "THD Voltage L2": ["THD_U2"],
      "THD Voltage L3": ["THD_U3"],
      "THD Voltage L12": ["THD_Upp1"],
      "THD Voltage L23": ["THD_Upp2"],
      "THD Voltage L31": ["THD_Upp3"],
      "THD Current L1": ["THD_I1"],
      "THD Current L2": ["THD_I2"],
      "THD Current L3": ["THD_I3"],
      TDD: ["TDD"],
      "TDD I1": ["TDD_I1"],
      "TDD I2": ["TDD_I2"],
      "TDD I3": ["TDD_I3"],
      "TDD Iavg": ["tdd_i_avg"],
    };

    const expandEnabledNames = (enabledParams, paramMap) => {
      const paramNames = enabledParams.flatMap(
        (param) => paramMap[param] || []
      );

      const expanded = new Set(paramNames);

      const treeData = tap.value === "Energy" ? energyTreeData : trendTreeData;

      treeData.forEach((node) => {
        if (node.children && paramNames.includes(node.Name)) {
          node.children.forEach((child) => {
            expanded.add(child.Name);
          });
        }
      });

      return Array.from(expanded);
    };

    const fetchData = async () => {
      try {
        if (tap.value == "Diagnosis") {
          if (props.asset != "") {
            const response = await axios.get(
              `/api/getTrendParameters/${props.asset}/Diagnostic`
            );
            if (response.data.success) {
              items.value = response.data.superlist;
            } else {
              console.log("No Data");
            }
          }
        } else if (tap.value == "PowerQuality") {
          if (props.asset != "") {
            const response = await axios.get(
              `/api/getTrendParameters/${props.asset}/PowerQuality`
            );
            if (response.data.success) {
              items.value = response.data.superlist;
            } else {
              console.log("No Data");
            }
          }
        } else if (tap.value == "Parameters") {
          if (props.asset != "") {
            const response = await axios.get(
              `/api/getTrendParameters/${props.asset}/parameter`
            );
            if (response.data.success) {
              items.value = response.data.superlist;
            } else {
              console.log("No Data");
            }
          }
        } else if (tap.value === "Meter") {
          const response = await axios.get(
            `/api/getTrendParameters/${channel.value}`
          );
          if (response.data.success) {
            const enabledParams = response.data.data.params;
            console.log("enabledParams", enabledParams);
            const filteredParams = enabledParams.filter(
              (param) =>
                ![
                  "Energy",
                  "Active Energy",
                  "Reactive Energy",
                  "Apparent Energy",
                ].includes(param)
            );

            const enabledNames = expandEnabledNames(
              filteredParams,
              meterParamMap
            );

            const deepFilterTree = (nodes) => {
              return nodes
                .map((node) => {
                  const isNodeEnabled = enabledNames.includes(node.Name);

                  if (node.children) {
                    const filteredChildren = node.children.filter((child) =>
                      enabledNames.includes(child.Name)
                    );
                    if (filteredChildren.length > 0 || isNodeEnabled) {
                      return {
                        ...node,
                        children: filteredChildren,
                      };
                    } else {
                      return null;
                    }
                  } else {
                    return isNodeEnabled ? node : null;
                  }
                })
                .filter(Boolean);
            };

            items.value = deepFilterTree(trendTreeData);
          }
        } else if (tap.value === "Energy") {
          items.value = energyTreeData;
        }
      } catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };

    function onCheckChange({
      id,
      checked,
      name,
      children = [],
      childrenNames = [],
    }) {
      if (checked) {
        if (!checkedIds.value.includes(id)) checkedIds.value.push(id);
        children.forEach((cid) => {
          if (!checkedIds.value.includes(cid)) checkedIds.value.push(cid);
        });
        if (!checkedNames.value.includes(name)) checkedNames.value.push(name);
        childrenNames.forEach((cname) => {
          if (!checkedNames.value.includes(cname))
            checkedNames.value.push(cname);
        });
      } else {
        checkedIds.value = checkedIds.value.filter(
          (item) => item !== id && !children.includes(item)
        );
        checkedNames.value = checkedNames.value.filter(
          (item) => item !== name && !childrenNames.includes(item)
        );
      }
      syncParentCheck();
    }

    function syncParentCheck() {
      const traverse = (node) => {
        if (node.children) {
          node.children.forEach(traverse);
          const allChildrenChecked = node.children.every((child) =>
            checkedIds.value.includes(child.ID)
          );
          if (allChildrenChecked) {
            if (!checkedIds.value.includes(node.ID)) {
              checkedIds.value.push(node.ID);
            }
          } else {
            checkedIds.value = checkedIds.value.filter((id) => id !== node.ID);
          }
        }
      };
      items.value.forEach(traverse);
    }

    const formatToISOString = (date, soe) => {
      if (typeof date === "string") {
        date = new Date(date);
      }
      if (!(date instanceof Date) || isNaN(date)) {
        throw new Error("Invalid date");
      }

      const pad = (num, size = 2) => String(num).padStart(size, "0");

      const year = date.getFullYear();
      const month = pad(date.getMonth() + 1);
      const day = pad(date.getDate());
      let hours, minutes, seconds;

      if (soe === 0) {
        hours = pad(0);
        minutes = pad(0);
        seconds = pad(0);
      } else if (soe === 1) {
        hours = pad(23);
        minutes = pad(59);
        seconds = pad(59);
      } else if (soe === 2) {
        hours = pad(0);
        minutes = pad(0);
        seconds = pad(0);
      } else {
        hours = pad(23);
        minutes = pad(59);
        seconds = pad(59);
      }

      const timezoneOffset = -date.getTimezoneOffset();
      const offsetSign = timezoneOffset >= 0 ? "+" : "-";
      const offsetHours = pad(Math.abs(Math.floor(timezoneOffset / 60)));
      const offsetMinutes = pad(Math.abs(timezoneOffset % 60));

      return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}${offsetSign}${offsetHours}:${offsetMinutes}`;
    };

    const drawMeterChart = async () => {
      if (!checkedNames.value || checkedNames.value.length === 0) {
        meterOption.value = { lineLabels: [], lineData: [] };
        return;
      }

      const paramMap = {
        Temp: ["Temp"],
        U1: ["U1"],
        U2: ["U2"],
        U3: ["U3"],
        U4: ["U4"],
        Upp1: ["Upp1"],
        Upp2: ["Upp2"],
        Upp3: ["Upp3"],
        Upp4: ["Upp4"],
        I1: ["I1"],
        I2: ["I2"],
        I3: ["I3"],
        P4: ["P4"],
        Q4: ["Q4"],
        S4: ["S4"],
        Freq: ["Freq"],
        PF1: ["PF1"],
        PF2: ["PF2"],
        PF3: ["PF3"],
        vunbal: ["Ubal1"],
        curunbal: ["Ibal1"],
        THD_U1: ["THD_U1"],
        THD_U2: ["THD_U2"],
        THD_U3: ["THD_U3"],
        THD_Upp1: ["THD_Upp1"],
        THD_Upp2: ["THD_Upp2"],
        THD_Upp3: ["THD_Upp3"],
        THD_I1: ["THD_I1"],
        THD_I2: ["THD_I2"],
        THD_I3: ["THD_I3"],
        TDD_I1: ["TDD_I1"],
        TDD_I2: ["TDD_I2"],
        TDD_I3: ["TDD_I3"],
        Ubal1: ["Ubal1"],
        Ibal1: ["Ibal1"],
      };

      // 선택된 필드들을 하나의 배열로 수집
      let selectedFields = [];
      let actualParamCount = 0;

      checkedNames.value.forEach((param) => {
        const keys = paramMap[param];
        if (keys) {
          actualParamCount += keys.length;
          selectedFields = selectedFields.concat(keys); // 필드 수집
        }
      });

      if (actualParamCount > 6) {
        alert(t("trend.Linechart.metercount"));
        return;
      }

      isLoading.value = true; // ✅ 로딩 시작

      try {
        const url = `/api/getMeterTrend/${channel.value}`;

        // POST 요청으로 변경하고 body에 파라미터 전송
        const response = await axios.post(url, {
          startDate: formatToISOString(props.startdate, 2),
          endDate: formatToISOString(props.enddate, 3),
          fields: selectedFields, // 선택된 필드 배열 전송
        });

        const responseData = response.data.data;
        lastDate.value = response.data.date;
        const datasets = [];
        const labels = [];
        const selectedParams = checkedNames.value;

        labels.push(...responseData.map((row) => row._time));

        // console.log("selectedParams", selectedParams);
        // console.log("selectedFields sent to API:", selectedFields);

        selectedParams.forEach((param) => {
          const keys = paramMap[param];
          if (!keys) return;

          keys.forEach((key) => {
            const data = responseData.map((row) => row[key]);
            datasets.push({
              name: nameToTitleMap[key] || key,
              data: data,
              isThreshold: false,
            });
          });
        });

        meterOption.value = {
          lineLabels: labels,
          lineData: datasets,
        };

        // console.log(
        //   `📊 받은 데이터 수: ${responseData.length}, 필드 수: ${selectedFields.length}`
        // );
      } catch (error) {
        console.error("데이터 가져오기 실패:", error);
        // 에러 메시지 표시 (optional)
        if (error.response?.data?.error) {
          alert(`Error: ${error.response.data.error}`);
        }
      } finally {
        isLoading.value = false; // ✅ 로딩 종료
      }
    };
    const drawEnergyChart = async () => {
      if (!checkedNames.value || checkedNames.value.length === 0) {
        energyOption.value = { lineLabels: [], lineData: [] };
        return;
      }

      isLoading.value = true; // ✅ 로딩 시작

      try {
        let url = `/api/getEnergyTrend/${channel.value}`;
        const response = await axios.get(url, {
          params: {
            startDate: formatToISOString(props.startdate, 2),
            endDate: formatToISOString(props.enddate, 3),
          },
        });

        if (response.data.result) {
          const responseData = response.data.data;
          lastDate.value = response.data.date;
          if (!Array.isArray(responseData)) {
            console.error(
              "Energy 응답 데이터가 배열이 아닙니다:",
              responseData
            );
            energyOption.value = { lineLabels: [], lineData: [] };
            return;
          }

          if (responseData.length === 0) {
            console.warn("Energy 데이터가 비어있습니다");
            energyOption.value = { lineLabels: [], lineData: [] };
            return;
          }

          const datasets = [];
          const labels = [];
          const selectedParams = checkedNames.value;

          try {
            labels.push(...responseData.map((row) => row._time));
          } catch (timeError) {
            console.error("시간 라벨 생성 실패:", timeError);
            energyOption.value = { lineLabels: [], lineData: [] };
            return;
          }

          const energyParamMap = {
            kwh_import_consumption: ["kwh_import_consumption"],
            kvarh_import_consumption: ["kvarh_import_consumption"],
            kvah_import_consumption: ["kvah_import_consumption"],
          };

          selectedParams.forEach((param) => {
            const keys = energyParamMap[param];
            if (!keys) {
              console.warn("Energy 파라미터 매핑을 찾을 수 없음:", param);
              return;
            }

            keys.forEach((key) => {
              try {
                const data = responseData.map((row) => row[key]);
                datasets.push({
                  name: nameToTitleMap[key] || key,
                  data: data,
                  isThreshold: false,
                });
              } catch (dataError) {
                console.error(`Energy 데이터 생성 실패 (${key}):`, dataError);
              }
            });
          });

          energyOption.value = {
            lineLabels: labels,
            lineData: datasets,
          };
        } else {
          console.error("Energy API 응답 실패:", response.data);
          energyOption.value = { lineLabels: [], lineData: [] };
        }
      } catch (error) {
        console.error("Energy 데이터 가져오기 실패:", error);
        energyOption.value = { lineLabels: [], lineData: [] };
      } finally {
        isLoading.value = false; // ✅ 로딩 종료
      }
    };

    function isParentId(id) {
      const findNode = (nodes) => {
        for (const node of nodes) {
          if (node.ID === id) {
            return node.isParent === true;
          }
          if (node.children) {
            const found = findNode(node.children);
            if (found !== undefined) return found;
          }
        }
        return undefined;
      };
      return findNode(items.value) || false;
    }

    function getEffectiveParameterIds() {
      const result = [];

      items.value.forEach((node) => {
        if (node.children && node.children.length > 0) {
          const childIds = node.children.map((c) => c.ID);
          const allChildrenChecked = childIds.every((cid) =>
            checkedIds.value.includes(cid)
          );
          if (allChildrenChecked) {
            result.push(...childIds);
          } else {
            node.children.forEach((c) => {
              if (checkedIds.value.includes(c.ID)) {
                result.push(c.ID);
              }
            });
          }
        } else {
          if (checkedIds.value.includes(node.ID)) {
            result.push(node.ID);
          }
        }
      });

      return result;
    }

    const drawDiagnosisChart = async () => {
      const effectiveIds = getEffectiveParameterIds();

      if (!effectiveIds || effectiveIds.length === 0) {
        option.value = {
          lineLabels: [],
          lineData: [],
        };
        return;
      }

      if (effectiveIds.length > 15) {
        alert(t("trend.Linechart.parametercount"));
        return;
      }

      isLoading.value = true; // ✅ 로딩 시작

      const trendDataRequest = {
        ParametersIds: effectiveIds,
        StartDate: formatToISOString(props.startdate, 0),
        EndDate: formatToISOString(props.enddate, 1),
      };

      try {
        const url = `/api/getTrendData`;
        const response = await axios.post(url, trendDataRequest, {
          headers: { "Content-Type": "application/json" },
        });

        if (response.data.success) {
          console.log("서버 응답 데이터:", response.data.data);
          const resData = response.data.data;
          lastDate.value = response.data.date;
          let datasets = [];
          let labels = [];

          Object.keys(resData).forEach((key) => {
            if (key !== "Thresholds") {
              const dataPoints = resData[key].data;
              if (dataPoints && dataPoints.length > 0) {
                if (labels.length === 0) {
                  labels = dataPoints.map((point) => point.XAxis);
                }
                datasets.push({
                  name: resData[key].Title,
                  data: dataPoints.map((point) => point.YAxis),
                  isThreshold: false,
                });
              }
            }
          });

          if (
            resData.Thresholds &&
            resData.Thresholds.length > 0 &&
            labels.length > 0
          ) {
            const ThresholdString = [
              "Out of Range(Down side)",
              "Repair",
              "Inspect",
              "Warning",
              "Warning",
              "Inspect",
              "Repair",
              "Out of Range(Upper side)",
            ];

            if (resData.Thresholds[0].Thresholds != null) {
              const thresholdCount = resData.Thresholds[0].Thresholds.length;

              for (let idx = 0; idx < thresholdCount; idx++) {
                const hasValidValue = resData.Thresholds.some((t) => {
                  const value = t.Thresholds[idx];
                  return (
                    value !== "NaN" &&
                    value !== null &&
                    value !== undefined &&
                    typeof value === "number"
                  );
                });

                if (!hasValidValue) continue;

                const timeList = resData.Thresholds.filter((t) => {
                  const value = t.Thresholds[idx];
                  return (
                    value !== "NaN" &&
                    value !== null &&
                    value !== undefined &&
                    typeof value === "number"
                  );
                })
                  .map((t) => ({
                    time: new Date(t.XAxis),
                    value: t.Thresholds[idx],
                  }))
                  .sort((a, b) => a.time - b.time);

                if (timeList.length === 0) continue;

                const thresholdData = labels.map((lbl) => {
                  const labelTime = new Date(lbl);

                  let applicableThreshold = timeList[0].value;

                  for (let i = 0; i < timeList.length; i++) {
                    if (labelTime >= timeList[i].time) {
                      applicableThreshold = timeList[i].value;
                    } else {
                      break;
                    }
                  }

                  return applicableThreshold;
                });

                datasets.push({
                  name: ThresholdString[idx],
                  data: thresholdData,
                  isThreshold: true,
                });
              }
            }
          }

          option.value = {
            lineLabels: labels,
            lineData: datasets,
          };
        } else {
          console.error("서버 오류:", response.data.error);
          option.value = {
            lineLabels: [],
            lineData: [],
          };
        }
      } catch (error) {
        console.error("요청 실패:", error);
      } finally {
        isLoading.value = false; // ✅ 로딩 종료
      }
    };

    const nameToTitleMap = {};

    function buildNameToTitleMap(tree) {
      tree.forEach((node) => {
        if (node.children) {
          node.children.forEach((child) => {
            nameToTitleMap[child.Name] = child.Title;
          });
        } else {
          nameToTitleMap[node.Name] = node.Title;
        }
      });
    }

    onMounted(() => {
      fetchData();
      buildNameToTitleMap(trendTreeData);
      buildNameToTitleMap(energyTreeData);
    });

    return {
      t,
      option,
      meterOption,
      energyOption,
      pqOption,
      channel,
      tap,
      items,
      checkedIds,
      checkedNames,
      isLoading, // ✅ 추가
      onCheckChange,
      drawMeterChart,
      drawEnergyChart,
      drawDiagnosisChart,
      trendTreeData,
      lastDate,
    };
  },
};
</script>
