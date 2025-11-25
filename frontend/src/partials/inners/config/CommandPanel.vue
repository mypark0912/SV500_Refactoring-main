<template>
  <div class="grow">
    <!-- Panel body -->
    <div class="p-6">
      <h2 class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-5">
        {{ t("sidebar.system") }}
      </h2>

      <!-- General -->
      <div class="mb-6">
        <!-- Filters -->
        <div
          class="mt-4 flex gap-2 border-b border-gray-200 dark:border-gray-700/60 pb-4"
        ></div>
        <div
          v-if="message"
          class="text-sm text-gray-800 dark:text-gray-100 mt-2"
        >
          {{ message }}🙌
        </div>
      </div>

      <!-- Connected Apps cards -->
      <section class="pb-6 border-b border-gray-200 dark:border-gray-700/60">
        <div class="grid grid-cols-12 gap-6">
          <CommandItem
            :item="'Clear'"
            :channel="'Main'"
            @service-done="showMessage"
          />
          <CommandItem
            :item="'Clear'"
            :channel="'Sub'"
            @service-done="showMessage"
          />
        </div>
      </section>

      <!-- Settings Section -->
      <section
        class="mt-6 pb-6 border-b border-gray-200 dark:border-gray-700/60"
      >
        <div class="grid grid-cols-12 gap-6">
          <CommandItem :item="'Settings'" @service-done="showMessage" />

          <!-- Backup Download & Smart System Update 통합 카드 -->
          <div
            class="col-span-full xl:col-span-6 2xl:col-span-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-lg"
          ><div class="flex flex-col h-full p-5">
            <div class="flex flex-col gap-5">
              <header class="flex items-center mb-4">
                <h3
                  class="text-lg text-gray-800 dark:text-gray-100 font-semibold mr-4"
                >
                  {{t("config.system.title_4")}}
                </h3>
              </header>
              <!-- Backup Download 섹션 -->
              <div
                class="flex items-center gap-3 pb-3 border-b border-gray-200 dark:border-gray-700/60"
              >
                <label
                  class="text-sm text-gray-700 dark:text-gray-300 font-medium whitespace-nowrap"
                >
                  Backup Download
                </label>

                <select
                  v-if="devMode != 'device0'"
                  class="h-9 w-56 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                  v-model="modalSelectItem"
                >
                  <option value="all">SmartSystem All</option>
                  <option value="log">SmartSystem Log</option>
                  <option value="project">SmartSystem Project</option>
                  <option value="dbbackup">SmartSystem Dbbackup</option>
                  <option value="backup">SmartSystem Backup</option>
                  <option value="other">Other Backup</option>
                </select>
                <select
                  v-else
                  class="h-9 w-32 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                  v-model="modalSelectItem"
                >
                  <option value="all">All</option>
                  <option value="log">Log</option>
                  <option value="dbbackup">Dbbackup</option>
                </select>

                <a
                  :href="downloadUrl"
                  class="btn h-9 px-5 bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white flex items-center"
                  download
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    width="16"
                    height="16"
                    stroke-width="2"
                    class="mr-2"
                  >
                    <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2"></path>
                    <polyline points="7 11 12 16 17 11"></polyline>
                    <line x1="12" y1="4" x2="12" y2="16"></line>
                  </svg>
                  Download
                </a>
              </div>

              <!-- Smart System Update 섹션 -->
              <div class="flex items-center gap-3">
                <!-- 라디오 버튼 그룹 -->
                <label
                  class="text-sm text-gray-700 dark:text-gray-300 font-medium whitespace-nowrap"
                >
                  Smart System
                </label>
                <div class="flex items-center gap-3">
                  <label class="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="updateMode"
                      value="update"
                      v-model="updateMode"
                      :disabled="isUpdating"
                      class="w-4 h-4 text-violet-600 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:ring-violet-500 dark:focus:ring-violet-600 focus:ring-2 disabled:opacity-50"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300"
                      >Update</span
                    >
                  </label>

                  <label class="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="updateMode"
                      value="reinstall"
                      v-model="updateMode"
                      :disabled="isUpdating"
                      class="w-4 h-4 text-violet-600 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:ring-violet-500 dark:focus:ring-violet-600 focus:ring-2 disabled:opacity-50"
                    />
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300"
                      >Reinstall</span
                    >
                  </label>
                </div>

                <!-- Proceed 버튼 (마진 추가) -->
                <button
                  @click="handleSystemUpdate"
                  :disabled="isUpdating"
                  class="btn h-9 px-5 bg-blue-600 text-white hover:bg-blue-700 rounded-md flex items-center ml-6 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg
                    v-if="isUpdating"
                    class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
                  {{ isUpdating ? "Processing..." : "Proceed" }}
                </button>
              </div>
            </div>
          </div>

          </div>
        </div>
      </section>

      <!-- Update Confirmation Modal -->
      <Teleport to="body">
        <transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="opacity-0"
          enter-to-class="opacity-100"
          leave-active-class="transition ease-out duration-100"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div
            v-if="showUpdateModal"
            class="fixed inset-0 z-50 overflow-hidden flex items-center justify-center px-4 sm:px-6"
            role="dialog"
          >
            <!-- Background overlay -->
            <div
              class="fixed inset-0 bg-black bg-opacity-30 transition-opacity"
              @click="showUpdateModal = false"
            ></div>

            <!-- Modal dialog - 깔끔한 흰색 디자인 -->
            <div
              class="bg-white dark:bg-gray-800 rounded-lg shadow-2xl relative max-w-md w-full mx-auto z-50 p-8"
            >
              <!-- 경고 아이콘 -->
              <div class="flex justify-center mb-4">
                <div
                  class="w-16 h-16 rounded-full bg-yellow-100 dark:bg-yellow-900/20 flex items-center justify-center"
                >
                  <svg
                    class="w-8 h-8 text-yellow-600 dark:text-yellow-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    ></path>
                  </svg>
                </div>
              </div>

              <!-- 제목 -->
              <h3
                class="text-lg font-semibold text-gray-900 dark:text-gray-100 text-center mb-4"
              >
                {{ t("config.system.warnmessage1") }}
              </h3>

              <!-- 내용 -->
              <div class="text-center mb-6">
                <p
                  class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed"
                >
                  {{ t("config.system.warnmessage2") }}
                </p>
                <p
                  class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed mt-2"
                >
                  {{ t("config.system.warnmessage3") }}
                </p>
                <p
                  class="text-sm font-medium text-gray-900 dark:text-gray-100 mt-4"
                >
                  {{ t("config.system.warnmessage4") }}
                </p>
              </div>

              <!-- 버튼 -->
              <div class="flex justify-center gap-3">
                <button
                  @click="showUpdateModal = false"
                  class="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium text-sm"
                >
                  {{ t("config.system.cancel") }}
                </button>
                <button
                  @click="confirmUpdate"
                  class="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium text-sm"
                >
                  {{ t("config.system.confirm") }}
                </button>
              </div>
            </div>
          </div>
        </transition>
      </Teleport>

      <!-- Disk Status Section -->
      <section class="mt-6"></section>
    </div>
  </div>
