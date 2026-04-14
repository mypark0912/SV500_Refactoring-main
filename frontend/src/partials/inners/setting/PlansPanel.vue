<template>
  <div class="grow dark:text-white">
    <!-- Panel body -->
    <div class="px-6 pt-3 pb-6 space-y-6">
      <!-- Plans -->
      <section>
        <div class="mb-4">
          <div class="flex items-center space-x-4 text-sm relative">
            <!-- FTP Checkbox -->
            <label v-if="false" class="flex items-center space-x-2">
              <input
                type="checkbox"
                class="form-checkbox text-violet-500 focus:ring-violet-500"
                :checked="
                  inputDict.useFuction.ftp === 1 ||
                  inputDict.useFuction.ftp === true
                "
                @change="handleFTPToggle($event)"
              />
              <span>{{ t("config.plansPanel.useWaveFormFTP") }}</span>
            </label>

            <!-- SNTP Checkbox -->
            <label v-if="false" class="flex items-center space-x-2">
              <input
                type="checkbox"
                class="form-checkbox text-violet-500 focus:ring-violet-500"
                :checked="
                  inputDict.useFuction.sntp === 1 ||
                  inputDict.useFuction.sntp === true
                "
                @change="
                  inputDict.useFuction.sntp = $event.target.checked ? 1 : 0
                "
              />
              <span>{{ t("config.plansPanel.useSNTP") }}</span>
            </label>

            <!-- FTP 안내문구는 SettingNew.vue 통합 헤더로 이동 -->

            <!-- File Upload Modal -->
            <ModalBasic
              id="feedback-modal"
              :modalOpen="feedbackModalOpen"
              @close-modal="feedbackModalOpen = false"
              title="File Upload"
            >
              <div class="px-4 py-3">
                <div class="text-sm">
                  <div class="font-medium text-gray-800 dark:text-gray-100 mb-2">
                    Setting file upload
                  </div>
                </div>
                <div class="space-y-2">
                  <div>
                    <label class="block text-sm font-medium mb-1" for="name">
                      file path <span class="text-red-500">*</span>
                    </label>
                    <input
                      id="filename"
                      class="form-input w-full px-2 py-1"
                      @change="handleFileUpload"
                      type="file"
                      required
                    />
                  </div>
                </div>
                <div class="text-sm mt-2">
                  <div class="font-medium text-gray-800 dark:text-gray-100">
                    {{ message }} 🙌
                  </div>
                </div>
              </div>
              <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700/60">
                <div class="flex flex-wrap justify-end space-x-2">
                  <button
                    class="btn-sm bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white"
                    @click.prevent="upload"
                  >
                    Import
                  </button>
                  <button
                    class="btn-sm border-gray-200 dark:border-gray-700/60 hover:border-gray-300 dark:hover:border-gray-600 text-gray-800 dark:text-white"
                    @click.stop="feedbackModalOpen = false"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </ModalBasic>
          </div>
        </div>

        <div class="grid grid-cols-12 gap-6 items-stretch">

          <!-- 1행: 장치정보 / Device Function / 통신설정 / [기타정보 + SNTP] -->
          <div class="col-span-full xl:col-span-3">
            <DeviceInfoCard />
          </div>
          <div class="col-span-full xl:col-span-3">
            <DeviceFunctionCard />
          </div>
          <div class="col-span-full xl:col-span-3">
            <CommunicationCard />
          </div>
          <div class="col-span-full xl:col-span-3 flex flex-col gap-6">
            <div class="flex-1 min-h-0">
              <EtcCard />
            </div>
            <SNTPCard
              :showSNTP="inputDict.useFuction.sntp === 1 || inputDict.useFuction.sntp === true"
            />
          </div>

          <!-- 2행: Modbus Serial / MQTT / Waveform FTP (각 토글 ON일 때만 표시) -->
          <div
            v-if="inputDict.modbus.rtu_use === 1"
            class="col-span-full xl:col-span-3 xl:col-start-1"
          >
            <ModbusSerialCard />
          </div>
          <div
            v-if="inputDict.MQTT.Use === 1"
            class="col-span-full xl:col-span-3"
          >
            <MQTTCard />
          </div>
          <WaveformFTPCard
            :showFTP="inputDict.useFuction.ftp === 1 || inputDict.useFuction.ftp === true"
          />

          <DiagnosisSetupCard1 :showDiagnosis="useDiagnosis || showDiagnosis" />
        </div>
      </section>
    </div>

    <!-- Panel footer -->
    <footer v-if="false">
      <div class="flex px-6 py-5 border-t border-gray-200 dark:border-gray-700/60">
        <div class="flex gap-3">
          <button
            class="btn bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white"
            @click.prevent="savefile"
          >
            {{ t("config.save") }}
          </button>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
