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
      {{ deviceTime }}
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
      @click="SetTime"
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
      @click="saveRef"
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
      >
        <span class="flex items-center justify-center gap-1.5">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V2"></path>
          </svg>
          Save
        </span>
      </button>
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

export default {
  name: "CaliSidebar",
  props: ["commands"],
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
        emit('startPolling');
        // if (Object.values(refDict.value).every(val => val === 0)) {
        //   alert("모든 값이 0입니다. 최소 하나 이상의 값을 입력해주세요.");
        //   return;
        // }
        // try {
        //     const response = await axios.post(`/config/calibrate/start`, refDict.value, {
        //       headers: { "Content-Type": "application/json" },
        //     });
        //     if (response.data.passOK == "1") {
        //       alert("Ref Save Success");
        //     } else {
        //       alert(response.data.error);
        //     }
        //   } catch (error) {
        //     alert(error);
        //   }
      } else if (index == 1) {
        try {
          const response = await axios.get("/config/calibrate/end");
          if (response.data.passOK == "1") {
            alert(commands.value[index]["name"] + " Success");
            emit('stopPolling');
          } else {
            alert(response.data.error);
          }
        } catch (error) {
          alert(error);
        }
      } else {
        let data = {};
        if ("Param" in commands.value[index]) {
          data["param"] = commands.value[index]["Param"];
          data["ref"] = refDict.value[commands.value[index]["Param"]].toString();
        } else {
          data["param"] = "None";
          data["ref"] = "None";
        }
        data["cmd"] = commands.value[index]["name"];
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
          } else {
            alert(response.data.error);
          }
        } catch (error) {
          alert(error);
        }
      }
    };

    const SetTime = () => {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const seconds = String(now.getSeconds()).padStart(2, '0');
      
      const pcTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
      console.log("PC Time:", pcTime);
      
      // 나중에 여기서 서버로 시간을 전송
      // axios.post('/config/synctime', { time: pcTime });
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
      SetTime,
      applySetup,
      deviceTime,
      getTime,
      macAddr,
      errorLimit,
      sendRef,
    };
  },
};
</script>