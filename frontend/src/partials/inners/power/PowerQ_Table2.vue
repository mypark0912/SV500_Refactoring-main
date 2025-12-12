<template>
    <div class="overflow-x-auto">
      <!-- DOL: 기존 3상 테이블 -->
      <table v-if="!isVFD" class="table-auto w-full dark:text-white">
        <thead class="text-xs uppercase text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-700 dark:bg-opacity-50 rounded-sm">
          <tr>
            <th class="p-2">
              <div class="font-bold text-left">Harmonics</div>
            </th>
            <th class="p-2">
              <div class="font-bold text-center">L1</div>
            </th>
            <th class="p-2">
              <div class="font-bold text-center">L2</div>
            </th>
            <th class="p-2">
              <div class="font-bold text-center">L3</div>
            </th>
          </tr>
        </thead>
        <tbody class="text-sm font-medium divide-y divide-gray-100 dark:divide-gray-700/60">
          <template v-for="(row, index) in convertedData" :key="index">
            <tr v-if="index > 1">
              <td class="p-2 text-left">{{ index }}</td>
              <td class="p-2 text-center">{{ row.L1 }}</td>
              <td class="p-2 text-center">{{ row.L2 }}</td>
              <td class="p-2 text-center">{{ row.L3 }}</td>
            </tr>
          </template>
        </tbody>
      </table>
  
      <!-- VFD: 단일 값 테이블 -->
      <table v-else class="table-auto w-full dark:text-white">
        <thead class="text-xs uppercase text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-700 dark:bg-opacity-50 rounded-sm">
          <tr>
            <th class="p-2">
              <div class="font-bold text-left">Harmonics</div>
            </th>
            <th class="p-2">
              <div class="font-bold text-center">{{ option === 'voltage' ? 'Voltage (%)' : 'Current (%)' }}</div>
            </th>
          </tr>
        </thead>
        <tbody class="text-sm font-medium divide-y divide-gray-100 dark:divide-gray-700/60">
          <tr v-for="(value, index) in vfdData" :key="index">
            <td class="p-2 text-left">{{ index + 2 }}</td>
            <td class="p-2 text-center">{{ formatValue(value) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script>
  import { ref, computed } from 'vue'
  
  export default {
    name: 'PowerQ_Table',
    props: {
      data: {
        type: [Array, Object],
        default: () => []
      },
      option: {
        type: String,
        required: true
      },
      driveType: {
        type: String,
        default: 'DOL'
      }
    },
    setup(props) {
      const isVFD = computed(() => props.driveType === 'VFD');
  
      const harmonicsMap = {
        "phaseVoltage": ["U1", "U2", "U3"],
        "lineVoltage": ["Upp1", "Upp2", "Upp3"],
        "current": ["I1", "I2", "I3"],
        "voltage": ["U1", "U2", "U3"],  // DOL voltage 옵션용 (w_mode에 따라 다르지만 일단 기본값)
      };
  
      // DOL용 데이터 변환
      const convertedData = computed(() => {
        if (isVFD.value) return [];
        
        const [k1, k2, k3] = harmonicsMap[props.option] || [];
        const L1 = props.data[k1] || [];
        const L2 = props.data[k2] || [];
        const L3 = props.data[k3] || [];
        const rowCount = Math.min(L1.length, L2.length, L3.length);
  
        const rows = [];
        for (let i = 0; i < rowCount; i++) {
          rows.push({
            L1: L1[i],
            L2: L2[i],
            L3: L3[i]
          });
        }
        return rows;
      });
  
      // VFD용 데이터
      const vfdData = computed(() => {
        if (!isVFD.value) return [];
        
        if (props.option === 'voltage') {
          return props.data.voltage || [];
        } else if (props.option === 'current') {
          return props.data.current || [];
        }
        return [];
      });
  
      // 값 포맷팅 (소수점 2자리)
      const formatValue = (value) => {
        if (value === null || value === undefined || isNaN(value)) return '-';
        return Number(value).toFixed(2);
      };
  
      return {
        isVFD,
        convertedData,
        vfdData,
        formatValue,
      }
    }
  }
  </script>