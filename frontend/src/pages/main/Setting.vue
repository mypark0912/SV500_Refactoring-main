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
        <div class="px-2 sm:px-4 lg:px-6 py-4 w-full max-w-full">
          <div class="mb-4">
            <h2
              class="text-xl md:text-2xl text-gray-800 dark:text-gray-100 font-bold"
            >
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

          <!-- Sticky Header Section - 정리된 레이아웃 -->
          <div
            v-if="mode == 'Device'"
            class="sticky top-16 z-20 bg-white dark:bg-gray-800 rounded-xl mb-4 p-4 shadow-sm border border-gray-200 dark:border-gray-700"
          >
            <!-- Page header - 좌우 정렬 -->
            <div class="flex justify-between items-center">
              <!-- Left: Channel Controls -->
              <div class="flex items-center space-x-4">
                <!-- General -->
                <div
                  v-if="mode == 'Device'"
                  class="inline-flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2 border border-gray-200 dark:border-gray-600 shadow-sm"
                >
                  <!-- 레이블 -->
                  <div class="flex items-center mr-3">
                    <svg
                      class="w-3.5 h-3.5 mr-1.5 text-gray-600 dark:text-gray-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clip-rule="evenodd"
                      ></path>
                    </svg>
                    <span
                      class="text-xs font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap"
                    >
                      {{ t("sidebar.general") }}
                    </span>
                  </div>

                  <!-- 구분선 -->
                  <div class="w-px h-4 bg-gray-300 dark:bg-gray-500 mr-3"></div>

                  <!-- 버튼 그룹 -->
                  <div class="flex items-center space-x-3">
                    <button
                      class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                      :class="getFTPButtonClass()"
                      :disabled="isDiagnosisEnabled || isSaving"
                      @click="toggleFTP"
                    >
                      <span class="relative z-10">
                        {{ t("config.plansPanel.useWaveFormFTP") }}
                      </span>
                      <!-- 활성화 상태 표시점 -->
                      <div
                        v-if="inputDict.useFuction.ftp"
                        class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"
                      ></div>
                      <!-- 비활성화 상태 표시 -->
                      <div
                        v-if="isDiagnosisEnabled || isSaving"
                        class="absolute inset-0 bg-gray-500 bg-opacity-70 rounded-md"
                      ></div>
                    </button>

                    <button
                      class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                      :class="
                        inputDict.useFuction.sntp
                          ? 'bg-lime-900 text-lime-100 hover:bg-lime-800 dark:bg-lime-100 dark:text-lime-800 dark:hover:bg-white'
                          : 'bg-gray-600 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white'
                      "
                      :disabled="isSaving"
                      @click="
                        inputDict.useFuction.sntp =
                          inputDict.useFuction.sntp === 1 ? 0 : 1
                      "
                    >
                      <span class="relative z-10">
                        {{ t("config.plansPanel.useSNTP") }}
                      </span>
                      <!-- 활성화 상태 표시점 -->
                      <div
                        v-if="inputDict.useFuction.sntp"
                        class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"
                      ></div>
                    </button>
                  </div>
                </div>
                <!-- 주채널 -->
                <div
                  v-if="mode == 'Device'"
                  class="inline-flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2 border border-gray-200 dark:border-gray-600 shadow-sm"
                >
                  <!-- 레이블 -->
                  <div class="flex items-center mr-3">
                    <svg
                      class="w-3.5 h-3.5 mr-1.5 text-gray-600 dark:text-gray-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clip-rule="evenodd"
                      ></path>
                    </svg>
                    <span
                      class="text-xs font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap"
                    >
                      {{ t("sidebar.main") }}
                    </span>
                  </div>

                  <!-- 구분선 -->
                  <div class="w-px h-4 bg-gray-300 dark:bg-gray-500 mr-3"></div>

                  <!-- 버튼 그룹 -->
                  <div class="flex items-center space-x-3">
                    <button
                      class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                      :class="
                        channel_main.Enable
                          ? 'bg-lime-900 text-lime-100 hover:bg-lime-800 dark:bg-lime-100 dark:text-lime-800 dark:hover:bg-white'
                          : 'bg-gray-600 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white'
                      "
                      :disabled="isSaving"
                      @click="channel_main.Enable = !channel_main.Enable"
                    >
                      <span class="relative z-10">
                        {{ t("config.channelPanel.selEnable") }}
                      </span>
                      <!-- 활성화 상태 표시점 -->
                      <div
                        v-if="channel_main.Enable"
                        class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"
                      ></div>
                    </button>
                    <button
                      v-if="false"
                      class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                      :class="
                        channel_main.PowerQuality
                          ? 'bg-lime-900 text-lime-100 hover:bg-lime-800 dark:bg-lime-100 dark:text-lime-800 dark:hover:bg-white'
                          : 'bg-gray-600 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white'
                      "
                      :disabled="isSaving"
                      @click="
                        channel_main.PowerQuality = !channel_main.PowerQuality
                      "
                    >
                      <span class="relative z-10">
                        {{ t("config.channelPanel.selPQ") }}
                      </span>
                      <!-- 활성화 상태 표시점 -->
                      <div
                        v-if="channel_main.PowerQuality"
                        class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"
                      ></div>
                    </button>

                    <button
                      v-if="showDiagnosisOption && channel_main.Enable"
                      class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                      :class="getDiagnosisButtonClass('main')"
                      :disabled="isFTPEnabled || isSaving"
                      @click="toggleDiagnosis('main')"
                    >
                      <span class="relative z-10">
                        {{ t("sidebar.diagnosis") }}
                      </span>
                      <!-- 활성화 상태 표시점 -->
                      <div
                        v-if="inputDict.useFuction.diagnosis_main"
                        class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"
                      ></div>
                      <!-- 비활성화 상태 표시 -->
                      <div
                        v-if="isFTPEnabled || isSaving"
                        class="absolute inset-0 bg-gray-500 bg-opacity-70 rounded-md"
                      ></div>
                    </button>
                  </div>
                </div>

                <!-- 보조채널 -->
                <div
                  v-if="mode == 'Device'"
                  class="inline-flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2 border border-gray-200 dark:border-gray-600 shadow-sm"
                >
                  <!-- 레이블 -->
                  <div class="flex items-center mr-3">
                    <svg
                      class="w-3.5 h-3.5 mr-1.5 text-gray-600 dark:text-gray-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clip-rule="evenodd"
                      ></path>
                    </svg>
                    <span
                      class="text-xs font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap"
                    >
                      {{ t("sidebar.sub") }}
                    </span>
                  </div>

                  <!-- 구분선 -->
                  <div class="w-px h-4 bg-gray-300 dark:bg-gray-500 mr-3"></div>

                  <!-- 버튼 그룹 -->
                  <div class="flex items-center space-x-3">
                    <button
                      class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                      :class="
                        channel_sub.Enable
                          ? 'bg-lime-900 text-lime-100 hover:bg-lime-800 dark:bg-lime-100 dark:text-lime-800 dark:hover:bg-white'
                          : 'bg-gray-600 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white'
                      "
                      :disabled="isSaving"
                      @click="channel_sub.Enable = !channel_sub.Enable"
                    >
                      <span class="relative z-10">
                        {{ t("config.channelPanel.selEnable") }}
                      </span>
                      <!-- 활성화 상태 표시점 -->
                      <div
                        v-if="channel_sub.Enable"
                        class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"
                      ></div>
                    </button>

                    <button
                      v-if="false"
                      class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                      :class="
                        channel_sub.PowerQuality
                          ? 'bg-lime-900 text-lime-100 hover:bg-lime-800 dark:bg-lime-100 dark:text-lime-800 dark:hover:bg-white'
                          : 'bg-gray-600 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white'
                      "
                      :disabled="isSaving"
                      @click="
                        channel_sub.PowerQuality = !channel_sub.PowerQuality
                      "
                    >
                      <span class="relative z-10">
                        {{ t("config.channelPanel.selPQ") }}
                      </span>
                      <!-- 활성화 상태 표시점 -->
                      <div
                        v-if="channel_sub.PowerQuality"
                        class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"
                      ></div>
                    </button>

                    <button
                      v-if="showDiagnosisOption && channel_sub.Enable"
                      class="btn h-6 relative overflow-hidden transition-all duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lime-500 rounded-md px-3 text-xs font-medium shadow-sm whitespace-nowrap"
                      :class="getDiagnosisButtonClass('sub')"
                      :disabled="isFTPEnabled || isSaving"
                      @click="toggleDiagnosis('sub')"
                    >
                      <span class="relative z-10">
                        {{ t("sidebar.diagnosis") }}
                      </span>
                      <!-- 활성화 상태 표시점 -->
                      <div
                        v-if="inputDict.useFuction.diagnosis_sub"
                        class="absolute top-1 right-1 w-2 h-2 bg-lime-400 rounded-full animate-pulse"
                      ></div>
                      <!-- 비활성화 상태 표시 -->
                      <div
                        v-if="isFTPEnabled || isSaving"
                        class="absolute inset-0 bg-gray-500 bg-opacity-70 rounded-md"
                      ></div>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Right: Action Buttons -->
              <div class="flex items-center space-x-3">
                <!-- Save Button -->
                <button
                  class="btn bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 px-6 py-2 shadow-lg transition-all duration-200 hover:shadow-xl rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="isSaving"
                  @click.prevent="savefile"
                >
                  <svg
                    v-if="!isSaving"
                    class="w-4 h-4 mr-2 inline-block"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  <!-- 로딩 스피너 -->
                  <svg
                    v-else
                    class="animate-spin h-4 w-4 mr-2 inline-block"
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
                  {{
                    isSaving
                      ? t("config.saving") || "Saving..."
                      : t("config.save")
                  }}
                </button>

                <!-- Apply Button -->
                <button
                  class="btn bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white px-6 py-2 shadow-lg transition-all duration-200 hover:shadow-xl rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="isSaving"
                  @click.stop.prevent="apply"
                >
                  <svg
                    class="w-4 h-4 mr-2 inline-block"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  Apply
                </button>
              </div>
            </div>

            <!-- 상태 알림 메시지 -->
            <div
              v-if="showConflictWarning"
              class="mt-3 p-3 bg-yellow-100 dark:bg-yellow-900 border border-yellow-300 dark:border-yellow-700 rounded-lg"
            >
              <div class="flex items-center">
                <svg
                  class="w-4 h-4 text-yellow-600 dark:text-yellow-400 mr-2"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clip-rule="evenodd"
                  />
                </svg>
                <span
                  class="text-yellow-800 dark:text-yellow-200 text-xs font-medium"
                >
                  ⚠️ FTP와 Diagnosis는 동시에 사용할 수 없습니다. (Main/Sub 채널
                  진단 모두 포함) 하나를 비활성화해주세요.
                </span>
              </div>
            </div>
          </div>

          <div v-if="mode == 'Device' && false" class="mb-6">
            <SettingsSidebar2 />
          </div>

          <!-- Content - 여백 제거 -->
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl">
            <div class="flex flex-col md:flex-row md:-mr-px">
              <AdminPanel
                v-if="mode != 'Device' && isAdmin"
                :channel="channel"
              />
              <AccountPanel v-else-if="mode != 'Device' && !isAdmin" />
              <PlansPanel
                v-else-if="mode == 'Device' && channel == 'General'"
                :channel="channel"
              />
              <ChannelPanel
                v-else-if="mode == 'Device' && channel == 'Main'"
                :channel="channel"
              />
              <ChannelPanel
                v-else-if="mode == 'Device' && channel == 'Sub'"
                :channel="channel"
              />
              <CommandPanel
                v-else-if="mode == 'Device' && channel == 'Command'"
              />
            </div>
          </div>
        </div>
        <ModalBasic
          :modalOpen="showNameplateConfirm"
          @close-modal="handleConfirm(false)"
          title="Confirm changes"
        >
          <div class="w-[600px] max-w-full px-6">
            <!-- 헤더 -->
            <div class="text-sm">
              {{ nameplateConfirmMessage }}
            </div>

            <!-- Footer -->
            <div
              class="px-5 py-4 border-t border-gray-200 dark:border-gray-700/60"
            >
              <div class="flex justify-end space-x-2">
                <button
                  class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                  @click="handleConfirm(true)"
                >
                  YES
                </button>
                <button
                  class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                  @click="handleConfirm(false)"
                >
                  CANCEL
                </button>
              </div>
            </div>
          </div>
        </ModalBasic>
        <OnboardModal
          :modalOpen="isModalOpen"
          :OpMode="devMode"
          :restartDone="isRestartDone"
          :preventBackdropClose="true"
          @close-modal="handleCloseModal"
          @restart-validation="restart"
        />
        <LoadingModal
          :isOpen="isStartingService"
          title="Starting Diagnostic Service"
          :message="serviceLoadingMessage"
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
import { useAuthStore } from "@/store/auth"; // Pinia Store
import { useSetupStore } from "@/store/setup"; // Pinia Store
import Sidebar from "../common/SideBar3.vue";
import Header from "../common/Header.vue";
import Footer from "../common/Footer.vue";
import { useRouter } from "vue-router";
//import SettingsSidebar from '../../partials/settings/SettingsSidebar.vue'
import PlansPanel from "../../partials/inners/setting/PlansPanel.vue";
import BillingPanel from "../../partials/inners/setting/BillingPanel.vue";
import ChannelPanel from "../../partials/inners/setting/ChannelPanel.vue";
import AdminPanel from "../../partials/inners/setting/AdminPanel.vue";
import AccountPanel from "../../partials/inners/setting/AccountPanel.vue";
import ModalBasic from "../common/ModalBasic.vue";
import ModalBlank from "../common/ModalBlank.vue";
import CommandPanel from "../../partials/inners/setting/CommandPanel.vue";
import { useInputDict } from "@/composables/useInputDict";
import { useI18n } from "vue-i18n"; //
import SettingsSidebar2 from "../../partials/inners/setting/SettingsSidebar2.vue";
import OnboardModal from "../../components/OnboardingModal.vue";
import LoadingModal from "../../components/LoadingModal.vue";
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
    const errorMessage = ref(""); // ✅ 에러 메시지 변수 추가
    const isReady = ref(false);
    const isModalOpen = ref(false);
    const mode = ref(props.mode);
    const checkNameplateflag = ref(false);
    const isRestartDone = ref(false);
    const isSaving = ref(false); // ✅ 저장 중 상태 추가
    const isStartingService = ref(false);
    const serviceLoadingMessage = ref("");

    //const langset = computed(() => authStore.getLang);
    const isAdmin = computed(() => {
      if (parseInt(authStore.getUserRole) > 1) return true;
      else return false;
    });

    function askNameplateConfirm(channels) {
      const channelList = channels.join(", ");
      nameplateConfirmMessage.value =
        t("config.comfirmtext1") +
        ` ${channelList}.\n` +
        t("config.comfirmtext2");
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
      // status_Info,
    } = useInputDict();

    const devMode = computed(() => authStore.getOpMode);
    const channel = computed(() => props.channel || route.params.channel);

    // FTP와 Diagnosis 상호 배타적 상태 계산
    const isFTPEnabled = computed(() => {
      return (
        inputDict.value.useFuction?.ftp === 1 ||
        inputDict.value.useFuction?.ftp === true
      );
    });

    const isDiagnosisEnabled = computed(() => {
      const isMainDiagnosisEnabled =
        inputDict.value.useFuction?.diagnosis_main === true ||
        inputDict.value.useFuction?.diagnosis_main === 1;
      const isSubDiagnosisEnabled =
        inputDict.value.useFuction?.diagnosis_sub === true ||
        inputDict.value.useFuction?.diagnosis_sub === 1;
      const isMainChannelEnabled =
        channel_main.value?.Enable === 1 || channel_main.value?.Enable === true;
      const isSubChannelEnabled =
        channel_sub.value?.Enable === 1 || channel_sub.value?.Enable === true;

      // Main 채널 진단 활성화 조건: Main 채널이 활성화되고 Main 진단이 활성화된 경우
      const mainDiagnosisActive =
        isMainDiagnosisEnabled && isMainChannelEnabled;

      // Sub 채널 진단 활성화 조건: Sub 채널이 활성화되고 Sub 진단이 활성화된 경우
      const subDiagnosisActive = isSubDiagnosisEnabled && isSubChannelEnabled;

      // 둘 중 하나라도 활성화되면 true
      return mainDiagnosisActive || subDiagnosisActive;
    });

    // 충돌 경고 표시 여부
    const showConflictWarning = computed(() => {
      return isFTPEnabled.value && isDiagnosisEnabled.value;
    });

    // Diagnosis 사용 여부 계산 (Main 또는 Sub 중 하나라도 체크되면 true)
    const showDiagnosis = computed(() => {
      return (
        inputDict.value.useFuction?.diagnosis_main ||
        inputDict.value.useFuction?.diagnosis_sub
      );
    });

    watch(
      () => channel_sub.value?.Enable,
      (newEnable, oldEnable) => {
        // 값을 boolean으로 정규화
        const isNewEnabled = newEnable === true || newEnable === 1;
        const wasOldEnabled = oldEnable === true || oldEnable === 1;

        // 보조채널이 활성화에서 비활성화로 변경될 때만
        if (wasOldEnabled && !isNewEnabled) {
          // 전력품질과 진단 모두 비활성화
          //channel_sub.value.PowerQuality = false;
          inputDict.value.useFuction.diagnosis_sub = false;
        }
      }
    );

    // Diagnosis 표시 여부 계산 (devMode에 따라 결정)
    const showDiagnosisOption = computed(() => {
      switch (devMode.value) {
        case "device0":
        case "server":
          return false;
        default:
          return true;
      }
    });

    // FTP 버튼 클래스 동적 계산
    const getFTPButtonClass = () => {
      if (isDiagnosisEnabled.value || isSaving.value) {
        // Diagnosis가 활성화되어 있거나 저장 중이면 비활성화 스타일
        return "bg-gray-400 text-gray-600 cursor-not-allowed dark:bg-gray-600 dark:text-gray-400 opacity-50";
      } else if (inputDict.value.useFuction.ftp) {
        // FTP가 활성화되어 있으면 활성화 스타일
        return "bg-lime-900 text-lime-100 hover:bg-lime-800 dark:bg-lime-100 dark:text-lime-800 dark:hover:bg-white";
      } else {
        // 기본 스타일
        return "bg-gray-600 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white";
      }
    };

    // Diagnosis 버튼 클래스 동적 계산
    const getDiagnosisButtonClass = (channelType) => {
      if (isFTPEnabled.value || isSaving.value) {
        // FTP가 활성화되어 있거나 저장 중이면 비활성화 스타일
        return "bg-gray-400 text-gray-600 cursor-not-allowed dark:bg-gray-600 dark:text-gray-400 opacity-50";
      } else if (inputDict.value.useFuction[`diagnosis_${channelType}`]) {
        // Diagnosis가 활성화되어 있으면 활성화 스타일
        return "bg-lime-900 text-lime-100 hover:bg-lime-800 dark:bg-lime-100 dark:text-lime-800 dark:hover:bg-white";
      } else {
        // 기본 스타일
        return "bg-gray-600 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white";
      }
    };

    // FTP 토글 함수
    const toggleFTP = () => {
      if (isSaving.value) return; // 저장 중이면 실행 안 함
      inputDict.value.useFuction.ftp =
        inputDict.value.useFuction.ftp === 1 ? 0 : 1;
    };

    // Diagnosis 토글 함수
    const toggleDiagnosis = (channelType) => {
      if (isSaving.value) return; // 저장 중이면 실행 안 함

      // Sub 채널의 경우 채널이 Enable되어 있는지 확인
      if (channelType === "sub" && !channel_sub.value?.Enable) {
        alert(
          "Sub 채널이 비활성화되어 있습니다. 먼저 Sub 채널을 활성화해주세요."
        );
        return;
      }

      inputDict.value.useFuction[`diagnosis_${channelType}`] =
        !inputDict.value.useFuction[`diagnosis_${channelType}`];

      if (inputDict.value.useFuction[`diagnosis_${channelType}`]) {
        if (!checkSmart()) {
          if (
            confirm(
              "Not running diagnostic service. Do you want to run service?"
            )
          ) {
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
        if (response.data.success) {
          return true;
        } else {
          return false;
        }
      } catch (error) {
        console.error(error);
        return false;
      }
    };
    const manageSmart = async (mode) => {
      try {
        if (parseInt(mode) == 1) {
          isStartingService.value = true; // ⭐ 로딩 모달 표시
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
        isStartingService.value = false; // ⭐ 로딩 모달 닫기
      }
    };

    // showDiagnosis 변경 시 useDiagnosis도 업데이트
    watch(
      () => showDiagnosis.value,
      (newVal) => {
        useDiagnosis.value = newVal;
      },
      { immediate: true }
    );

    // Main/Sub 체크박스와 currentDiagnosis 연동
    watch(
      () => inputDict.value.useFuction?.diagnosis_main,
      (newVal) => {
        currentDiagnosis.value.Main = newVal;
      },
      { immediate: true }
    );

    watch(
      () => inputDict.value.useFuction?.diagnosis_sub,
      (newVal) => {
        currentDiagnosis.value.Sub = newVal;
      },
      { immediate: true }
    );

    watch(
      () => [route.params.channel, route.params.mode],
      ([newChannel, newMode]) => {
        channel.value = newChannel;
        mode.value = newMode;
      }
    );

    // useDiagnosis 상태 변화 감지
    // watch(
    //   () => useDiagnosis.value,
    //   (newVal) => {
    //     if (useDiagnosis.value) GetDiagnosisSetting();
    //   },
    //   { immediate: true }
    // );
    watch(
      () => useDiagnosis.value,
      async (newVal, oldVal) => {
        // false → true로 변경될 때만 (진단 기능 켜질 때)
        if (newVal && !oldVal) {
          const isRunning = await checkSmart();

          if (!isRunning) {
            const confirmed = confirm(
              "Not running diagnostic service. Do you want to run diagnostic service?"
            );

            if (confirmed) {
              const started = await manageSmart(1); // 여기서 로딩 모달 자동 표시

              if (!started) {
                // 서비스 시작 실패 시 진단 다시 끄기
                inputDict.value.useFuction.diagnosis_main = false;
                inputDict.value.useFuction.diagnosis_sub = false;
                console.error("스마트 서비스 시작 실패");
                return;
              }
            } else {
              // 사용자가 취소 시 진단 다시 끄기
              inputDict.value.useFuction.diagnosis_main = false;
              inputDict.value.useFuction.diagnosis_sub = false;
              return;
            }
          }

          // 서비스 확인 완료 후 설정 가져오기
          GetDiagnosisSetting();
        }
      }
    );

    // FTP와 Diagnosis 충돌 감지 및 자동 해제
    watch(
      () => [
        isFTPEnabled.value,
        isDiagnosisEnabled.value,
        channel_sub.value?.Enable,
      ],
      ([ftpEnabled, diagnosisEnabled, subChannelEnabled]) => {
        if (ftpEnabled && diagnosisEnabled) {
          console.warn(
            "⚠️ FTP와 Diagnosis가 동시에 활성화되었습니다. 충돌을 해결해주세요."
          );
        }
      },
      { immediate: true }
    );

    const handleFileUpload = (event) => {
      selectedFile.value = event.target.files[0]; // 파일 객체 저장
    };

    const upload = async () => {
      if (!selectedFile.value) {
        message.value = "파일을 선택하세요!";
        return;
      }

      const formData = new FormData();
      formData.append("file", selectedFile.value);
      //console.log(formData);
      try {
        const response = await axios.post("/setting/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        if (response.data.passOK == "1") {
          message.value = "Upload Success : " + response.data.file_path;
          feedbackModalOpen.value = false;
          await GetSettingData(); // ✅ 업로드 성공 후 GetSetting 실행
        } else {
          message.value = response.data.error;
        }
      } catch (error) {
        message.value = "업로드 실패: " + error.response.data.error;
      }
    };

    const download = async () => {
      try {
        const response = await axios.get("/setting/download", {
          responseType: "blob", // 서버에서 파일을 바이너리 형식으로 받아옴
        });

        // Blob 객체를 이용해 다운로드 링크를 생성
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "setting.json"); // 다운로드할 파일 이름 설정
        document.body.appendChild(link);
        link.click();

        // 링크 제거
        document.body.removeChild(link);

        message.value = "Download Success!";
      } catch (error) {
        message.value = "다운로드 실패: " + error.response.data.error;
      }
    };

    const formattedChannel = computed(() => {
      if (mode.value == "Device") {
        if (channel.value === "General") {
          return "General";
        } else if (channel.value === "Main") {
          return "Main Channel";
        } else if (channel.value === "Sub") {
          return "Sub Channel";
        } else {
          return "Command";
        }
      } else {
        if (channel.value == "User") return "User Management";
        else if (channel.value == "APIUser") return "API User Management";
        else return "Account";
      }
    });

    const apply = async () => {
      if (isSaving.value) {
        return; // 저장 중이면 Apply 불가
      }
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
      if (
        inputDict.value.useFuction.diagnosis_main ||
        inputDict.value.useFuction.diagnosis_sub
      ) {
        try {
          const response = await axios.get(`/setting/restartasset`);
          //console.log("Restart Response:", response);

          if (response.data.status === "1") {
            if (response.data.success) {
              const servicflag = await serviceRestart(
                "restart",
                "SmartSystems"
              );
              //const apiflag = await serviceRestart("restart", "SmartAPI");
              if (servicflag["result"]) {
                alert("✅ Service restarted successfully");
                //isModalOpen.value = false;
                isRestartDone.value = true;
              } else {
                alert("❌ SmartSystem Restart failed");
              }
            } else {
              //isModalOpen.value = false;
              isRestartDone.value = true;

              alert("✅ System restarted successfully");
            }
          } else {
            //isModalOpen.value = false;
            //isRestartDone.value = true;

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

    const GetSetting = async () => {
      try {
        const response = await axios.get(
          `/setting/getSettingData/${channel.value}`
        );

        if (response.data.passOK == 1) {
          if (channel.value == "General") {
            Object.assign(inputDict.value, response.data.data); // ✅ 기존 데이터 유지하면서 새로운 데이터 병합
            //console.log(response.data.data);
          } else if (channel.value == "Main") {
            Object.assign(channel_main.value, response.data.data); // ✅ 기존 데이터 유지하면서 새로운 데이터 병합
            //console.log(response.data.data);
          } else {
            Object.assign(channel_sub.value, response.data.data[0]); // ✅ 기존 데이터 유지하면서 새로운 데이터 병합
            //console.log(response.data.data[0]);
          }

          setupStore.setsetupFromFile(true);
          //console.log("Data Loaded!");
        }
      } catch (error) {
        console.error("데이터 가져오기 실패:", error);
        errorMessage.value = "데이터를 불러오는 중 오류가 발생했습니다.";
      }
    };

    // Diagnosisfile 데이터 불러오기
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

    const GetSettingData = async () => {
      try {
        const response = await axios.get(`/setting/getSetting`);

        if (response.data.passOK == 1) {
          setupDict.value = response.data.data;
          Object.assign(inputDict.value, setupDict.value["General"]);
          Object.assign(channel_main.value, setupDict.value["main"]);
          Object.assign(channel_sub.value, setupDict.value["sub"]);
          // if ('status_Info' in setupDict.value) {
          //   Object.assign(status_Info, setupDict.value["status_Info"]);
          // }
          setupStore.setsetupFromFile(true);
          //console.log(status_Info);
        }
      } catch (error) {
        console.error("데이터 가져오기 실패:", error);
        //errorMessage.value = "데이터를 불러오는 중 오류가 발생했습니다.";
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
          } else {
            console.error("❌ Error: logout 함수가 정의되지 않음!");
          }
          dangerModalOpen.value = false;
        } else {
          console.error("데이터 가져오기 실패:", response.data.msg);
        }
      } catch (error) {
        console.error("데이터 가져오기 실패:", error);
      }
    };

    const saveAllSettings = async () => {
      try {
        let errorMessages = [];

        // === 1. General 설정 저장 ===
        let generalSuccess = true;
        try {
          const generalData = { ...inputDict.value };

          // useFuction 필드들을 숫자로 변환
          if (generalData.useFuction) {
            generalData.useFuction.ftp =
              generalData.useFuction.ftp === true ||
              generalData.useFuction.ftp === 1
                ? 1
                : 0;
            generalData.useFuction.sntp =
              generalData.useFuction.sntp === true ||
              generalData.useFuction.sntp === 1
                ? 1
                : 0;
          }

          // modbus rtu_use 필드를 숫자로 변환
          if (generalData.modbus && generalData.modbus.rtu_use !== undefined) {
            generalData.modbus.rtu_use =
              generalData.modbus.rtu_use === true ||
              generalData.modbus.rtu_use === 1
                ? 1
                : 0;
          }
          const generalResponse = await axios.post(
            "/setting/savefile/General",
            generalData,
            {
              headers: { "Content-Type": "application/json;charset=utf-8" },
              withCredentials: true,
            }
          );

          if (!generalResponse.data || generalResponse.data["status"] !== "1") {
            generalSuccess = false;
            const errorMsg =
              generalResponse.data?.error || "General settings save failed";
            errorMessages.push(`General settings: ${errorMsg}`);
          }
        } catch (err) {
          generalSuccess = false;
          const errorMsg =
            err.response?.data?.error ||
            err.message ||
            "General settings save error";
          errorMessages.push(`General settings: ${errorMsg}`);
          console.error("General 저장 실패:", err);
        }

// === 2. Diagnosis 설정 저장 ===
        let diagnosisSuccess = true;
        if (useDiagnosis.value) {
          try {
            if (
              diagnosisData.value &&
              Object.keys(diagnosisData.value).length > 0
            ) {
              const diagnosisResponse = await axios.post(
                "/setting/setDiagnosisSetting",
                diagnosisData.value,
                {
                  headers: { "Content-Type": "application/json" },
                  withCredentials: true,
                }
              );

              const { status, success, error } = diagnosisResponse.data || {};

              // status가 0이면 무조건 실패
              if (status === "0" || status === 0) {
                diagnosisSuccess = false;
                const errorList = Array.isArray(error) ? error : [error || "API request failed"];
                errorMessages.push(`Check Smart API Service: \n`);
                errorMessages.push(...errorList.map(err => `Diagnosis settings: ${err}`));
              }
              // status가 1이면서 success가 false면 실패
              else if ((status === "1" || status === 1) && !success) {
                diagnosisSuccess = false;
                const errorList = Array.isArray(error) ? error : [error || "Diagnosis settings save failed"];
                errorMessages.push(...errorList.map(err => `Diagnosis settings: ${err}`));
              }
            }

            if (
              advancedData.value &&
              Object.keys(advancedData.value).length > 0
            ) {
              const advancedResponse = await axios.post(
                "/setting/setDiagnosisProfile",
                advancedData.value,
                {
                  headers: { "Content-Type": "application/json" },
                  withCredentials: true,
                }
              );

              const { status, success, error } = advancedResponse.data || {};

              // status가 0이면 무조건 실패
              if (status === "0" || status === 0) {
                diagnosisSuccess = false;
                const errorList = Array.isArray(error) ? error : [error || "API request failed"];
                errorMessages.push(`Check Smart API Service: \n`);
                errorMessages.push(...errorList.map(err => `Advanced diagnosis settings: ${err}`));
              }
              // status가 1이면서 success가 false면 실패
              else if ((status === "1" || status === 1) && !success) {
                diagnosisSuccess = false;
                const errorList = Array.isArray(error) ? error : [error || "Advanced diagnosis settings save failed"];
                errorMessages.push(...errorList.map(err => `Advanced diagnosis settings: ${err}`));
              }
            }
          } catch (err) {
            diagnosisSuccess = false;
            const errors = err.response?.data?.error || [err.message || "Diagnosis settings save error"];
            const errorList = Array.isArray(errors) ? errors : [errors];
            errorMessages.push(...errorList.map(e => `Diagnosis settings: ${e}`));
            console.error("Diagnosis 저장 실패:", err);
          }
        }

        // === 3. Main Channel 설정 저장 ===
        const mainResult = await saveChannelData(channel_main.value, "Main");
        if (!mainResult.success) {
          errorMessages.push(`Main Channel: ${mainResult.error}`);
        }

        // === 4. Sub Channel 설정 저장 ===
        const subResult = await saveChannelData(channel_sub.value, "Sub");
        if (!subResult.success) {
          errorMessages.push(`Sub Channel: ${subResult.error}`);
        }
        // console.log(devMode.value)
        // console.log(status_Info);
        // if(devMode.value == 'device2'){
        //   const statusResult = await saveStatusData(status_Info);
        //     if (!statusResult.success) {
        //       errorMessages.push(`Status Info: ${statusResult.error}`);
        //     }
        // }

        // === 5. 결과 알림 ===
        // channel_main.value나 channel_sub.value에 
        // JSON으로 변환할 수 없는 값이 있을 수 있음
        // console.log(JSON.stringify(channel_main.value)); // 에러 확인
        // console.log(JSON.stringify(channel_sub.value));
        if (
          generalSuccess &&
          diagnosisSuccess &&
          mainResult.success &&
          subResult.success
        ) {
          alert("✅ All settings have been saved successfully!");
        } else {
          //console.log("generalSucces:", generalSuccess,'diagnosisSuccess', diagnosisSuccess,'mainResult.success', mainResult.success, subResult.success);
          let errorMsg = "❌ Some settings failed to save:\n";
          errorMessages.forEach((msg) => {
            errorMsg += `- ${msg}\n`;
          });
          alert(errorMsg);
        }
      } catch (err) {
        console.log(err);
        const errorMsg =
          err.response?.data?.error || err.message || "Unknown error occurred";
        alert(`Error occurred while saving: ${errorMsg}`);
      }

      setupStore.setApplySetup(false);
      await setupStore.checkSetting();
    };

const savefile = async () => {
  // 이미 저장 중이면 중단
  if (isSaving.value) {
    return;
  }

  // 충돌 상황 체크 - 업데이트된 로직
  if (showConflictWarning.value) {
    alert(
      "Cannot use Waveform FTP and Diagnosis simultaneously. Please disable one of them."
    );
    return;
  }

  try {
    isSaving.value = true; // ✅ 저장 시작

    // 진단 미사용 채널의 Asset 등록 체크
    for (const channelName in diagnosis_detail.value) {
      const channelData = diagnosis_detail.value[channelName];

      // Main/Sub 채널별 diagnosis 사용 여부 확인
      const isDiagnosisEnabledForChannel =
        channelName === "main"
          ? inputDict.value.useFuction.diagnosis_main
          : inputDict.value.useFuction.diagnosis_sub;

      // 진단이 OFF인데 Asset이 등록되어 있는 경우
      if (
        !isDiagnosisEnabledForChannel &&
        channelData.assetName &&
        channelData.assetName !== ""
      ) {
        alert(
          `Diagnosis is disabled for ${channelName} channel, but an asset (${channelData.assetName}) is registered. Please remove the asset or enable diagnosis.`
        );
        return;
      }
    }

    // 1. 먼저 nameplate configuration 체크 - 가장 먼저 실행
    let needsNameplateConfirmation = false;
    let nameplateChannels = [];

    for (const channelName in diagnosis_detail.value) {
      const channelData = diagnosis_detail.value[channelName]; // main 또는 sub 데이터

      // Main/Sub 채널별 diagnosis 사용 여부 확인
      const isDiagnosisEnabledForChannel =
        channelName === "main"
          ? inputDict.value.useFuction.diagnosis_main
          : inputDict.value.useFuction.diagnosis_sub;

      // assetName과 tableData 검증 및 nameplate 체크
      if (
        channelData.use &&
        isDiagnosisEnabledForChannel &&
        channelData.assetName &&
        channelData.assetName !== "" &&
        channelData.tableData &&
        Array.isArray(channelData.tableData) &&
        channelData.tableData.length > 0
      ) {
        try {
          const combinedData = [
            ...channelData.tableData,
            ...(channelData.modalData &&
            Array.isArray(channelData.modalData)
              ? channelData.modalData
              : []),
          ];
          const nameplateFlag = await checkNameplateConfig(
            combinedData,
            channelData.assetName
          );
          if (nameplateFlag) {
            needsNameplateConfirmation = true;
            nameplateChannels.push(
              `${channelName} channel(${channelData.assetName})`
            );
          }
        } catch (error) {
          console.error(
            `Error checking nameplate for ${channelName}:`,
            error
          );
          alert(
            `An error occurred while checking nameplate configuration for ${channelName}: ${error.message}`
          );
          return;
        }
      }
    }

    // 2. Nameplate 변경이 필요한 경우 사용자 확인
    if (needsNameplateConfirmation) {
      const userConfirmed = await askNameplateConfirm(nameplateChannels);
      if (!userConfirmed) return;
    }

    // 3. Nameplate 및 Asset Params 저장
    for (const channelName in diagnosis_detail.value) {
      const channelData = diagnosis_detail.value[channelName];
      const isDiagnosisEnabledForChannel =
        channelName === "main"
          ? inputDict.value.useFuction.diagnosis_main
          : inputDict.value.useFuction.diagnosis_sub;

      // Nameplate 설정 저장
      if (
        channelData.use &&
        isDiagnosisEnabledForChannel &&
        channelData.assetName &&
        channelData.assetName !== "" &&
        channelData.tableData &&
        Array.isArray(channelData.tableData) &&
        channelData.tableData.length > 0
      ) {
        const combinedData = [
          ...channelData.tableData,
          ...(channelData.modalData && Array.isArray(channelData.modalData)
            ? channelData.modalData
            : []),
        ];

        const nameplateResult = await setNameplateConfig(
          combinedData,
          channelData.assetName,
          channelName
        );
        
        if (!nameplateResult.success) {
          alert(`❌ Failed to save ${channelName} channel nameplate settings:\n${nameplateResult.error}`);
          return;
        }
      }

      // Asset Params 저장
      if (
        channelData.use &&
        isDiagnosisEnabledForChannel &&
        channelData.assetName &&
        channelData.assetName !== "" &&
        channelData.paramData &&
        Array.isArray(channelData.paramData) &&
        channelData.paramData.length > 0
      ) {
        const paramsResult = await setAssetParams(
          channelData.paramData,
          channelData.assetName,
          channelName
        );
        
        if (!paramsResult.success) {
          alert(`❌ Failed to save ${channelName} channel asset parameters:\n${paramsResult.error}`);
          return;
        }
      }
    }

    if (devMode.value === "device0") {
      const device0Params = [
        "Temperature",
        "Frequency",
        "Line Voltage",
        "Phase Voltage",
        "Current",
        "Unbalance",
        "PF",
        "THD",
        "TDD",
        "Power",
      ];

      if (!channel_main.value.trendInfo) {
        channel_main.value.trendInfo = {};
      }
      channel_main.value.trendInfo.params = [...device0Params];

      if (!channel_sub.value.trendInfo) {
        channel_sub.value.trendInfo = {};
      }
      channel_sub.value.trendInfo.params = [...device0Params];
    }

    // 저장 진행
    await saveAllSettings();
  } catch (error) {
    console.error("Save error:", error);
    alert(`An error occurred while saving: ${error.message}`);
  } finally {
    isSaving.value = false;
  }
};
    const checkNameplateConfig = async (tableData, assetName) => {
      try {
        if (!Array.isArray(tableData) || tableData.length === 0) {
          console.error("Invalid or empty tableData:", tableData);
          return false;
        }

        if (!assetName || assetName === "") {
          console.error("No asset name provided");
          return false;
        }

        const plainTableData = tableData.map((item) => ({ ...item }));

        //console.log(plainTableData);

        const response = await axios.post(
          `/setting/checkAssetConfig/${assetName}`,
          plainTableData,
          {
            headers: { "Content-Type": "application/json" },
          }
        );

        if (response.data.success) {
          return response.data.result;
        } else {
          console.log("Server did not respond properly");
          return false;
        }
      } catch (error) {
        console.error("Error in checkNameplateConfig:", error);
        return false;
      }
    };

const setNameplateConfig = async (tableData, assetName, channelName) => {
  try {
    if (!Array.isArray(tableData) || tableData.length === 0) {
      console.error("Invalid or empty tableData:", tableData);
      return { success: false, error: "Invalid or empty tableData" };
    }

    if (!assetName || assetName === "") {
      console.error("No asset name provided");
      return { success: false, error: "No asset name provided" };
    }

    const plainTableData = tableData.map((item) => ({ ...item }));

    const response = await axios.post(
      `/setting/setAssetConfig/${assetName}`,
      plainTableData,
      {
        headers: { "Content-Type": "application/json" },
      }
    );

    const { status, success, error } = response.data || {};

    // status가 0이면 무조건 실패
    if (status === "0" || status === 0) {
      const errorMsg = Array.isArray(error)
        ? error.join('\n')
        : error || "API request failed";
      console.error(`❌ Failed to save ${channelName} channel asset settings:`, errorMsg);
      return { success: false, error: `Check Smart API Service: ${errorMsg}` };
    }

    // status가 1이면서 success가 false면 실패
    if ((status === "1" || status === 1) && !success) {
      const errorMsg = Array.isArray(error)
        ? error.join('\n')
        : error || "unknown error";
      console.error(`❌ Failed to save ${channelName} channel asset settings:`, errorMsg);
      return { success: false, error: errorMsg };
    }

    // status가 1이면서 success가 true면 성공
    if ((status === "1" || status === 1) && success) {
      console.log(`✅ Successfully saved ${channelName} channel asset settings`);
      return { success: true };
    }

    return { success: false, error: "Unknown response status" };
  } catch (error) {
    console.error(`Error occurred while saving ${channelName} channel asset:`, error);
    return { success: false, error: error.message || "Unknown error" };
  }
};

    const checkTableData = async (tableData, assetName, channelName) => {
      try {
        checkNameplateflag.value = await checkNameplateConfig(
          tableData,
          assetName
        );
        //console.log('checkTableData - ', checkNameplateflag.value);
        if (checkNameplateflag.value) {
          // 사용자에게 확인 팝업 표시
          const userConfirmed = confirm(
            `The changed settings will delete all ${channelName} previous calculations. Would you like to proceed?`
          );

          if (userConfirmed) {
            await setNameplateConfig(tableData, assetName, channelName);
          } else {
            alert("Nameplate configuration has been canceled.");
            return false; // 사용자가 취소한 경우
          }
        }
        return true;
      } catch (error) {
        console.error(
          `Error occurred while checking table data for ${channelName}:`,
          error
        );
        alert(
          `An error occurred during nameplate configuration for ${channelName}: ${error.message}`
        );
        return false;
      }
    };

const setAssetParams = async (paramData, assetName, channelName) => {
  try {
    if (!Array.isArray(paramData) || paramData.length === 0) {
      console.error("Invalid or empty paramData:", paramData);
      return { success: false, error: "Invalid or empty paramData" };
    }

    if (!assetName || assetName === "") {
      console.error("No asset name provided");
      return { success: false, error: "No asset name provided" };
    }

    const plainTableData = paramData.map((item) => ({ ...item }));

    const response = await axios.post(
      `/setting/setAssetParams/${assetName}`,
      plainTableData,
      {
        headers: { "Content-Type": "application/json" },
      }
    );

    const { status, success, error } = response.data || {};

    // status가 0이면 무조건 실패
    if (status === "0" || status === 0) {
      const errorMsg = Array.isArray(error)
        ? error.join('\n')
        : error || "API request failed";
      console.error(`❌ Failed to save ${channelName} channel asset parameters:`, errorMsg);
      return { success: false, error: `Check Smart API Service: ${errorMsg}` };
    }

    // status가 1이면서 success가 false면 실패
    if ((status === "1" || status === 1) && !success) {
      const errorMsg = Array.isArray(error)
        ? error.join('\n')
        : error || "unknown error";
      console.error(`❌ Failed to save ${channelName} channel asset parameters:`, errorMsg);
      return { success: false, error: errorMsg };
    }

    // status가 1이면서 success가 true면 성공
    if ((status === "1" || status === 1) && success) {
      console.log(`✅ Successfully saved ${channelName} channel asset parameters`);
      return { success: true };
    }

    return { success: false, error: "Unknown response status" };
  } catch (error) {
    console.error(`Error occurred while saving ${channelName} channel asset parameters:`, error);
    return { success: false, error: error.message || "Unknown error" };
  }
};
    // 헬퍼 함수
    const saveChannelData = async (channelData, channelName) => {
      try {
        const data = { ...channelData };
        console.log('saveChannelData - ', data);
        data.channel = channelName;
        data.Enable = data.Enable === true || data.Enable === 1 ? 1 : 0;
        data.PowerQuality =
          data.PowerQuality === true || data.PowerQuality === 1 ? 1 : 0;
        if (data.hasOwnProperty('useDO')) {
          data.useDO = (data.useDO === true || data.useDO === 1) ? 1 : 0;
        }
        if (data.hasOwnProperty('confStatus')) {
          data.confStatus = (data.confStatus === true || data.confStatus === 1) ? 1 : 0;
        }

        // 🔥 useAI도 있다면 0 또는 1로 변환
        if (data.hasOwnProperty('useAI')) {
          data.useAI = (data.useAI === true || data.useAI === 1) ? 1 : 0;
        }
      // 🔥 useDO가 false이면 status_Info 초기화
        const isUseDOEnabled = data.confStatus === 1 || data.confStatus === true;
        if (!isUseDOEnabled && data.status_Info) {
          data.status_Info.diagnosis = [];
          data.status_Info.pq = [];    
          data.status_Info.faults = [];
          data.status_Info.events = [];
        }
        // 데이터 타입 변환
        for (const key in data.ctInfo) {
          if (key == "direction") {
            for (let i = 0; i < data.ctInfo.direction.length; i++) {
              data.ctInfo[key][i] = parseInt(data.ctInfo.direction[i]);
            }
          } else if (key === "inorminal" ) {
            // inorminal과 startingcurrent는 소수점 유지
            data.ctInfo[key] = parseFloat(data.ctInfo[key]);
          } else {
            if (Object.prototype.hasOwnProperty.call(data.ctInfo, key)) {
              const value = data.ctInfo[key];
              data.ctInfo[key] = parseInt(value);
            }
          }
        }
        for (const key in data.ptInfo) {
          if (Object.prototype.hasOwnProperty.call(data.ptInfo, key)) {
            const value = data.ptInfo[key];
            data.ptInfo[key] = parseInt(value);
          }
        }
        for (const key in data.eventInfo) {
          if (Object.prototype.hasOwnProperty.call(data.eventInfo, key)) {
            const value = data.eventInfo[key];
            data.eventInfo[key] = parseInt(value);
          }
        }
        //console.log('save channel', data);
        const response = await axios.post(
          `/setting/savefile/${channelName}`,
          data,
          {
            headers: { "Content-Type": "application/json;charset=utf-8" },
            withCredentials: true,
          }
        );

        if (response.data && response.data["status"] === "1") {
          return { success: true };
        } else {
          const errorMsg =
            response.data?.error || `${channelName} Channel save failed`;
          return { success: false, error: errorMsg };
        }
      } catch (err) {
        console.error(`${channelName} Channel 저장 실패:`, err);
        const errorMsg =
          err.response?.data?.error ||
          err.message ||
          `${channelName} Channel save error`;
        return { success: false, error: errorMsg };
      }
    };

    const saveStatusData = async (statusData) => {
        const sendData = {...statusData}
        const response = await axios.post(
          `/setting/savefile/status`,
          sendData,
          {
            headers: { "Content-Type": "application/json;charset=utf-8" },
            withCredentials: true,
          }
        );
        if (response.data && response.data["status"] === "1") {
          return { success: true };
        } else {
          const errorMsg =
            response.data?.error || `${channelName} StatusSetting save failed`;
          return { success: false, error: errorMsg };
        }
    };

    onMounted(() => {
      GetSettingData();
    });

    provide("inputDict", inputDict);
    provide("channel_main", channel_main);
    provide("channel_sub", channel_sub);
    provide("useDiagnosis", useDiagnosis);
    provide("diagnosisData", diagnosisData);
    provide("advancedData", advancedData);
    provide("currentDiagnosis", currentDiagnosis);
    provide("devMode", devMode);
    provide("saveAllSettings", saveAllSettings);
    provide("changeDiagnosis", changeDiagnosis);
    provide("checkNameplateflag", checkNameplateflag);
    provide("diagnosis_detail", diagnosis_detail);
    provide("GetSettingData", GetSettingData);
    //provide("status_Info", status_Info);

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
      savefile,
      isModalOpen,
      handleCloseModal,
      // 새로 추가된 상호배타 로직
      isFTPEnabled,
      isDiagnosisEnabled,
      showConflictWarning,
      getFTPButtonClass,
      getDiagnosisButtonClass,
      toggleFTP,
      toggleDiagnosis,
      restart,
      GetDiagnosisSetting,
      checkNameplateflag,
      diagnosis_detail,
      showNameplateConfirm,
      nameplateConfirmMessage,
      handleConfirm,
      isRestartDone,
      isSaving, // ✅ 추가
      isStartingService,
      serviceLoadingMessage,
    };
  },
};
</script>
