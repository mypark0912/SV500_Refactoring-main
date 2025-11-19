<template>
    <div
      class="relative col-span-full xl:col-span-8 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg"
    >
      <div
        class="absolute top-0 left-0 right-0 h-0.5 bg-orange-500"
        aria-hidden="true"
      ></div>
      <div
        class="px-5 pt-5 pb-6 border-b border-gray-200 dark:border-gray-700/60"
      >
        <header class="flex items-center mb-2">
          <div class="w-6 h-6 rounded-full shrink-0 bg-orange-500 mr-3">
            <svg
              class="w-6 h-6 fill-current text-white"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle
                cx="17"
                cy="17"
                r="4"
                stroke="currentColor"
                stroke-width="2"
                fill="none"
              />
              <path
                d="M20 20l2 2"
                stroke="currentColor"
                stroke-width="2"
                fill="none"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
          <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">
            AI Module MODBUS Configuration
          </h3>
        </header>
      </div>
  
      <div class="px-4 py-3 space-y-4">
        <!-- 버튼 영역 - 탭처럼 패널 밖에 배치 -->
        <div class="flex space-x-2">
          <button
            @click="addRow"
            class="px-3 py-1.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            + Add Row
          </button>
          <button
            @click="handleReset"
            class="px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-violet-500"
          >
            Reset
          </button>
        </div>
  
        <div
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700/60"
        >
          <!-- 테이블 -->
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b-2 border-gray-300 dark:border-gray-600">
                  <th class="px-2 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50 w-14">
                    Index
                  </th>
                  <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">
                    Address
                  </th>
                  <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">
                    FC
                  </th>
                  <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">
                    Start Addr.
                  </th>
                  <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">
                    Read<br>Count
                  </th>
                  <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">
                    Dest. ID
                  </th>
                  <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">
                    Dest. Src
                  </th>
                  <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">
                    Period<br>(ms)
                  </th>
                  <th class="px-2 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50 w-20">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, idx) in modbusConfig"
                  :key="row.id"
                  class="border-b border-gray-200 dark:border-gray-700/60 hover:bg-gray-50 dark:hover:bg-gray-700/30"
                >
                  <td class="px-2 py-2 text-center text-xs text-gray-800 dark:text-gray-200 font-medium">
                    {{ idx + 1 }}
                  </td>
                  <td class="px-2 py-2 text-center">
                    <input
                      type="number"
                      v-model.number="row.address"
                      class="w-16 px-1.5 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500"
                      min="0"
                      max="255"
                    />
                  </td>
                  <td class="px-2 py-2 text-center">
                    <select
                      v-model.number="row.fc"
                      class="w-16 px-1 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500"
                    >
                      <option :value="0">-</option>
                      <option :value="1">01</option>
                      <option :value="2">02</option>
                      <option :value="3">03</option>
                      <option :value="4">04</option>
                      <option :value="5">05</option>
                      <option :value="6">06</option>
                      <option :value="15">15</option>
                      <option :value="16">16</option>
                    </select>
                  </td>
                  <td class="px-2 py-2 text-center">
                    <input
                      type="number"
                      v-model.number="row.startAddr"
                      class="w-20 px-1.5 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500"
                      min="0"
                    />
                  </td>
                  <td class="px-2 py-2 text-center">
                    <input
                      type="number"
                      v-model.number="row.readCount"
                      class="w-16 px-1.5 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500"
                      min="0"
                    />
                  </td>
                  <td class="px-2 py-2 text-center">
                    <input
                      type="number"
                      v-model.number="row.destId"
                      class="w-16 px-1.5 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500"
                      min="0"
                    />
                  </td>
                  <td class="px-2 py-2 text-center">
                    <input
                      type="number"
                      v-model.number="row.destSrc"
                      class="w-16 px-1.5 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500"
                      min="0"
                    />
                  </td>
                  <td class="px-2 py-2 text-center">
                    <input
                      type="number"
                      v-model.number="row.period"
                      class="w-20 px-1.5 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500"
                      min="0"
                      step="100"
                    />
                  </td>
                  <td class="px-2 py-2 text-center">
                    <button
                      @click="removeRow(idx)"
                      :disabled="modbusConfig.length <= 1"
                      class="px-2 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                      title="Delete row"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
  
          <!-- 설명 -->
          <div class="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
            <p class="text-xs text-blue-800 dark:text-blue-200">
              <strong>Note:</strong> 
              • FC: Function Code (03=Read Holding Registers, 04=Read Input Registers, 16=Write Multiple Registers, etc.)
              <br>
              • Dest. ID: Destination device ID for write operations
              <br>
              • Dest. Src: Starting address in destination memory for write operations
            </p>
          </div>
  
          <!-- 하단 정보 -->
          <div class="flex justify-between items-center mt-6">
            <div class="text-sm text-gray-600 dark:text-gray-400">
              Total Configurations: <span class="font-semibold">{{ modbusConfig.length }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from "vue";
  
  // 고유 ID 생성용 카운터
  let nextId = 3;
  
  // Modbus 설정 데이터 (초기 2개)
  const modbusConfig = ref([
    { id: 1, address: 100, fc: 3, startAddr: 14, readCount: 28, destId: 3, destSrc: 0, period: 1000 },
    { id: 2, address: 100, fc: 3, startAddr: 90, readCount: 12, destId: 3, destSrc: 28, period: 1000 },
  ]);
  
  // 행 추가
  const addRow = () => {
    modbusConfig.value.push({
      id: nextId++,
      address: 0,
      fc: 0,
      startAddr: 0,
      readCount: 0,
      destId: 0,
      destSrc: 0,
      period: 1000
    });
  };
  
  // 행 삭제
  const removeRow = (index) => {
    if (modbusConfig.value.length > 1) {
      modbusConfig.value.splice(index, 1);
    }
  };
  
  // 초기값으로 리셋
  const handleReset = () => {
    if (confirm('Are you sure you want to reset to default configuration?')) {
      nextId = 3;
      modbusConfig.value = [
        { id: 1, address: 100, fc: 3, startAddr: 14, readCount: 28, destId: 3, destSrc: 0, period: 1000 },
        { id: 2, address: 100, fc: 3, startAddr: 90, readCount: 12, destId: 3, destSrc: 28, period: 1000 },
      ];
      console.log('Configuration reset to default values');
    }
  };
  
  // 저장
  const handleSave = () => {
    // 유효성 검사
    const invalidRows = modbusConfig.value.filter((row, idx) => {
      if (row.fc > 0 && (row.address === 0 || row.startAddr < 0 || row.readCount <= 0)) {
        return true;
      }
      return false;
    });
  
    if (invalidRows.length > 0) {
      alert('Please check invalid configurations. Address, Start Address and Read Count must be valid when FC is set.');
      return;
    }
  
    console.log('Saving configuration:', modbusConfig.value);
    
    // API 호출 예시
    // await saveModbusConfig(modbusConfig.value);
    
    alert('Configuration saved successfully!');
  };
  </script>
  
  <style scoped>
  input[type="number"]:focus,
  select:focus {
    outline: none;
  }
  
  /* 숫자 입력 필드의 스피너 제거 */
  input[type="number"]::-webkit-inner-spin-button,
  input[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }
  
  input[type="number"] {
    -moz-appearance: textfield;
  }
  </style>