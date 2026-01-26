<template>
  <div class="overflow-x-auto">
    <table class="table-auto w-full dark:text-white">
      <!-- Table header -->
      <thead class="text-xs uppercase text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-700 dark:bg-opacity-50 rounded-sm">
        <tr>
          <th class="p-2">
            <div class="font-bold text-left">Harmonics</div>
          </th>
          <!-- VFD: 1열, DOL: 3열 -->
          <template v-if="driveType === 'VFD'">
            <th class="p-2">
              <div class="font-bold text-center">{{ isVoltage ? 'Voltage' : 'Current' }}</div>
            </th>
          </template>
          <template v-else>
            <th class="p-2">
              <div class="font-bold text-center">L1</div>
            </th>
            <th class="p-2">
              <div class="font-bold text-center">L2</div>
            </th>
            <th class="p-2">
              <div class="font-bold text-center">L3</div>
            </th>
          </template>
        </tr>
      </thead>
      <!-- Table body -->
      <tbody class="text-sm font-medium divide-y divide-gray-100 dark:divide-gray-700/60">
        <template v-for="(row, index) in convertedData" :key="index">
          <!-- VFD: 모든 행 표시, DOL: index > 1 부터 -->
          <tr v-if="driveType === 'VFD' || index > 1">
            <!-- VFD: index + 2 (2차부터), DOL: index (원본 인덱스가 차수) -->
            <td class="p-2 text-left">{{ driveType === 'VFD' ? index + 2 : index }}</td>
            <template v-if="driveType === 'VFD'">
              <td class="p-2 text-center">{{ row.value }}</td>
            </template>
            <template v-else>
              <td class="p-2 text-center">{{ row.L1 }}</td>
              <td class="p-2 text-center">{{ row.L2 }}</td>
              <td class="p-2 text-center">{{ row.L3 }}</td>
            </template>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'PowerQ_Table',
  props: {
    data: {
      type: [Array, Object],
      default: () => ({})
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
    // DOL용 매핑
    const harmonicsMap = {
      "phaseVoltage": ["U1", "U2", "U3"],
      "lineVoltage": ["Upp1", "Upp2", "Upp3"],
      "current": ["I1", "I2", "I3"]
    };

    // VFD용 Voltage 체크 (대소문자 모두 대응)
    const isVoltage = computed(() => {
      return props.option === 'Voltage' || props.option === 'voltage';
    });

    const convertedData = computed(() => {
      // VFD 처리
      if (props.driveType === 'VFD') {
        const dataArray = isVoltage.value
          ? props.data.voltage 
          : props.data.current;
        
        if (!Array.isArray(dataArray)) return [];
        
        return dataArray.map((value) => ({
          value: value
        }));
      }
      
      // DOL 처리
      const [k1, k2, k3] = harmonicsMap[props.option] || harmonicsMap.phaseVoltage;
      const L1 = props.data[k1] || [];
      const L2 = props.data[k2] || [];
      const L3 = props.data[k3] || [];
      const rowCount = Math.max(L1.length, L2.length, L3.length);

      const rows = [];
      for (let i = 0; i < rowCount; i++) {
        rows.push({
          L1: L1[i] ?? '-',
          L2: L2[i] ?? '-',
          L3: L3[i] ?? '-'
        });
      }
      return rows;
    });

    return {
      convertedData,
      isVoltage,
    }
  }
}
</script>