</template>

<script>
import CommandItem from "../setting/CommandItem.vue";
import { onMounted, ref, watch, provide, computed, inject } from "vue";
import { useSetupStore } from "@/store/setup";
import { useAuthStore } from "@/store/auth";
import { useI18n } from "vue-i18n";
import axios from "axios";

export default {
  name: "ServicePannel",
  components: {
    CommandItem,
  },
  setup() {
    const { t } = useI18n();
    const setupStore = useSetupStore();
    const authStore = useAuthStore();
    const message = ref("");
    const health = ref("");
    const sysStatus = ref({});
    const diskStatus = ref([]);
    const modalSelectItem = ref("all");
    const GetSettingData = inject("GetSettingData");

    // 추가된 상태
    const updateMode = ref("update"); // 'update' or 'reinstall'
    const showUpdateModal = ref(false);
    const isUpdating = ref(false); // 업데이트 진행 중 상태

    provide("GetSettingData", GetSettingData);

    const showMessage = (text) => {
      message.value = text;
      // 3초 후 메시지 자동 삭제
      setTimeout(() => {
        message.value = "";
      }, 3000);
    };

    const ChannelState = computed(() => {
      const re = setupStore.getChannelSetting;
      return re.MainDiagnosis || re.SubDiagnosis;
    });

    const devMode = computed(() => authStore.getOpMode);

    const downloadUrl = computed(() => {
      const hostname = window.location.hostname;
      if (devMode.value != "device0") {
        if (modalSelectItem.value == "other")
          return `http://${hostname}:4000/setting/backup/download/${modalSelectItem.value}`;
        else
          return `http://${hostname}:5000/api/getFolder?name=${modalSelectItem.value}`;
      } else
        return `http://${hostname}:4000/setting/backup/download/${modalSelectItem.value}`;
    });

    // Smart System Update 처리
    const handleSystemUpdate = () => {
      if (updateMode.value === "reinstall") {
        showUpdateModal.value = true;
      } else {
        // Update 모드일 때 바로 실행
        performUpdate();
      }
    };

    const confirmUpdate = () => {
      showUpdateModal.value = false;
      performUpdate();
    };

    const performUpdate = async () => {
      isUpdating.value = true;

      // mode: 0 = update, 1 = reinstall
      const mode = updateMode.value === "reinstall" ? 1 : 0;

      try {
        const response = await axios.get(`/setting/updateSmartSystem/${mode}`);

        if (response.data.success) {
          showMessage(
            mode === 1
              ? t("config.system.reinstall_success") ||
                  "시스템 재설치가 완료되었습니다."
              : t("config.system.update_success") ||
                  "시스템 업데이트가 완료되었습니다."
          );

          // 재설치 후 페이지 새로고침 (선택사항)
          if (mode === 1) {
            setTimeout(() => {
              window.location.reload();
            }, 2000);
          }
        } else {
          showMessage(
            t("config.system.update_failed") ||
              "업데이트 실패: " + (response.data.message || "알 수 없는 오류")
          );
        }
      } catch (error) {
        console.error("Update failed:", error);
        showMessage(
          t("config.system.update_failed") ||
            "업데이트 실패: " + (error.response?.data?.message || error.message)
        );
      } finally {
        isUpdating.value = false;
      }
    };

    // Helper functions for disk status display
    const formatSize = (sizeInGB) => {
      if (sizeInGB >= 1024) {
        return (sizeInGB / 1024).toFixed(1) + " TB";
      }
      return sizeInGB.toFixed(1) + " GB";
    };

    const getUsagePercentage = (item) => {
      const used = item.totalGB - item.freeGB;
      return Math.round((used / item.totalGB) * 100);
    };

    const getProgressBarColor = (item) => {
      const usage = getUsagePercentage(item);
      if (usage >= 90) return "bg-red-500";
      if (usage >= 75) return "bg-yellow-500";
      return "bg-green-500";
    };

    const CheckAPI = async () => {
      try {
        const response = await axios.get("/setting/checkAPI");
        if (response.data.success) {
          health.value = response.data.data;
        } else {
          health.value = "";
        }
      } catch (error) {
        console.log(error);
        message.value = "Restful API Service is not running";
      }
    };

    const SysCheck = async () => {
      try {
        const response = await axios.get("/setting/SysCheck");
        if (response.data.success) {
          diskStatus.value = response.data.disk;
          sysStatus.value = response.data.data;
        } else {
          message.value = "System Check API is not respond";
        }
      } catch (error) {
        message.value = "System Check Failed";
        console.log(error);
      }
    };

    onMounted(() => {
      SysCheck();
    });

    provide("sysStatus", sysStatus);
    provide("health", health);

    // watch(
    //   () => ChannelState.value,
    //   (newVal, oldVal) => {
    //     if (newVal) {
    //       CheckAPI();
    //     } else {
    //       console.log("둘 다 비활성화됨");
    //     }
    //   },
    //   { immediate: true }
    // );

    return {
      message,
      showMessage,
      health,
      CheckAPI,
      sysStatus,
      diskStatus,
      ChannelState,
      devMode,
      formatSize,
      getUsagePercentage,
      getProgressBarColor,
      t,
      modalSelectItem,
      downloadUrl,
      updateMode,
      showUpdateModal,
      handleSystemUpdate,
      confirmUpdate,
      isUpdating, // 추가
    };
  },
};
</script>
