<template>
  <div class="grow">
    <!-- Panel body -->
    <div class="p-6">
      <h2 class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-5">
        {{ t("config.maintenance.header") }}
      </h2>

      <!-- General -->
      <div class="mb-6">
        <!-- Filters -->
        <div
          class="mt-4 flex gap-2 border-b border-gray-200 dark:border-gray-700/60 p-2 pb-4"
        >
          <div
            v-if="message"
            class="font-medium text-gray-800 dark:text-gray-100 mb-3"
          >
            {{ message }}🙌
          </div>
        </div>
      </div>

      <!-- Connected Apps cards -->
      <section class="pb-6 border-b border-gray-200 dark:border-gray-700/60">
        <div
          class="flex flex-col space-y-10 sm:flex-row sm:space-x-6 sm:space-y-0 md:flex-col md:space-x-0 md:space-y-10 xl:flex-row xl:space-x-6 xl:space-y-0 mt-9"
        >
          <div class="w-full">
            <div
              class="bg-white dark:bg-gray-800 shadow-lg rounded-xl p-5 mb-2"
            >
              <div class="space-y-6">
                <!-- Title + Version -->
                <div class="flex flex-col sm:flex-row sm:items-end gap-4">
                  <div class="flex flex-col w-full">
                    <label
                      for="title-input"
                      class="text-sm font-medium text-gray-700 dark:text-gray-300 w-20"
                      >{{ t("config.maintenance.Title") }}</label
                    >
                    <input
                      id="title-input"
                      v-model="title"
                      class="form-input flex-1 bg-gray-100 dark:bg-gray-700 border-transparent dark:border-transparent focus:bg-white dark:focus:bg-gray-800 placeholder-gray-500"
                      type="text"
                      placeholder=""
                      :maxlength="100"
                    />
                  </div>
                </div>
                <div class="flex flex-col sm:flex-row sm:items-end gap-4">
                  <div class="flex space-x-5">
                    <label
                      class="inline-flex items-center text-sm font-medium cursor-pointer text-gray-400 peer-checked:text-violet-500"
                    >
                      <input
                        type="radio"
                        class="sr-only peer"
                        name="action"
                        value="0"
                        v-model="mtype"
                      />
                      <svg
                        class="shrink-0 mr-2 stroke-current peer-checked:text-violet-500 transition-colors"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                      <span class="peer-checked:text-violet-500">{{
                        t("config.maintenance.Installation")
                      }}</span>
                    </label>

                    <label
                      class="inline-flex items-center text-sm font-medium cursor-pointer text-gray-400 peer-checked:text-violet-500"
                    >
                      <input
                        type="radio"
                        class="sr-only peer"
                        name="action"
                        value="1"
                        v-model="mtype"
                      />
                      <svg
                        class="shrink-0 mr-2 stroke-current peer-checked:text-violet-500 transition-colors"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <polyline points="23 4 23 10 17 10" />
                        <polyline points="1 20 1 14 7 14" />
                        <path d="M3.51 9a9 9 0 0 1 14.13-3.36L23 10" />
                        <path d="M20.49 15a9 9 0 0 1-14.13 3.36L1 14" />
                      </svg>
                      <span class="peer-checked:text-violet-500">{{
                        t("config.maintenance.Update")
                      }}</span>
                    </label>

                    <label
                      class="inline-flex items-center text-sm font-medium cursor-pointer text-gray-400 peer-checked:text-violet-500"
                    >
                      <input
                        type="radio"
                        class="sr-only peer"
                        name="action"
                        value="2"
                        v-model="mtype"
                      />
                      <svg
                        class="shrink-0 mr-2 stroke-current peer-checked:text-violet-500 transition-colors"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <polyline points="16 3 21 3 21 8" />
                        <line x1="4" y1="20" x2="21" y2="3" />
                        <polyline points="8 21 3 21 3 16" />
                      </svg>
                      <span class="peer-checked:text-violet-500">{{
                        t("config.maintenance.Replacement")
                      }}</span>
                    </label>
                    <label
                      class="inline-flex items-center text-sm font-medium cursor-pointer text-gray-400 peer-checked:text-violet-500"
                    >
                      <input
                        type="radio"
                        class="sr-only peer"
                        name="action"
                        value="3"
                        v-model="mtype"
                      />
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        class="shrink-0 mr-2 stroke-current peer-checked:text-violet-500 transition-colors"
                        fill="none"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <path d="M4 8h4v4h-4z" />
                        <path d="M6 4l0 4" />
                        <path d="M6 12l0 8" />
                        <path d="M10 14h4v4h-4z" />
                        <path d="M12 4l0 10" />
                        <path d="M12 18l0 2" />
                        <path d="M16 5h4v4h-4z" />
                        <path d="M18 4l0 1" />
                        <path d="M18 9l0 11" />
                      </svg>
                      <span class="peer-checked:text-violet-500">{{
                        t("config.maintenance.Calibration")
                      }}</span>
                    </label>
                  </div>

                  <!-- Component Selection - 수정된 부분 -->
                  <div
                    v-if="mtype == 0 || mtype == 1"
                    class="flex flex-wrap gap-4"
                  >
                    <!-- FW -->
                    <label
                      class="inline-flex items-center text-sm font-medium cursor-pointer text-gray-600 dark:text-gray-300"
                    >
                      <input
                        type="checkbox"
                        class="form-checkbox text-violet-500 border-gray-300 dark:border-gray-600 focus:ring-violet-400"
                        v-model="selectedTarget.fw"
                      />
                      <span class="ml-2">FW</span>
                    </label>

                    <!-- A35 -->
                    <label
                      class="inline-flex items-center text-sm font-medium cursor-pointer text-gray-600 dark:text-gray-300"
                    >
                      <input
                        type="checkbox"
                        class="form-checkbox text-violet-500 border-gray-300 dark:border-gray-600 focus:ring-violet-400"
                        v-model="selectedTarget.a35"
                      />
                      <span class="ml-2">A35</span>
                    </label>

                    <!-- Web -->
                    <label
                      class="inline-flex items-center text-sm font-medium cursor-pointer text-gray-600 dark:text-gray-300"
                    >
                      <input
                        type="checkbox"
                        class="form-checkbox text-violet-500 border-gray-300 dark:border-gray-600 focus:ring-violet-400"
                        v-model="selectedTarget.web"
                      />
                      <span class="ml-2">Web</span>
                    </label>

                    <!-- Core -->
                    <label
                      class="inline-flex items-center text-sm font-medium cursor-pointer text-gray-600 dark:text-gray-300"
                    >
                      <input
                        type="checkbox"
                        class="form-checkbox text-violet-500 border-gray-300 dark:border-gray-600 focus:ring-violet-400"
                        v-model="selectedTarget.core"
                      />
                      <span class="ml-2">Core</span>
                    </label>

                    <!-- SmartSystem -->
                    <label
                      class="inline-flex items-center text-sm font-medium cursor-pointer text-gray-600 dark:text-gray-300"
                    >
                      <input
                        type="checkbox"
                        class="form-checkbox text-violet-500 border-gray-300 dark:border-gray-600 focus:ring-violet-400"
                        v-model="selectedTarget.smartsystem"
                      />
                      <span class="ml-2">SmartSystem</span>
                    </label>
                  </div>
                </div>

                <!-- Version Inputs - 3컬럼으로 수정 -->
                <div v-if="!isNoneSelected" class="space-y-3">
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <!-- FW Version -->
                    <div
                      v-if="selectedTarget.fw"
                      class="flex items-center space-x-2"
                    >
                      <label
                        class="text-sm font-medium text-gray-700 dark:text-gray-300 min-w-[60px]"
                        >FW</label
                      >
                      <input
                        class="form-input flex-1 bg-gray-100 dark:bg-gray-700 border-transparent dark:border-transparent focus:bg-white dark:focus:bg-gray-800 placeholder-gray-500 text-sm"
                        type="text"
                        placeholder="1.0.0"
                        v-model="versions.fw"
                        :maxlength="20"
                      />
                    </div>

                    <!-- A35 Version -->
                    <div
                      v-if="selectedTarget.a35"
                      class="flex items-center space-x-2"
                    >
                      <label
                        class="text-sm font-medium text-gray-700 dark:text-gray-300 min-w-[60px]"
                        >A35</label
                      >
                      <input
                        class="form-input flex-1 bg-gray-100 dark:bg-gray-700 border-transparent dark:border-transparent focus:bg-white dark:focus:bg-gray-800 placeholder-gray-500 text-sm"
                        type="text"
                        placeholder="1.0.0"
                        v-model="versions.a35"
                        :maxlength="20"
                      />
                    </div>

                    <!-- Web Version -->
                    <div
                      v-if="selectedTarget.web"
                      class="flex items-center space-x-2"
                    >
                      <label
                        class="text-sm font-medium text-gray-700 dark:text-gray-300 min-w-[60px]"
                        >Web</label
                      >
                      <input
                        class="form-input flex-1 bg-gray-100 dark:bg-gray-700 border-transparent dark:border-transparent focus:bg-white dark:focus:bg-gray-800 placeholder-gray-500 text-sm"
                        type="text"
                        placeholder="1.0.0"
                        v-model="versions.web"
                        :maxlength="20"
                      />
                    </div>

                    <!-- Core Version -->
                    <div
                      v-if="selectedTarget.core"
                      class="flex items-center space-x-2"
                    >
                      <label
                        class="text-sm font-medium text-gray-700 dark:text-gray-300 min-w-[60px]"
                        >Core</label
                      >
                      <input
                        class="form-input flex-1 bg-gray-100 dark:bg-gray-700 border-transparent dark:border-transparent focus:bg-white dark:focus:bg-gray-800 placeholder-gray-500 text-sm"
                        type="text"
                        placeholder="1.0.0"
                        v-model="versions.core"
                        :maxlength="20"
                      />
                    </div>

                    <!-- SmartSystem Version -->
                    <div
                      v-if="selectedTarget.smartsystem"
                      class="flex items-center space-x-2"
                    >
                      <label
                        class="text-sm font-medium text-gray-700 dark:text-gray-300 min-w-[60px]"
                        >SmartSys</label
                      >
                      <input
                        class="form-input flex-1 bg-gray-100 dark:bg-gray-700 border-transparent dark:border-transparent focus:bg-white dark:focus:bg-gray-800 placeholder-gray-500 text-sm"
                        type="text"
                        placeholder="1.0.0"
                        v-model="versions.smartsystem"
                        :maxlength="20"
                      />
                    </div>
                  </div>
                </div>

                <!-- Context + Send -->
                <div class="flex flex-col sm:flex-row sm:items-end gap-4">
                  <div class="flex flex-col w-full">
                    <label
                      for="context-input"
                      class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                      >{{ t("config.maintenance.Context") }}</label
                    >
                    <textarea
                      id="context-input"
                      v-model="context"
                      rows="3"
                      class="form-textarea w-full bg-gray-100 dark:bg-gray-700 border-transparent dark:border-transparent focus:bg-white dark:focus:bg-gray-800 placeholder-gray-500"
                      placeholder=""
                      :maxlength="200"
                    ></textarea>
                  </div>
                </div>
                <div class="flex gap-2">
                  <button
                    @click="save"
                    class="btn-sm w-32 bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white whitespace-nowrap"
                  >
                    {{ t("config.maintenance.Save") }}
                  </button>
                  <button
                    v-if="id !== 0"
                    @click="remove"
                    class="btn-sm w-32 bg-blue-900 text-blue-100 hover:bg-blue-800 dark:bg-blue-100 dark:text-blue-800 dark:hover:bg-white whitespace-nowrap"
                  >
                    {{ t("config.maintenance.Delete") }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Job list -->
            <div class="space-y-2">
              <JobListItem
                v-for="item in paginatedContents"
                :key="item.id + '-' + contents.length"
                :item="item"
                @editTitle="handleEdit"
              />
            </div>

<!-- Pagination -->
<div v-if="totalPages > 1" class="mt-6">
  <div class="flex justify-center">
    <nav class="flex items-center space-x-1" role="navigation" aria-label="Pagination">
      <!-- Previous Button -->
      <button
        @click="goToPage(currentPage - 1)"
        :disabled="currentPage === 1"
        class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="currentPage === 1 
          ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed' 
          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <!-- Page Numbers -->
      <button
        v-for="page in visiblePages"
        :key="page"
        @click="goToPage(page)"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="page === currentPage 
          ? 'bg-violet-500 text-white' 
          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'"
      >
        {{ page }}
      </button>

      <!-- Next Button -->
      <button
        @click="goToPage(currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="currentPage === totalPages 
          ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed' 
          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </nav>
  </div>
  
  <!-- Page Info -->
  <div class="text-center mt-2 text-sm text-gray-500 dark:text-gray-400">
    {{ currentPage }} / {{ totalPages }}  ( {{ contents.length }})
  </div>
</div>
          </div>
        </div>
      </section>
      <section></section>
    </div>
  </div>
</template>

<script>
import { useI18n } from "vue-i18n";
import JobListItem from "./maintenanceItem.vue";
import { ref, computed, onMounted, reactive, watchEffect } from "vue";
import axios from "axios";

export default {
  name: "MaintenancePanel",
  components: {
    JobListItem,
  },
  setup() {
    const { t } = useI18n();
    const sidebarOpen = ref(false);
    const id = ref(0);
    const message = ref("");
    const title = ref("");
    const context = ref("");
    const contents = ref([]);
    const selContext = ref(0);

    // 버전 정보 - 5개로 확장
    const versions = ref({
      fw: "",
      a35: "",
      web: "",
      core: "",
      smartsystem: "",
    });

    const mtype = ref(-1);

    // 선택 타겟 - 5개로 확장
    const selectedTarget = reactive({
      fw: false,
      a35: false,
      web: false,
      core: false,
      smartsystem: false,
    });

    // Pagination state
    const currentPage = ref(1);
    const itemsPerPage = ref(5);

    // utype 계산 - 5개 컴포넌트
    const utype = computed(() => {
      const types = [];
      if (selectedTarget.fw) types.push("fw");
      if (selectedTarget.a35) types.push("a35");
      if (selectedTarget.web) types.push("web");
      if (selectedTarget.core) types.push("core");
      if (selectedTarget.smartsystem) types.push("smartsystem");
      return types.join(",");
    });

    const isNoneSelected = computed(() => {
      return (
        !selectedTarget.fw &&
        !selectedTarget.a35 &&
        !selectedTarget.web &&
        !selectedTarget.core &&
        !selectedTarget.smartsystem
      );
    });

    // Pagination computed properties (동일)
    const totalPages = computed(() => {
      return Math.ceil(contents.value.length / itemsPerPage.value);
    });

    const startIndex = computed(() => {
      return (currentPage.value - 1) * itemsPerPage.value;
    });

    const endIndex = computed(() => {
      return startIndex.value + itemsPerPage.value;
    });

    const paginatedContents = computed(() => {
      const sortedContents = [...contents.value].sort((a, b) => b.id - a.id);
      return sortedContents.slice(startIndex.value, endIndex.value);
    });

    const visiblePages = computed(() => {
      const pages = [];
      const maxVisiblePages = 5;
      let start = Math.max(
        1,
        currentPage.value - Math.floor(maxVisiblePages / 2)
      );
      let end = Math.min(totalPages.value, start + maxVisiblePages - 1);

      if (end - start + 1 < maxVisiblePages) {
        start = Math.max(1, end - maxVisiblePages + 1);
      }

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      return pages;
    });

    const goToPage = (page) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page;
      }
    };

    watchEffect(() => {
      if (contents.value.length > 0 && currentPage.value > totalPages.value) {
        currentPage.value = 1;
      }
    });

    onMounted(() => {
      getContents();
    });

    // utype 적용 함수 - 5개 컴포넌트
    function applyUtype(utypeStr) {
      const types = utypeStr.split(",").map((t) => t.trim().toLowerCase());
      selectedTarget.fw = types.includes("fw");
      selectedTarget.a35 = types.includes("a35");
      selectedTarget.web = types.includes("web");
      selectedTarget.core = types.includes("core");
      selectedTarget.smartsystem = types.includes("smartsystem");
    }

    const handleEdit = (item) => {
      selContext.value = 1;
      id.value = item.id;
      title.value = item.title;
      mtype.value = item.mtype;
      applyUtype(item.utype);
      context.value = item.context;

      // 버전 정보 매핑
      versions.value.fw = item.f_version || "";
      versions.value.a35 = item.a_version || "";
      versions.value.web = item.w_version || "";
      versions.value.core = item.c_version || "";
      versions.value.smartsystem = item.smart_version || "";
    };

    const save = async () => {
      const data = {
        title: title.value,
        mtype: mtype.value,
        utype: utype.value,
        context: context.value,
        f_version: versions.value.fw,
        a_version: versions.value.a35,
        w_version: versions.value.web,
        c_version: versions.value.core,
        smart_version: versions.value.smartsystem,
      };
      if(title.value.trim() === "") {
        alert("❌ Title is required!");
        return;
      }
      console.log(data);
      try {
        const response = await axios.post(
          `/config/savePost/${selContext.value}/${id.value}`,
          data,
          {
            headers: { "Content-Type": "application/json" },
            withCredentials: true,
          }
        );

        if (response.data && response.data.passOK === "1") {
          alert("✅ Data saved successfully!");
          // 폼 초기화
          selContext.value = 0;
          id.value = 0;
          title.value = "";
          mtype.value = -1;
          context.value = "";
          versions.value = {
            fw: "",
            a35: "",
            web: "",
            core: "",
            smartsystem: "",
          };
          applyUtype("");
          await getContents();
        } else {
          alert("❌ Data save failed!");
        }
      } catch (err) {
        console.log("Error occurred while saving:", err);
      }
    };

    const getContents = async () => {
      try {
        const response = await axios.get("/config/getPost");
        if (response.data.result === 1) {
          const newData = response.data.data || [];
          contents.value.splice(0, contents.value.length, ...newData);
          currentPage.value = 1;
          await getLastContents();
        } else {
          contents.value.splice(0);
        }
      } catch (err) {
        contents.value.splice(0);
      }
    };

    const getLastContents = async () => {
      try {
        const response = await axios.get("/config/getLastPost");
        if (response.data.result === 1) {
          const newData = response.data.data || {};
          versions.value.fw = newData["f_version"];
          versions.value.a35 = newData["a_version"];
          versions.value.web = newData["w_version"];
          versions.value.core = newData["c_version"];
          versions.value.smartsystem = newData["smart_version"];
        } else {
          contents.value.splice(0);
        }
      } catch (err) {
        contents.value.splice(0);
      }
    };

    const remove = async () => {
      try {
        const response = await axios.get(`/config/deletePost/${id.value}`);
        if (response.data.result === 1) {
          alert("✅ Data deleted successfully!");
          id.value = 0;
          selContext.value = 0;
          title.value = "";
          mtype.value = -1;
          context.value = "";
          versions.value = {
            fw: "",
            a35: "",
            web: "",
            core: "",
            smartsystem: "",
          };
          applyUtype("");
          await getContents();
          if (contents.value.length == 0) {
            contents.value = [];
          }
        }
      } catch (err) {
        console.log("읽기 오류 발생:", err);
      }
    };

    return {
      sidebarOpen,
      message,
      versions,
      mtype,
      selectedTarget,
      isNoneSelected,
      title,
      context,
      utype,
      save,
      contents,
      handleEdit,
      id,
      remove,
      // Pagination
      currentPage,
      itemsPerPage,
      totalPages,
      startIndex,
      endIndex,
      paginatedContents,
      visiblePages,
      goToPage,
      t,
    };
  },
};
</script>
