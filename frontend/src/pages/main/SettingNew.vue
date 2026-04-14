<template>
    <div class="flex h-[100dvh] overflow-hidden">
      <!-- Sidebar -->
      <Sidebar :sidebarOpen="sidebarOpen" @close-sidebar="sidebarOpen = false" />
  
      <!-- Content area -->
      <div
        class="relative flex flex-col flex-1 overflow-y-auto overflow-x-hidden"
      >
        <!-- Site header -->
        <Header
          :sidebarOpen="sidebarOpen"
          @toggle-sidebar="sidebarOpen = !sidebarOpen"
        />
  
        <main class="grow">
          <div class="px-2 sm:px-4 lg:px-6 pt-2 pb-4 w-full max-w-full">

            <!-- Non-device 모드 (User Management 등): 단순 타이틀만 -->
            <div v-if="mode != 'Device'" class="mb-4">
              <h2 class="text-lg md:text-xl text-gray-800 dark:text-gray-100 font-bold">
                <template
                  v-if="
                    ![
                      'User Management',
                      'API User Management',
                      'Account',
                      'User',
                      'maintenance',
                    ].includes(formattedChannel)
                  "
                >
                  {{ t("config.sitemap.title") }} >
                </template>
                {{ t(`config.sitemap.${formattedChannel}`) }}
              </h2>
            </div>

            <!-- Device 모드: 타이틀 + 토글 + Save/Apply 통합 sticky 헤더 -->
            <div
              v-if="mode == 'Device'"
              class="sticky top-16 z-20 mb-1 -mx-2 sm:-mx-4 lg:-mx-6 px-2 sm:px-4 lg:px-6 bg-gray-100/95 dark:bg-gray-900/95 backdrop-blur-sm"
            >
              <!-- 상단: 타이틀 -->
              <div class="pt-0 pb-0">
                <h2 class="text-lg md:text-xl text-gray-800 dark:text-gray-100 font-bold">
                  {{ t("config.sitemap.title") }} > {{ t(`config.sitemap.${formattedChannel}`) }}
                </h2>
              </div>

              <!-- 하단: 채널/옵션 pill 영역 -->
              <div class="flex justify-between items-center py-3">
                <!-- Left: Channel Controls -->
                <div class="flex items-center space-x-4">
                  <!-- General pill 제거됨 (FTP/SNTP/Modbus/MQTT 토글은 PlansPanel의 Device Function 카드로 이동) -->

                  <!-- Main Channel -->
                  <div
                    v-if="mode == 'Device'"
                    class="inline-flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2 border border-gray-200 dark:border-gray-600 shadow-sm"
                  >
                    <div class="flex items-center mr-3">
                      <svg class="w-3.5 h-3.5 mr-1.5 text-gray-600 dark:text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                      </svg>
                      <span class="text-xs font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ t("sidebar.main") }}</span>
                    </div>
                    <div class="w-px h-4 bg-gray-300 dark:bg-gray-500 mr-3"></div>
                    <div class="flex items-center space-x-3">
                      <button
                        class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                        :class="channel_main.Enable ? 'bg-lime-900 text-lime-100 hover:bg-lime-800 dark:bg-lime-100 dark:text-lime-800 dark:hover:bg-white' : 'bg-gray-600 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white'"
                        :disabled="isSaving"
                        @click="channel_main.Enable = !channel_main.Enable"
                      >
                        <span class="relative z-10">{{ t("config.channelPanel.selEnable") }}</span>
                        <div v-if="channel_main.Enable" class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"></div>
                      </button>
                      <button
                        v-if="showDiagnosisOption && channel_main.Enable"
                        class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                        :class="getDiagnosisButtonClass('main')"
                        :disabled="isFTPEnabled || isSaving"
                        @click="toggleDiagnosis('main')"
                      >
                        <span class="relative z-10">{{ t("sidebar.diagnosis") }}</span>
                        <div v-if="inputDict.useFuction.diagnosis_main" class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"></div>
                        <div v-if="isFTPEnabled || isSaving" class="absolute inset-0 bg-gray-500 bg-opacity-70 rounded-md"></div>
                      </button>
                    </div>
                  </div>

                  <!-- Sub Channel -->
                  <div
                    v-if="mode == 'Device'"
                    class="inline-flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2 border border-gray-200 dark:border-gray-600 shadow-sm"
                  >
                    <div class="flex items-center mr-3">
                      <svg class="w-3.5 h-3.5 mr-1.5 text-gray-600 dark:text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                      </svg>
                      <span class="text-xs font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ t("sidebar.sub") }}</span>
                    </div>
                    <div class="w-px h-4 bg-gray-300 dark:bg-gray-500 mr-3"></div>
                    <div class="flex items-center space-x-3">
                      <button
                        class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                        :class="channel_sub.Enable ? 'bg-lime-900 text-lime-100 hover:bg-lime-800 dark:bg-lime-100 dark:text-lime-800 dark:hover:bg-white' : 'bg-gray-600 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white'"
                        :disabled="isSaving"
                        @click="channel_sub.Enable = !channel_sub.Enable"
                      >
                        <span class="relative z-10">{{ t("config.channelPanel.selEnable") }}</span>
                        <div v-if="channel_sub.Enable" class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"></div>
                      </button>
                      <button
                        v-if="showDiagnosisOption && channel_sub.Enable"
                        class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                        :class="getDiagnosisButtonClass('sub')"
                        :disabled="isFTPEnabled || isSaving"
                        @click="toggleDiagnosis('sub')"
                      >
                        <span class="relative z-10">{{ t("sidebar.diagnosis") }}</span>
                        <div v-if="inputDict.useFuction.diagnosis_sub" class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"></div>
                        <div v-if="isFTPEnabled || isSaving" class="absolute inset-0 bg-gray-500 bg-opacity-70 rounded-md"></div>
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Right: Save / Apply -->
                <div class="flex items-center space-x-2">
                  <button
                    class="btn bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 px-5 py-1.5 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="isSaving"
                    @click.prevent="openSaveModal"
                  >
                    <svg v-if="!isSaving" class="w-4 h-4 mr-1.5 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <svg v-else class="animate-spin h-4 w-4 mr-1.5 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {{ isSaving ? t("config.saving") || "Saving..." : t("config.save") }}
                  </button>
                  <button
                    class="btn bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white px-5 py-1.5 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="isSaving"
                    @click.stop.prevent="apply"
                  >
                    <svg class="w-4 h-4 mr-1.5 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                    {{ t("config.apply") }}
                  </button>
                </div>

              </div>

              <!-- Conflict Warning은 DeviceFunctionCard로 이동됨 -->
            </div>

            <div v-if="mode == 'Device' && false" class="mb-6">
              <SettingsSidebar2 />
            </div>

            <!-- Content -->
            <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl">
              <div class="flex flex-col md:flex-row md:-mr-px">
                <AdminPanel v-if="mode != 'Device' && isAdmin" :channel="channel" />
                <AccountPanel v-else-if="mode != 'Device' && !isAdmin" />
                <PlansPanel v-else-if="mode == 'Device' && channel == 'General'" :channel="channel" />
                <ChannelPanel v-else-if="mode == 'Device' && channel == 'Main'" :channel="channel" />
                <ChannelPanel v-else-if="mode == 'Device' && channel == 'Sub'" :channel="channel" />
                <CommandPanel v-else-if="mode == 'Device' && channel == 'Command'" />
              </div>
            </div>
          </div>

          <ModalBasic :modalOpen="showNameplateConfirm" @close-modal="handleConfirm(false)" title="Confirm changes">
            <div class="w-[600px] max-w-full px-6">
              <div class="text-sm">{{ nameplateConfirmMessage }}</div>
              <div class="px-5 py-4 border-t border-gray-200 dark:border-gray-700/60">
                <div class="flex justify-end space-x-2">
                  <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600" @click="handleConfirm(true)">YES</button>
                  <button class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600" @click="handleConfirm(false)">CANCEL</button>
                </div>
              </div>
            </div>
          </ModalBasic>

          <OnboardModal
            :modalOpen="isModalOpen"
            :OpMode="devMode"
            :restartDone="isRestartDone"
            :preventBackdropClose="true"
            :applyMode="applyMode"
            @close-modal="handleCloseModal"
            @restart-validation="restart"
          />

          <LoadingModal
            :isOpen="isStartingService"
            title="Starting Diagnostic Service"
            :message="serviceLoadingMessage"
          />

          <!-- Save Progress Modal -->
          <SaveProgressModal
            :modalOpen="isSaveModalOpen"
            @close-modal="handleSaveModalClose"
            @save-complete="handleSaveComplete"
          />
        </main>
        <Footer />
      </div>
    </div>
  </template>
  
  <script>
  import { ref, computed, watch, provide, onMounted } from "vue";
  import axios from "axios";
  import SettingsSidebar from "../../partials/inners/setting/SettingsSidebar.vue";
  import { useRoute } from "vue-router";
  import { useAuthStore } from "@/store/auth";
  import { useSetupStore } from "@/store/setup";
  import Sidebar from "../common/SideBar3.vue";
  import Header from "../common/Header.vue";
  import Footer from "../common/Footer.vue";
  import { useRouter } from "vue-router";
  import PlansPanel from "../../partials/inners/setting/PlansPanel.vue";
  import BillingPanel from "../../partials/inners/setting/BillingPanel.vue";
  import ChannelPanel from "../../partials/inners/setting/ChannelPanel.vue";
  import AdminPanel from "../../partials/inners/setting/AdminPanel.vue";
  import AccountPanel from "../../partials/inners/setting/AccountPanel.vue";
  import ModalBasic from "../common/ModalBasic.vue";
  import ModalBlank from "../common/ModalBlank.vue";
  import CommandPanel from "../../partials/inners/setting/CommandPanel.vue";
  import { useInputDict } from "@/composables/useInputDict";
  import { useI18n } from "vue-i18n";
  import SettingsSidebar2 from "../../partials/inners/setting/SettingsSidebar2.vue";
  import OnboardModal from "../../components/OnboardingModal2.vue";
  import LoadingModal from "../../components/LoadingModal.vue";
  import SaveProgressModal from "../../components/SaveProgressModal.vue";

  export default {
    name: "Setting",
    props: ["channel", "mode"],
    components: {
      Sidebar,
      Header,
      Footer,
      PlansPanel,
      ChannelPanel,
      AccountPanel,
      ModalBasic,
      SettingsSidebar,
      BillingPanel,
      AdminPanel,
      ModalBlank,
      CommandPanel,
      SettingsSidebar2,
      OnboardModal,
      LoadingModal,
      SaveProgressModal,
    },
    setup(props) {
      const { t } = useI18n();
      const route = useRoute();
      const authStore = useAuthStore();
      const setupStore = useSetupStore();
      const router = useRouter();
      const showNameplateConfirm = ref(false);
      const nameplateConfirmMessage = ref("");
      let resolveNameplateConfirm = null;
      const sidebarOpen = ref(false);
      const dangerModalOpen = ref(false);
      const errorMessage = ref("");
      const isReady = ref(false);
      const isModalOpen = ref(false);
      const mode = ref(props.mode);
      const checkNameplateflag = ref(false);
      const isRestartDone = ref(false);
      const isSaving = ref(false);
      const isStartingService = ref(false);
      const serviceLoadingMessage = ref("");
      const checkNameplateResult = ref(false);
      const isSaveModalOpen = ref(false);

      const isAdmin = computed(() => {
        if (parseInt(authStore.getUserRole) > 1) return true;
        else return false;
      });
      const applyMode = ref(-1);

      function askNameplateConfirm(channels) {
        const channelList = channels.join(", ");
        nameplateConfirmMessage.value =
          t("config.comfirmtext1") + ` ${channelList}.\n` + t("config.comfirmtext2");
        showNameplateConfirm.value = true;
        return new Promise((resolve) => {
          resolveNameplateConfirm = resolve;
        });
      }

      function handleConfirm(ok) {
        showNameplateConfirm.value = false;
        if (resolveNameplateConfirm) {
          resolveNameplateConfirm(!!ok);
          resolveNameplateConfirm = null;
        }
      }

      const {
        setupDict,
        inputDict,
        channel_main,
        channel_sub,
        useDiagnosis,
        diagnosisData,
        advancedData,
        currentDiagnosis,
        changeDiagnosis,
        diagnosis_detail,
      } = useInputDict();

      const devMode = computed(() => authStore.getOpMode);
      const channel = computed(() => props.channel || route.params.channel);
      const devLang = ref('');
      const isFTPEnabled = computed(() => {
        return inputDict.value.useFuction?.ftp === 1 || inputDict.value.useFuction?.ftp === true;
      });

      const isDiagnosisEnabled = computed(() => {
        const isMainDiagnosisEnabled = inputDict.value.useFuction?.diagnosis_main === true || inputDict.value.useFuction?.diagnosis_main === 1;
        const isSubDiagnosisEnabled = inputDict.value.useFuction?.diagnosis_sub === true || inputDict.value.useFuction?.diagnosis_sub === 1;
        const isMainChannelEnabled = channel_main.value?.Enable === 1 || channel_main.value?.Enable === true;
        const isSubChannelEnabled = channel_sub.value?.Enable === 1 || channel_sub.value?.Enable === true;
        const mainDiagnosisActive = isMainDiagnosisEnabled && isMainChannelEnabled;
        const subDiagnosisActive = isSubDiagnosisEnabled && isSubChannelEnabled;
        return mainDiagnosisActive || subDiagnosisActive;
      });

      const showConflictWarning = computed(() => {
        return isFTPEnabled.value && isDiagnosisEnabled.value;
      });

      const showDiagnosis = computed(() => {
        return inputDict.value.useFuction?.diagnosis_main || inputDict.value.useFuction?.diagnosis_sub;
      });

      watch(
        () => channel_sub.value?.Enable,
        (newEnable, oldEnable) => {
          const isNewEnabled = newEnable === true || newEnable === 1;
          const wasOldEnabled = oldEnable === true || oldEnable === 1;
          if (wasOldEnabled && !isNewEnabled) {
            inputDict.value.useFuction.diagnosis_sub = false;
          }
        }
      );

      const showDiagnosisOption = computed(() => {
        switch (devMode.value) {
          case "device0":
          case "server":
            return false;
          default:
            return true;
        }
      });

      const getFTPButtonClass = () => {
        if (isDiagnosisEnabled.value || isSaving.value) {
          return "bg-gray-400 text-gray-600 cursor-not-allowed dark:bg-gray-600 dark:text-gray-400 opacity-50";
        } else if (inputDict.value.useFuction.ftp) {
          return "bg-lime-900 text-lime-100 hover:bg-lime-800 dark:bg-lime-100 dark:text-lime-800 dark:hover:bg-white";
        } else {
          return "bg-gray-600 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white";
        }
      };

      const getDiagnosisButtonClass = (channelType) => {
        if (isFTPEnabled.value || isSaving.value) {
          return "bg-gray-400 text-gray-600 cursor-not-allowed dark:bg-gray-600 dark:text-gray-400 opacity-50";
        } else if (inputDict.value.useFuction[`diagnosis_${channelType}`]) {
          return "bg-lime-900 text-lime-100 hover:bg-lime-800 dark:bg-lime-100 dark:text-lime-800 dark:hover:bg-white";
        } else {
          return "bg-gray-600 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white";
        }
      };

      const toggleFTP = () => {
        if (isSaving.value) return;
        inputDict.value.useFuction.ftp = inputDict.value.useFuction.ftp === 1 ? 0 : 1;
      };

      const toggleDiagnosis = async(channelType) => {
        if (isSaving.value) return;
        if (channelType === "sub" && !channel_sub.value?.Enable) {
          alert("Sub 채널이 비활성화되어 있습니다. 먼저 Sub 채널을 활성화해주세요.");
          return;
        }
        inputDict.value.useFuction[`diagnosis_${channelType}`] = !inputDict.value.useFuction[`diagnosis_${channelType}`];
        if (inputDict.value.useFuction[`diagnosis_${channelType}`]) {
          const active = await checkSmart();
          if (!active) {
            if (confirm("Not running diagnostic service. Do you want to run service?")) {
              manageSmart(1);
            } else {
              return;
            }
          }
        }
      };

      const checkSmart = async () => {
        try {
          const response = await axios.get("/setting/checkSmart");
          return response.data.success;
        } catch (error) {
          console.error(error);
          return false;
        }
      };

      const manageSmart = async (mode) => {
        try {
          if (parseInt(mode) == 1) {
            isStartingService.value = true;
            serviceLoadingMessage.value = "Starting diagnostic service...";
          }
          const response = await axios.get(`/setting/manageSmart/${mode}`);
          if (parseInt(mode) == 1) {
            if (response.data.api && response.data.success) {
              serviceLoadingMessage.value = "Service ready!";
              await new Promise((resolve) => setTimeout(resolve, 500));
              return true;
            } else {
              alert("Failed to start service: " + (response.data.message || ""));
              return false;
            }
          } else {
            alert("All Services is ready");
            return true;
          }
        } catch (error) {
          console.error(error);
          alert("Error starting service: " + error.message);
          return false;
        } finally {
          isStartingService.value = false;
        }
      };

      watch(showDiagnosis, (newVal) => { useDiagnosis.value = newVal; }, { immediate: true });
      watch(() => inputDict.value.useFuction?.diagnosis_main, (newVal) => { currentDiagnosis.value.Main = newVal; }, { immediate: true });
      watch(() => inputDict.value.useFuction?.diagnosis_sub, (newVal) => { currentDiagnosis.value.Sub = newVal; }, { immediate: true });
      watch(() => [route.params.channel, route.params.mode], ([newChannel, newMode]) => { channel.value = newChannel; mode.value = newMode; });

      watch(
        () => useDiagnosis.value,
        async (newVal, oldVal) => {
          if (newVal && !oldVal) {
            const isRunning = await checkSmart();
            if (!isRunning) {
              const confirmed = confirm("Not running diagnostic service. Do you want to run diagnostic service?");
              if (confirmed) {
                const started = await manageSmart(1);
                if (!started) {
                  inputDict.value.useFuction.diagnosis_main = false;
                  inputDict.value.useFuction.diagnosis_sub = false;
                  return;
                }
              } else {
                inputDict.value.useFuction.diagnosis_main = false;
                inputDict.value.useFuction.diagnosis_sub = false;
                return;
              }
            }
            GetDiagnosisSetting();
            GetAdvancedProfile(); // ★ Advanced Profile도 함께 로드
          }
        }
      );

      watch(
        () => [isFTPEnabled.value, isDiagnosisEnabled.value, channel_sub.value?.Enable],
        ([ftpEnabled, diagnosisEnabled]) => {
          if (ftpEnabled && diagnosisEnabled) {
            console.warn("⚠️ FTP와 Diagnosis가 동시에 활성화되었습니다.");
          }
        },
        { immediate: true }
      );

      const formattedChannel = computed(() => {
        if (mode.value == "Device") {
          if (channel.value === "General") return "General";
          else if (channel.value === "Main") return "Main Channel";
          else if (channel.value === "Sub") return "Sub Channel";
          else return "Command";
        } else {
          if (channel.value == "User") return "User Management";
          else if (channel.value == "APIUser") return "API User Management";
          else return "Account";
        }
      });

      const apply = async () => {
        if (isSaving.value) return;
        isModalOpen.value = true;
      };

      const handleCloseModal = () => {
        isModalOpen.value = false;
        isRestartDone.value = false;
      };

      const restart = async () => {
        if (devMode.value == "device0") {
          alert("✅ System restarted successfully");
          isRestartDone.value = true;
          return;
        }
        
        if (inputDict.value.useFuction.diagnosis_main || inputDict.value.useFuction.diagnosis_sub) {
          try {
            const response = await axios.get(`/setting/restartasset`);
            if (response.data.status === "1") {
              if (response.data.success) {
                const servicflag = await serviceRestart("restart", "SmartSystems");
                if (servicflag["result"]) {
                  alert("✅ Service restarted successfully");
                  isRestartDone.value = true;
                } else {
                  alert("❌ SmartSystem Restart failed");
                }
              } else {
                isRestartDone.value = true;
                alert("✅ System restarted successfully");
              }
            } else {
              alert("✅ System restarted failed: " + response.data.error);
            }
          } catch (e) {
            console.error("Error occurred:", e);
            alert("❌ Error occurred while restarting: " + e.message);
          }
        } else {
          await manageSmart(0);
          alert("✅ Service restarted successfully");
          isRestartDone.value = true;
        }
        await serviceMQTT();
        await networkApply();
      };

      const serviceRestart = async (cmd, item) => {
        try {
          const response = await axios.get(`/setting/SysService/${cmd}/${item}`);
          if (response.data.success) {
            return { result: true, msg: response.data.error };
          } else {
            return { result: false, msg: response.data.error };
          }
        } catch (error) {
          return { result: false, msg: error };
        }
      };

      const networkApply = async () => {
        try {
          const response = await axios.get(`/setting/applyNetwork`);
          if (response.data.result) {
            console.log(response.data.ip);
          } 
        } catch (error) {
          console.log(error);
        }
      };

      const serviceMQTT = async () => {
        try {
          const response = await axios.get(`/setting/checkMQTT`);
          if (response.data.passOK == 1) {
            console.log(response.data.ret);
          } 
        } catch (error) {
          console.log(error);
        }
      };

      const GetSetting = async () => {
        try {
          const response = await axios.get(`/setting/getSettingData/${channel.value}`);
          if (response.data.passOK == 1) {
            if (channel.value == "General") {
              Object.assign(inputDict.value, response.data.data);
            } else if (channel.value == "Main") {
              Object.assign(channel_main.value, response.data.data);
            } else {
              Object.assign(channel_sub.value, response.data.data[0]);
            }

            setupStore.setsetupFromFile(true);
          }
        } catch (error) {
          console.error("데이터 가져오기 실패:", error);
          errorMessage.value = "데이터를 불러오는 중 오류가 발생했습니다.";
        }
      };

      const GetDiagnosisSetting = async () => {
        try {
          const response = await axios.get(`/setting/getDiagnosisSetting`);
          if (response.data.success) {
            Object.assign(diagnosisData.value, response.data.data);
          } else {
            console.warn("⚠️ 서버 응답 실패:", response.data.error);
          }
        } catch (error) {
          console.error("❌ 데이터 가져오기 실패:", error);
          errorMessage.value = "데이터를 불러오는 중 오류가 발생했습니다.";
        }
      };

      // ★ Advanced Profile 가져오기
      const GetAdvancedProfile = async () => {
        try {
          const response = await axios.get("/setting/getDiagnosisProfile");
          if (response.data.success) {
            Object.assign(advancedData.value, response.data.data);
          }
        } catch (error) {
          console.error("❌ Advanced Profile 가져오기 실패:", error);
        }
      };

      // ★ Diagnosis 데이터 전체 리로드 (Cancel 시 사용)
      const reloadDiagnosisData = async () => {
        await GetDiagnosisSetting();
        await GetAdvancedProfile();
      };

      const GetSettingData = async () => {
        try {
          const response = await axios.get(`/setting/getSetting`);
          if (response.data.passOK == 1) {
            setupDict.value = response.data.data;
            Object.assign(inputDict.value, setupDict.value["General"]);
            Object.assign(channel_main.value, setupDict.value["main"]);
            Object.assign(channel_sub.value, setupDict.value["sub"]);
            devLang.value = setupDict.value["lang"];       
            inputDict.value.MQTT.device_id = inputDict.value.deviceInfo.mac_address;
            setupStore.setsetupFromFile(true);
          }
        } catch (error) {
          console.error("데이터 가져오기 실패:", error);
        }
      };

      const Reset = async () => {
        try {
          const response = await axios.get("/setting/Reset");
          if (response.data.success) {
            authStore.setInstall(0);
            if (authStore.logout) {
              await authStore.logout();
              router.push("/signin");
            }
            dangerModalOpen.value = false;
          }
        } catch (error) {
          console.error("데이터 가져오기 실패:", error);
        }
      };

      // Save Modal Functions
      const openSaveModal = () => {
        if (isSaving.value) return;
        if (showConflictWarning.value) {
          alert("Cannot use Waveform FTP and Diagnosis simultaneously. Please disable one of them.");
          return;
        }
        isSaving.value = true;
        isSaveModalOpen.value = true;
      };

      const handleSaveModalClose = async () => {
        isSaveModalOpen.value = false;
        isSaving.value = false;
        // ★ Cancel 시 Diagnosis 데이터 리로드
        if (useDiagnosis.value) {
          await reloadDiagnosisData();
        }
      };

      const handleSaveComplete = async (result) => {
        isSaveModalOpen.value = false;
        isSaving.value = false;
        if (result.success) {
          setupStore.setApplySetup(false);
          await setupStore.checkSetting();
        }
      };

      onMounted(async () => {
        await GetSettingData();
        // ★ 초기 로드 시 Diagnosis 활성화되어 있으면 Advanced Profile도 로드
        if (useDiagnosis.value) {
          await GetDiagnosisSetting();
          await GetAdvancedProfile();
        }
      });

      provide("inputDict", inputDict);
      provide("channel_main", channel_main);
      provide("channel_sub", channel_sub);
      provide("useDiagnosis", useDiagnosis);
      provide("diagnosisData", diagnosisData);
      provide("advancedData", advancedData);
      provide("currentDiagnosis", currentDiagnosis);
      provide("devMode", devMode);
      provide("devLang", devLang);
      provide("changeDiagnosis", changeDiagnosis);
      provide("checkNameplateflag", checkNameplateflag);
      provide("diagnosis_detail", diagnosis_detail);
      provide("GetSettingData", GetSettingData);
      provide("reloadDiagnosisData", reloadDiagnosisData); // ★ 리로드 함수 provide

      return {
        sidebarOpen,
        channel,
        channel_main,
        channel_sub,
        formattedChannel,
        inputDict,
        GetSetting,
        errorMessage,
        isAdmin,
        mode,
        t,
        devMode,
        Reset,
        dangerModalOpen,
        showDiagnosis,
        showDiagnosisOption,
        apply,
        isModalOpen,
        handleCloseModal,
        isFTPEnabled,
        isDiagnosisEnabled,
        showConflictWarning,
        getFTPButtonClass,
        getDiagnosisButtonClass,
        toggleFTP,
        toggleDiagnosis,
        restart,
        GetDiagnosisSetting,
        GetAdvancedProfile,
        reloadDiagnosisData,
        checkNameplateflag,
        diagnosis_detail,
        showNameplateConfirm,
        nameplateConfirmMessage,
        handleConfirm,
        isRestartDone,
        isSaving,
        isStartingService,
        serviceLoadingMessage,
        checkNameplateResult,
        applyMode,
        isSaveModalOpen,
        openSaveModal,
        handleSaveModalClose,
        handleSaveComplete,
        devLang,
      };
    },
  };
  </script>