<template>
  <div
    class="relative h-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg flex flex-col flex-1"
  >
    <div class="absolute top-0 left-0 right-0 h-0.5 bg-blue-500" aria-hidden="true"></div>
    <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700/60">
      <header class="flex items-center">
        <div class="w-6 h-6 rounded-full shrink-0 bg-blue-500 mr-3">
          <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 20h18M5 16l4-4 4 4 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">MQTT</h3>
      </header>
    </div>
    <div class="px-4 py-3 space-y-4">
      <!-- Use + Type -->
      <div class="flex space-x-3">
        <div class="flex-1 min-w-0">
          <label class="block text-sm font-medium mb-1.5">Use</label>
          <select
            v-model="inputDict.MQTT.Use"
            class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option :value="0">{{ t("config.plansPanel.modbus.no") }}</option>
            <option :value="1">{{ t("config.plansPanel.modbus.yes") }}</option>
          </select>
        </div>
        <div class="flex-1 min-w-0" v-if="inputDict.MQTT.Use === 1">
          <label class="block text-sm font-medium mb-1.5">Type</label>
          <select
            v-model="inputDict.MQTT.Type"
            class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option :value="0">Local</option>
            <option :value="1">public</option>
            <option :value="2">AWSIoTCore</option>
          </select>
        </div>
      </div>

      <!-- LTE Use (Local 제외) -->
      <div v-if="inputDict.MQTT.Use === 1 && inputDict.MQTT.Type >= 1" class="flex items-center justify-between">
        <label class="block text-sm font-medium">LTE Use</label>
        <div
          class="relative inline-flex items-center cursor-pointer"
          @click="toggleLte"
        >
          <div
            class="w-11 h-6 rounded-full transition-colors duration-200"
            :class="inputDict.MQTT.lteuse === 1 ? 'bg-sky-500' : 'bg-gray-300 dark:bg-gray-600'"
          ></div>
          <div
            class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
            :class="inputDict.MQTT.lteuse === 1 ? 'translate-x-5' : 'translate-x-0'"
          ></div>
        </div>
      </div>

      <!-- Host (단독) -->
      <div v-if="inputDict.MQTT.Use === 1">
        <label class="block text-sm font-medium mb-1.5">Host</label>
        <input v-model="inputDict.MQTT.host" class="form-input w-full" type="text" placeholder="Enter MQTT host" />
      </div>

      <!-- Port & Device ID -->
      <div v-if="inputDict.MQTT.Use === 1" class="flex space-x-3">
        <div class="flex-1">
          <label class="block text-sm font-medium mb-1.5">Port</label>
          <input v-model.number="inputDict.MQTT.port" class="form-input w-full" type="number" placeholder="1883" />
        </div>
        <div class="flex-1">
          <label class="block text-sm font-medium mb-1.5">Device ID</label>
          <input :value="inputDict.MQTT.device_id" class="form-input w-full bg-gray-100 dark:bg-gray-700" type="text" readonly />
        </div>
      </div>

      <!-- externalPort & externalUrl (public) -->
      <div v-if="inputDict.MQTT.Use === 1 && inputDict.MQTT.Type === 1" class="flex space-x-3">
        <div class="flex-1">
          <label class="block text-sm font-medium mb-1.5">externalPort</label>
          <input v-model="inputDict.MQTT.externalport" class="form-input w-full" type="number" placeholder="Enter external port" />
        </div>
        <div class="flex-1">
          <label class="block text-sm font-medium mb-1.5">externalUrl</label>
          <input v-model="inputDict.MQTT.url" class="form-input w-full" type="text" placeholder="Enter url" />
        </div>
      </div>

      <!-- Username & Password (Local) -->
      <div v-if="inputDict.MQTT.Use === 1 && inputDict.MQTT.Type === 0" class="flex space-x-3">
        <div class="flex-1">
          <label class="block text-sm font-medium mb-1.5">Username</label>
          <input v-model="inputDict.MQTT.username" class="form-input w-full" type="text" placeholder="Enter username" />
        </div>
        <div class="flex-1">
          <label class="block text-sm font-medium mb-1.5">Password</label>
          <input v-model="inputDict.MQTT.password" class="form-input w-full" type="password" placeholder="Enter password" />
        </div>
      </div>

      <!-- AWS IoT Core Certificates -->
      <div v-if="inputDict.MQTT.Use === 1 && inputDict.MQTT.Type === 2" class="space-y-3">
        <div class="text-xs text-gray-800 dark:text-gray-100 font-semibold uppercase">Certificates</div>
        <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4">
          <input
            type="file"
            multiple
            accept=".pem,.crt,.key,.cert"
            @change="handleCertUpload"
            class="hidden"
            ref="certFileInput"
          />
          <div class="text-center">
            <svg class="mx-auto h-10 w-10 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <button type="button" @click="certFileInput.click()" class="mt-2 btn-sm bg-blue-500 text-white hover:bg-blue-600">
              Select Certificate Files
            </button>
            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">.pem, .crt, .key, .cert files</p>
          </div>
        </div>
        <div v-if="uploadedCerts.length > 0" class="space-y-2">
          <div class="text-xs font-medium text-gray-600 dark:text-gray-300">Uploaded Files:</div>
          <div
            v-for="(cert, index) in uploadedCerts"
            :key="index"
            class="flex items-center justify-between bg-gray-50 dark:bg-gray-700 rounded px-3 py-2"
          >
            <div class="flex items-center space-x-2">
              <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-sm text-gray-700 dark:text-gray-200">{{ cert.filename }}</span>
            </div>
            <button @click="removeCert(index)" class="text-red-500 hover:text-red-700">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <div v-if="certUploadMessage" :class="certUploadSuccess ? 'text-green-600' : 'text-red-600'" class="text-sm">
          {{ certUploadMessage }}
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { inject, ref, watch } from "vue";
import axios from "axios";
import { useI18n } from "vue-i18n";

