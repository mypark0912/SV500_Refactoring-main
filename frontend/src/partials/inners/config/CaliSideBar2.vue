<template>
  <div
    class="flex flex-nowrap overflow-x-scroll no-scrollbar md:block md:overflow-auto px-3 py-4 border-b md:border-b-0 md:border-l border-gray-200 dark:border-gray-700/60 md:space-y-2"
  >
    <!-- Channel Selection Group -->
    <div
      class="flex flex-col gap-1.5 border-b border-gray-200 dark:border-gray-700/60 pb-3 mb-3"
    >
      <div
        class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase"
      >
        Channel Selection
      </div>
      <div class="flex gap-3">
        <label
          class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/30 p-1 rounded transition-colors"
        >
          <input
            type="checkbox"
            v-model="showMainChannel"
            @change="handleMainChannelChange"
            class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
          />
          <span class="text-xs font-medium text-gray-700 dark:text-gray-300"
            >Main Channel</span
          >
        </label>
        <label
          class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/30 p-1 rounded transition-colors"
        >
          <input
            type="checkbox"
            v-model="showSubChannel"
            @change="handleSubChannelChange"
            class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
          />
          <span class="text-xs font-medium text-gray-700 dark:text-gray-300"
            >Sub Channel</span
          >
        </label>
      </div>
    </div>
    
    <!-- Setting Group -->
    <div
      class="flex flex-col gap-2 border-b border-gray-200 dark:border-gray-700/60 pb-3 mb-3"
    >
      <div
        class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase"
      >
        Setting
      </div>
      
      <!-- Serial Number -->
      <div class="flex flex-col gap-1">
        <label
          for="reference"
          class="text-xs font-bold text-gray-700 dark:text-gray-300"
        >
          Serial Number
        </label>
        <input
          class="h-9 w-full p-2 text-xs border border-gray-300 rounded-md"
          type="text" v-model="macAddr"
          disabled
        />
      </div>
      
      <!-- Select Setup with Upload button -->
      <div class="flex flex-col gap-1">
        <label
          for="selectItem"
          class="text-xs font-bold text-gray-700 dark:text-gray-300"
        >
          Select Setup
        </label>
        <div class="flex gap-2">
          <select
            id="selectItem"
            class="h-9 flex-1 p-2 text-xs border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
            v-model="selectSetup"
          >
            <option
              v-for="(setup, index) in select_setupList"
              :key="index"
              :value="index"
            >
              {{ setup.item }}
            </option>
          </select>
          <button
            class="h-9 px-4 text-xs bg-gray-900 text-white rounded-md hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white"
            @click="showUploadModal = true"
          >
            Upload
          </button>
          <button
            class="h-9 px-4 text-xs bg-gray-600 text-white rounded-md hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white"
            @click="applySetup"
          >
            Apply
          </button>
        </div>
      </div>
      
      <!-- Upload status message -->
      <div v-if="message" class="font-medium text-xs text-gray-800 dark:text-gray-100">
        {{ message }}🙌
      </div>
    </div>
    
    <!-- Time & ErrorLimit -->
    <div
  class="flex flex-col gap-2 border-b border-gray-200 dark:border-gray-700/60 pb-3 mb-3"
>
  <div
    class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase"
  >
    DateTime
  </div>
  
  <!-- 장비 시간 표시 -->
  <div v-if="deviceTime" class="p-2 bg-gray-50 dark:bg-gray-700 rounded-md">
    <div class="text-xs font-mono font-semibold text-gray-800 dark:text-gray-100">
      <span>{{ timemode }} </span> {{ deviceTime }}
    </div>
  </div>
  
  <!-- Get Time, Set Time 버튼 -->
  <div class="flex gap-2">
    <button
      id="getTimeBtn"
      @click="getTime"
      class="flex-1 h-9 w-24 text-xs bg-gray-600 text-white rounded-md hover:bg-gray-700 flex items-center justify-center gap-1"
    >
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>Get Time</span>
    </button>
    <button
      id="syncTimeBtn"
      @click="syncSystemTime"
      class="flex-1 h-9 w-24 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center justify-center gap-1"
    >
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>Set Time</span>
    </button>
  </div>
</div>
    
    <!-- Reference -->
    <div
  class="flex flex-col gap-2 border-b border-gray-200 dark:border-gray-700/60 pb-3 mb-3"