import { ref, onMounted, watch, inject, computed, provide } from "vue";
import axios from "axios";
import ModalBasic from "../../../components/ModalBasic.vue";
import flatPickr from "vue-flatpickr-component";
import "flatpickr/dist/flatpickr.css";
import { useSetupStore } from "@/store/setup";
import { useAuthStore } from "@/store/auth";
import { settingValidator } from "@/utils/validation.js";
import WaveformFTPCard from "./WaveformFTPCard.vue";
import SNTPCard from "./SNTPCard.vue";
import DiagnosisSetupCard1 from "./General_diagnosisCard.vue";
import DeviceInfoCard from "./DeviceInfoCard.vue";
import EtcCard from "./EtcCard.vue";
import CommunicationCard from "./CommunicationCard.vue";
import DeviceFunctionCard from "./DeviceFunctionCard.vue";
import ModbusSerialCard from "./ModbusSerialCard.vue";
import MQTTCard from "./MQTTCard.vue";
import { useI18n } from "vue-i18n";
export default {
  name: "PlansPanel",
  props: ["channel"],
  components: {
    ModalBasic,
    flatPickr,
    WaveformFTPCard,
    SNTPCard,
    DiagnosisSetupCard1,
    DeviceInfoCard,
    EtcCard,
    CommunicationCard,
    DeviceFunctionCard,
    ModbusSerialCard,
    MQTTCard,
  },
  setup(props) {
    const { t } = useI18n();
    const setupStore = useSetupStore();
    const channel = ref(props.channel);
    const errorMessage = ref("");
    const feedbackModalOpen = ref(false);
    const selectedFile = ref(null);
    const toggle1 = ref("YES");
    const message = ref("Select upload setting file");
    const inputDict = inject("inputDict");
    const diagnosisData = inject("diagnosisData");
    const advancedData = inject("advancedData");
    const useDiagnosis = inject("useDiagnosis");
    const devMode = inject("devMode");
    const saveAllSettings = inject("saveAllSettings");
    const showFTPToast = ref(false);

    const channel_main = inject("channel_main");
    const channel_sub = inject("channel_sub");

    if (inputDict.value.tcpip && inputDict.value.tcpip.dhcp === undefined) {
      inputDict.value.tcpip.dhcp = 0;
    }

    const handleFTPToggle = (event) => {
      const isChecked = event.target.checked;
      inputDict.value.useFuction.ftp = isChecked ? 1 : 0;
      if (isChecked) {
        showFTPToast.value = false;
      } else {
        showFTPToast.value = true;
      }
    };

    watch(
      () => inputDict.value.useFuction?.ftp,
      (newVal) => {
        showFTPToast.value = newVal !== 1;
      },
      { immediate: true }
    );

    if (!inputDict.value.modbus) {
      inputDict.value.modbus = {
        mode: "serial",
        tcp_port: 502,
        tcp_timeout: 5000,
        modbus_id: 1,
        baud_rate: 0,
        parity: 0,
        data_bits: 8,
        stop_bits: 1,
      };
    }

    const setDiagnosisSetting = async () => {
      try {
        const response = await axios.post(
          "/setting/setDiagnosisSetting",
          diagnosisData.value,
          { headers: { "Content-Type": "application/json" }, withCredentials: true }
        );
        if (response.data && response.data.success) {
          console.log("✅ Diagnosis 설정 저장 성공!");
        } else {
          console.log("❌ Diagnosis 설정 저장 실패!");
        }
      } catch (err) {
        console.log("❌ 저장 중 오류 발생: " + err.message);
      }
    };

    const setDiagnosisProfile = async () => {
      try {
        const response = await axios.post(
          "/setting/setDiagnosisProfile",
          advancedData.value,
          { headers: { "Content-Type": "application/json" }, withCredentials: true }
        );
        if (response.data && response.data.success) {
          console.log("✅ Diagnosis 설정 저장 성공!");
        } else {
          console.log("❌ Diagnosis 설정 저장 실패!");
        }
      } catch (err) {
        console.log("❌ 저장 중 오류 발생: " + err.message);
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
        const response = await axios.post("/setting/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        if (response.data.passOK == "1") {
          message.value = "Upload Success : " + response.data.file_path;
          feedbackModalOpen.value = false;
          await GetSetting();
        } else {
          message.value = response.data.error;
        }
      } catch (error) {
        message.value = "업로드 실패: " + error.response.data.error;
      }
    };

    const savefile = async () => {
      const isFTPEnabled = inputDict.value.useFuction.ftp === 1;
      const isMainDiagnosisEnabled =
        inputDict.value.useFuction.diagnosis_main === true ||
        inputDict.value.useFuction.diagnosis_main === 1;
      const isSubDiagnosisEnabled =
        inputDict.value.useFuction.diagnosis_sub === true ||
        inputDict.value.useFuction.diagnosis_sub === 1;
      const isMainChannelEnabled = channel_main.value && channel_main.value.Enable === 1;
      const isSubChannelEnabled = channel_sub.value && channel_sub.value.Enable === 1;
      const isAnyDiagnosisEnabled =
        (isMainDiagnosisEnabled && isMainChannelEnabled) ||
        (isSubDiagnosisEnabled && isSubChannelEnabled);

      if (isFTPEnabled && isAnyDiagnosisEnabled) {
        alert("Cannot use Waveform FTP and Diagnosis simultaneously. Please disable one of them.");
        return;
      }
      const validationResult = settingValidator.validateAllSettings(
        inputDict.value,
        channel_main.value,
        channel_sub.value
      );
      if (!validationResult.isValid) {
        alert(settingValidator.formatErrorOnlyMessage());
        return;
      }
      if (validationResult.hasWarnings) {
        const proceed = confirm(settingValidator.formatWarningMessage());
        if (!proceed) return;
      }
      await saveAllSettings();
    };

    const GetSetting = async () => {
      try {
        const response = await axios.get("/setting/getSettingData/General");
        if (response.data.passOK == 1) {
          Object.assign(inputDict.value, response.data.data);
          setupStore.setsetupFromFile(true);
        }
      } catch (error) {
        console.error("데이터 가져오기 실패:", error);
        errorMessage.value = "데이터를 불러오는 중 오류가 발생했습니다.";
      }
    };

    const dateConfig = {
      dateFormat: "Y-m-d",
      defaultDate: new Date(),
      onChange: (selectedDates, dateStr) => {
        console.log("Selected Date:", dateStr);
      },
    };

    const triggerTimePicker = (e) => {
      e.target.showPicker();
    };

    return {
      inputDict,
      channel,
      errorMessage,
      feedbackModalOpen,
      message,
      selectedFile,
      upload,
      handleFileUpload,
      savefile,
      toggle1,
      GetSetting,
      useDiagnosis,
      setDiagnosisSetting,
      dateConfig,
      triggerTimePicker,
      devMode,
      diagnosisData,
      advancedData,
      t,
      showFTPToast,
      handleFTPToggle,
    };
  },
};
</script>