export default {
  name: "MQTTCard",
  setup() {
    const { t } = useI18n();
    const inputDict = inject("inputDict");

    const uploadedCerts = ref([]);
    const certUploadMessage = ref('');
    const certUploadSuccess = ref(false);
    const certFileInput = ref(null);

    const toggleLte = () => {
      inputDict.value.MQTT.lteuse = inputDict.value.MQTT.lteuse === 1 ? 0 : 1;
    };

    const loadCertList = async () => {
      try {
        const response = await axios.get('/setting/listCerts');
        if (response.data.passOK === 1) {
          uploadedCerts.value = response.data.files;
        }
      } catch (error) {
        console.error('Failed to load cert list:', error);
      }
    };

    const handleCertUpload = async (event) => {
      const files = event.target.files;
      if (!files || files.length === 0) return;
      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      try {
        certUploadMessage.value = 'Uploading...';
        certUploadSuccess.value = false;
        const response = await axios.post('/setting/uploadCerts', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        if (response.data.passOK === 1) {
          certUploadSuccess.value = true;
          certUploadMessage.value = `${response.data.uploaded.length} file(s) uploaded successfully`;
          await loadCertList();
        } else {
          certUploadMessage.value = response.data.error || 'Upload failed';
        }
      } catch (error) {
        certUploadMessage.value = 'Upload failed: ' + (error.response?.data?.error || error.message);
      }
      event.target.value = '';
    };

    const removeCert = async (index) => {
      const cert = uploadedCerts.value[index];
      if (!confirm(`Delete ${cert.filename}?`)) return;
      try {
        const response = await axios.delete(`/setting/deleteCert/${cert.filename}`);
        if (response.data.passOK === 1) {
          uploadedCerts.value.splice(index, 1);
          certUploadMessage.value = 'File deleted';
          certUploadSuccess.value = true;
        }
      } catch (error) {
        certUploadMessage.value = 'Delete failed';
        certUploadSuccess.value = false;
      }
    };

    watch(
      () => inputDict.value.MQTT?.Type,
      (newVal) => {
        if (newVal === 'AWSIoTCore') {
          loadCertList();
        }
      },
      { immediate: true }
    );

    return {
      t,
      inputDict,
      uploadedCerts,
      certUploadMessage,
      certUploadSuccess,
      certFileInput,
      handleCertUpload,
      removeCert,
      toggleLte,
    };
  },
};
</script>