>
  <div
    class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase"
  >
    Reference
  </div>
  
  <!-- 첫 번째 줄: U Ref, I Ref, In Ref -->
  <div class="grid grid-cols-3 gap-1">
    <div class="flex flex-col gap-0.5">
      <label
        for="uRef"
        class="text-xs font-bold text-gray-700 dark:text-gray-300"
      >
        U ref
      </label>
      <input
        id="uRef"
        v-model.number="refDict.U"
        type="text"
        class="h-8 w-20 px-1.5 text-xs rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
      />
    </div>
    <div class="flex flex-col gap-0.5">
      <label
        for="iRef"
        class="text-xs font-bold text-gray-700 dark:text-gray-300"
      >
        I Ref
      </label>
      <input
        id="iRef"
        v-model.number="refDict.I"
        type="text"
        class="h-8 w-20 px-1.5 text-xs rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
      />
    </div>
    <div class="flex flex-col gap-0.5">
      <label
        for="inRef"
        class="text-xs font-bold text-gray-700 dark:text-gray-300"
      >
        In Ref
      </label>
      <input
        id="inRef"
        type="text"
        v-model.number="refDict.In"
        class="h-8 w-20 px-1.5 text-xs rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
      />
    </div>
  </div>
  
  <!-- 두 번째 줄: Phase Angle, Error Limit -->
  <div class="grid grid-cols-3 gap-1">
  <div class="flex flex-col gap-0.5">
    <label
      for="phaseAngle"
      class="text-xs font-bold text-gray-700 dark:text-gray-300"
    >
      Phase Angle
    </label>
    <input
      id="phaseAngle"
      type="text"
      v-model.number="refDict.P"
      class="h-8 w-20 px-1.5 text-xs rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
    />
  </div>
  <div class="flex flex-col gap-0.5">
    <label
      for="errorLimit"
      class="text-xs font-bold text-gray-700 dark:text-gray-300"
    >
      Error Limit
    </label>
    <input
      id="errorLimit"
      v-model.number="errorLimit"
      type="text"
      class="h-8 w-20 px-1.5 text-xs rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
    />
  </div>
  <!-- Action 버튼 (div로 감싸기) -->
  <div class="flex flex-col gap-0.5">
    <label
      for="sa"
      class="text-xs font-bold text-gray-700 dark:text-gray-300"
    >
      Action
    </label>
    <button
      class="h-8 px-2 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
      @click="sendRef"
    >
      Send
    </button>
  </div>
</div>
</div>
    
    <!-- Command -->
    <div
      class="flex flex-col gap-2 border-b border-gray-200 dark:border-gray-700/60 pb-3 mb-3"
    >
      <div
        class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase"
      >
        Command
      </div>
      <div v-if="cmdMessage" class="font-medium text-xs text-gray-800 dark:text-gray-100">
        {{ cmdMessage }}🙌
      </div>
      <div class="grid grid-cols-2 gap-1.5">
        <button
          v-for="(row, index) in commands"
          class="text-xs dark:hover:bg-white"
          :class="btnClass(index)"
          @click="sendCmd(index)"
        >
          {{ row.Label }}
        </button>
      </div>
    </div>
    
    <!-- Bottom buttons -->
    <section class="grid grid-cols-2 gap-2 pt-1">
      <button
        class="h-9 px-3 text-xs font-semibold bg-gradient-to-r from-gray-700 to-gray-900 hover:from-gray-800 hover:to-black text-white rounded-lg shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-200"
        @click="SaveCal"
        >
        <span class="flex items-center justify-center gap-1.5">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V2"></path>
          </svg>
          Save
        </span>
      </button>

      <!-- @click="showReportModal = true" -->
      <button
      
        class="h-9 px-3 text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-200"
      >
        <span class="flex items-center justify-center gap-1.5">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
          </svg>
          Send Report
        </span>
      </button>
          <!-- Send Report Modal -->
      <SendReportModal
        :isOpen="showReportModal"
        :reportData="reportData"
        @close="showReportModal = false"
        @send="handleSend"
      />
    </section>
    
    <!-- Upload Modal -->
    <Teleport to="body">
      <div v-if="showUploadModal" class="fixed inset-0 z-50 overflow-y-auto">
        <!-- Backdrop -->
        <div 
          class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          @click="showUploadModal = false"
        ></div>
        
        <!-- Modal -->
        <div class="flex min-h-full items-center justify-center p-4">
          <div class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
            <!-- Modal Header -->
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Upload Setting File
              </h3>
              <button
                @click="showUploadModal = false"
                class="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
            
            <!-- Modal Body -->
            <div class="space-y-4">
              <!-- File input area -->
              <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
                <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  Click to upload or drag and drop
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-500">
                  Setting files only
                </p>
                <input
                  type="file"
                  class="hidden"
                  ref="fileInput"
                  @change="handleFileUpload"
                />
                <button
                  @click="$refs.fileInput.click()"
                  class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                >
                  Choose File
                </button>
              </div>
              
              <!-- Selected file display -->
              <div v-if="selectedFile" class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="flex items-center">
                  <svg class="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
                  </svg>
                  <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    {{ selectedFile.name }}
                  </span>
                </div>
                <button
                  @click="selectedFile = null"
                  class="text-red-500 hover:text-red-700"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
            
            <!-- Modal Footer -->
            <div class="mt-6 flex justify-end gap-3">
              <button
                @click="showUploadModal = false"
                class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-700 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                @click="uploadFromModal"
                :disabled="!selectedFile"
                class="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                Upload
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, inject, onUnmounted } from "vue";
import axios from "axios";
import { useSetupStore } from "@/store/setup";
import SendReportModal from './Sendreportmodal.vue';
export default {
  name: "CaliSidebar",
  props: ["commands"],
    components: {
    SendReportModal
  },
  emits: ['startPolling', 'stopPolling'],
  setup(props, { emit }) {
    const setupStore = useSetupStore();
    const selectedFile = ref(null);
    const message = ref("");
    const setupList = ref([]);
    const macAddr = ref('');
    const commands = ref([]);
    const select_setupList = ref([]);
    const selectSetup = ref(-1);
    const errorLimit = ref(0);
    const showUploadModal = ref(false);
    const showMainChannel = inject("showMainChannel", ref(true));
    const showSubChannel = inject("showSubChannel", ref(true));
    const deviceTime = ref('');
    const timemode = ref('');
    const cmdMessage = ref('');
    //let updateInterval = null;
    // Channel selection handlers
    const handleMainChannelChange = () => {
      if (!showMainChannel.value && !showSubChannel.value) {
        showMainChannel.value = true;
      }
    };

    const handleSubChannelChange = () => {
      if (!showSubChannel.value && !showMainChannel.value) {
        showSubChannel.value = true;
      }
    };
    const reportInfo = ref({
      tester: '',
      approver: '',
      sn: '',
      manufactureDate: '',
      StandardEquipmentName: '',
      Uncertainty: '',
      frequency: ''
    });

    const showReportModal = ref(false);
    const handleSend = (data) => {
        try {
        // CSV 데이터 생성
        const csvContent = generateCSV();
        console.log(csvContent);
        // Blob 생성 및 다운로드
        const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        // 파일명 생성 (날짜 포함)
        const now = new Date();
        const dateStr = now.toISOString().split('T')[0].replace(/-/g, '');
        const fileName = `TestReport_${dateStr}.csv`;
        
        link.setAttribute('href', url);
        link.setAttribute('download', fileName);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        alert('CSV 파일이 다운로드되었습니다.');
        showReportModal.value = false;
      } catch (error) {
        console.error('CSV 다운로드 실패:', error);
        alert('CSV 다운로드 중 오류가 발생했습니다.');
      }
      console.log('전송 버튼 눌림!', data);
      // 여기서 원하는 작업 수행
    };


 // CSV 생성 함수 (더미 데이터)
    const generateCSV = () => {
      let csv = '';
      
      // 제목
      csv += `${reportInfo.value.modelName} 시험 성적서\n\n`;
      
      // 1. 기본 정보
      csv += '1. 기본 정보 (Basic Information)\n';
      csv += `성적서 번호,${reportInfo.value.reportNumber}\n`;
      csv += `시험일자,${reportInfo.value.testDate}\n`;
      csv += `시험자,${reportInfo.value.tester}\n`;
      csv += `승인자,${reportInfo.value.approver}\n\n`;
      
      // 2. 피시험기기 정보
      csv += '2. 피시험기기 정보\n';
      csv += `모델명,${reportInfo.value.modelName}\n`;
      csv += `시리얼번호,${reportInfo.value.serialNumber}\n`;
      csv += `제조일자,${reportInfo.value.manufactureDate}\n\n`;
      
      // 3. 시험 조건
      csv += '3. 시험 조건\n';
      csv += '항목,값\n';
      csv += `정격전압,${reportInfo.value.ratedVoltage}\n`;
      csv += `정격전류,${reportInfo.value.ratedCurrent}\n`;
      csv += `주파수,${reportInfo.value.frequency}\n`;
      csv += `역률,cosφ=0.5 지상\n\n`;
      
      // 4. 표준기기
      csv += '4. 표준기기\n';
      csv += '장비명,모델명,불확도\n';
      csv += '전압전류 발생기,ZERA,±0.1\n\n';
      
      // 더미 데이터 생성 함수
      const generateDummyData = (standard, variation = 0.3) => {
        // 표준값 기준으로 ±variation% 범위의 랜덤 측정값 생성
        const measured = standard * (1 + (Math.random() * variation * 2 - variation) / 100);
        const error = ((measured - standard) / standard * 100).toFixed(2);
        const pass = Math.abs(error) <= errorLimit.value ? '적합' : '부적합';
        return { measured: measured.toFixed(2), error, pass };
      };
      
      // 5. 전압 정밀도 시험
      csv += '5. 전압 정밀도 시험\n';
      csv += '위상,표준값 (V),측정값 (V),오차 (%),허용오차 (%),판정\n';
      const voltageStandard = refDict.value.U;
      ['L1', 'L2', 'L3'].forEach(phase => {
        const data = generateDummyData(voltageStandard);
        csv += `${phase},${voltageStandard},${data.measured},${data.error},${errorLimit.value},${data.pass}\n`;
      });
      csv += '\n';
      
      // 6. 전류 정밀도 시험
      csv += '6. 전류 정밀도 시험\n';
      csv += '위상,표준값 (A),측정값 (A),오차 (%),허용오차 (%),판정\n';
      const currentStandard = refDict.value.I * 5;
      ['L1', 'L2', 'L3'].forEach(phase => {
        const data = generateDummyData(currentStandard);
        csv += `${phase},${currentStandard},${data.measured},${data.error},${errorLimit.value},${data.pass}\n`;
      });
      csv += '\n';
      
      // 7. 유효전력 정밀도 시험
      csv += '7. 유효전력 정밀도 시험\n';
      csv += '위상,표준값 (W),측정값 (W),오차 (%),허용오차 (%),판정\n';
      const activePowerStandard = refDict.value.U * refDict.value.I * 5 * 0.5; // P = U * I * cosφ
      ['L1', 'L2', 'L3'].forEach(phase => {
        const data = generateDummyData(activePowerStandard, 0.4);
        csv += `${phase},${activePowerStandard.toFixed(0)},${parseFloat(data.measured).toFixed(0)},${data.error},${errorLimit.value},${data.pass}\n`;
      });
      csv += '\n';
      
      // 8. 무효전력 정밀도 시험
      csv += '8. 무효전력 정밀도 시험\n';
      csv += '위상,표준값 (var),측정값 (var),오차 (%),허용오차 (%),판정\n';
      const reactivePowerStandard = Math.round(refDict.value.U * refDict.value.I * 5 * Math.sin(Math.acos(0.5))); // Q = U * I * sinφ
      ['L1', 'L2', 'L3'].forEach(phase => {
        const data = generateDummyData(reactivePowerStandard, 0.4);
        csv += `${phase},${reactivePowerStandard},${parseFloat(data.measured).toFixed(0)},${data.error},${errorLimit.value},${data.pass}\n`;
      });
      csv += '\n';
      
      // 9. 피상전력 정밀도 시험
      csv += '9. 피상전력 정밀도 시험 cosφ = 0.5 지상\n';
      csv += '위상,표준값 (VA),측정값 (VA),오차 (%),허용오차 (%),판정\n';
      const apparentPowerStandard = refDict.value.U * refDict.value.I * 5; // S = U * I
      ['L1', 'L2', 'L3'].forEach(phase => {
        const data = generateDummyData(apparentPowerStandard, 0.4);
        csv += `${phase},${apparentPowerStandard.toFixed(0)},${parseFloat(data.measured).toFixed(0)},${data.error},${errorLimit.value},${data.pass}\n`;
      });
      csv += '\n';
      
      // 10. 종합 판정
      csv += '10. 종합 판정 (Overall Assessment)\n';
      csv += '시험항목,판정,비고\n';
      csv += '전압 정밀도,☑ 적합 □ 부적합,\n';
      csv += '전류 정밀도,☑ 적합 □ 부적합,\n';
      csv += '유효전력 정밀도,☑ 적합 □ 부적합,\n';
      csv += '무효전력 정밀도,☑ 적합 □ 부적합,\n';
      csv += '피상전력 정밀도,☑ 적합 □ 부적합,\n\n';
      
      csv += '\n';
      csv += '최종 판정:,☑ 적합 □ 부적합\n';
      csv += '시험자:,,,승인자:\n';
      csv += '_________________ (서명/날짜),,,_________________ (서명/날짜)\n';
      
      return csv;
    };






    const refDict = ref({
      U: 0,
      I: 0,
      In: 0,
      P: 0,
      Error: 0,
    });

    onMounted(() => {
      commands.value = props.commands;
    });

    const btnClass = (index) => {
      if (index % 2 == 0)
        return "h-9 bg-green-900 text-white rounded-md hover:bg-green-800 dark:bg-green-100 dark:text-green-800 dark:hover:bg-white";
      else
        return "h-9 bg-pink-900 text-white rounded-md hover:bg-pink-800 dark:bg-pink-100 dark:text-pink-800 dark:hover:bg-white";
    };

    const sendRef = async() =>{
      refDict.value["Error"] = errorLimit.value
      if (Object.values(refDict.value).every(val => val === 0)) {
          alert("모든 값이 0입니다. 최소 하나 이상의 값을 입력해주세요.");
          return;
        }
        try {
            const response = await axios.post(`/config/calibrate/saveRef`, refDict.value, {
              headers: { "Content-Type": "application/json" },
            });
            if (response.data.passOK == "1") {
              alert("Ref Save Success");
            } else {
              alert(response.data.error);
            }
          } catch (error) {
            alert(error);
          }
    }

    const sendCmd = async (index) => {
      if (index == 0) {
        try {
          const response = await axios.get("/config/calibrate/start");
          if (response.data.passOK == "1") {
            cmdMessage.value = commands.value[index]["name"] + " Success";
            emit('startPolling');
          } else {
            cmdMessage.value = response.data.error;
          }
        } catch (error) {
          cmdMessage.value = error;
        }
      } else if (index == 1) {
        try {
          const response = await axios.get("/config/calibrate/end");
          if (response.data.passOK == "1") {
            cmdMessage.value = commands.value[index]["name"] + " Success";
            emit('stopPolling');
          } else {
            cmdMessage.value = response.data.error;
          }
        } catch (error) {
          cmdMessage.value = error;
        }
      } else {
        let data = {};
        if ("Param" in commands.value[index]) {
          data["param"] = commands.value[index]["Param"];
          if(data["param"].includes(",")){
            data["ref1"] =  refDict.value["U"].toString();
            data["ref2"] =  refDict.value["I"].toString();
          }else{
            data["ref1"] = refDict.value[commands.value[index]["Param"]].toString();
            data["ref2"] = "None";
          }
          
        } else {
          data["param"] = "None";
          data["ref1"] = "None";
          data["ref2"] = "None";
        }
        data["cmd"] = commands.value[index]["name"];
        data["cmdnum"] = commands.value[index]["number"];
        if (showMainChannel.value && showSubChannel.value) {
          data["channel"] = "Both";
        } else if (showMainChannel.value) {
          data["channel"] = "Main";
        } else if (showSubChannel.value) {
          data["channel"] = "Sub";
        }
        data["type"] = commands.value[index]["Type"];

        try {
          const response = await axios.post(`/config/calibrate/cmd`, data, {
            headers: { "Content-Type": "application/json" },
          });
          if (response.data.passOK == "1") {
            alert(commands.value[index]["name"] + " Success");
            cmdMessage.value = commands.value[index]["name"] + " Success"
          } else {
            cmdMessage.value = response.data.error;
          }
        } catch (error) {
          cmdMessage.value = error;
        }
      }
    };

    const SaveCal = async() =>{
      let data = {};
      data["param"] = "None";
      data["ref1"] = "None";
      data["ref2"] = "None";
      data["cmd"] = "CAL_SAVE"
      data["cmdnum"] = 99
      if (showMainChannel.value && showSubChannel.value) {
          data["channel"] = "Both";
        } else if (showMainChannel.value) {
          data["channel"] = "Main";
        } else if (showSubChannel.value) {
          data["channel"] = "Sub";
        }
        data["type"] = "SAVE"
        try {
          const response = await axios.post(`/config/calibrate/cmd`, data, {
            headers: { "Content-Type": "application/json" },
          });
          if (response.data.passOK == "1") {
            alert("Save Success");
          } else {
            alert(response.data.error);
          }
        } catch (error) {
          alert(error);
        }
    };

    // const SetTime = () => {
    //   const now = new Date();
    //   const year = now.getFullYear();
    //   const month = String(now.getMonth() + 1).padStart(2, '0');
    //   const day = String(now.getDate()).padStart(2, '0');
    //   const hours = String(now.getHours()).padStart(2, '0');
    //   const minutes = String(now.getMinutes()).padStart(2, '0');
    //   const seconds = String(now.getSeconds()).padStart(2, '0');
      
    //   const pcTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    //   console.log("PC Time:", pcTime);
      
    //   // 나중에 여기서 서버로 시간을 전송
    //   // axios.post('/config/synctime', { time: pcTime });
    // };
    const syncSystemTime = async () => {
      try {
        // 브라우저 현재 시간 가져오기
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        
        const pcTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        console.log("PC Time:", pcTime);
        
        // 타임존 가져오기
        const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        console.log("Timezone:", timeZone);
        
        // FastAPI로 전송
        const response = await axios.post('/config/calibrate/setSystemTime', {
          datetime_str: pcTime,
          timezone: timeZone || "Asia/Seoul"
        });
        if (response.data.success){
          timemode.value = 'SetTime -';
          deviceTime.value = response.data.current_time;
        }
        
      } catch (error) {
        console.error("시간 동기화 실패:", error);
        alert("시간 설정 실패: " + error.message);
      }
    };

    const handleFileUpload = (event) => {
      selectedFile.value = event.target.files[0];
    };

    const upload = async () => {
      if (!selectedFile.value) {
        message.value = "파일을 선택하세요!";
        return;
      }

      const formData = new FormData();
      formData.append("file", selectedFile.value);
      
      try {
        const response = await axios.post("/config/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        if (response.data.passOK == "1") {
          message.value = "Upload Success: " + response.data.file_path;
          setupList.value = response.data.data;
          setupStore.setCalib(true);
          selectedFile.value = null;
        } else {
          message.value = response.data.error;
        }
      } catch (error) {
        message.value = "업로드 실패: " + error.response.data.error;
      }
    };

    const applySetup = async()=> {
      try {
            const response = await axios.get("/config/calibrate/applySetup");
            if (response.data.passOK == "1") {
              message.value = commands.value[index]["name"] + " Success";            
            } else {
              message.value = response.data.error;
            }
      } catch (error) {
        alert(error);
      }
    }

    const uploadFromModal = async () => {
      await upload();
      if (message.value.includes("Success")) {
        showUploadModal.value = false;
      }
    };

    watch(
      () => setupStore.calib,
      (newVal) => {
        if (newVal) fetchsetupList(newVal);
      },
      { immediate: true }
    );

    const fetchsetupList = async () => {
      try {
        const response = await axios.get("/config/checkSetup");
        if (response.data.passOK == "1") {
          select_setupList.value = response.data.data;
          macAddr.value = response.data.mac;
          if (!setupStore.getCalib) setupStore.setCalib(true);
        }else{
          macAddr.value = response.data.mac;
        }
      } catch (error) {
        const msg = "업로드 실패: " + error.response.data.error;
        alert(msg);
      }
    };

    const getTime = async () => {
      try {
        const response = await axios.get('/config/calibrate/gettime');
        const deviceDate = new Date(response.data.deviceTime);
        deviceTime.value = deviceDate.toLocaleString('ko-KR', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        });
        timemode.value = "Device Time - "
        // 시간 차이 계산 (초 단위)
        // const browserDate = new Date();
        // timeDiff.value = (deviceDate - browserDate) / 1000;
        
      } catch (error) {
        console.error('Failed to get device time:', error);
        // statusMessage.value = 'Failed to get device time';
        // statusType.value = 'error';
      }
    };

    onMounted(() => {
      fetchsetupList();
      // updateInterval = setInterval(() => {
      //   getDeviceTime();
      //   }, 1000);
    });
    onUnmounted(()=>{
      // if (updateInterval) {
      //   clearInterval(updateInterval);
      // }
    });

    return {
      handleFileUpload,
      upload,
      uploadFromModal,
      setupList,
      message,
      commands,
      btnClass,
      sendCmd,
      refDict,
      select_setupList,
      selectSetup,
      showMainChannel,
      showSubChannel,
      handleMainChannelChange,
      handleSubChannelChange,
      selectedFile,
      showUploadModal,
      syncSystemTime,
      applySetup,
      deviceTime,
      getTime,
      macAddr,
      errorLimit,
      sendRef,
      SaveCal,
      showReportModal,
      reportInfo,
      handleSend,
      cmdMessage,
      timemode,
    };
  },
};
</script>