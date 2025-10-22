<template>
  <!-- Modal Backdrop -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        @click.self="closeModal"
      >
        <!-- Modal Container -->
        <div
          class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden"
          @click.stop
        >
          <!-- Modal Header -->
          <div class="px-6 py-5 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-800">
            <div class="flex items-center justify-between">
              <h3 class="text-xl font-bold text-gray-900 dark:text-gray-100">
                리포트 전송 확인
              </h3>
              <button
                @click="closeModal"
                class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-all duration-200 hover:rotate-90 rounded-lg p-1 hover:bg-white/50 dark:hover:bg-gray-700/50"
                aria-label="닫기"
              >
                <svg
                  class="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>

          <!-- Modal Body -->
          <div class="px-6 py-6">
            <!-- 리포트 정보 입력 폼 -->
            <div class="space-y-5">
              <div class="grid grid-cols-2 gap-4">
                <!-- 주파수 -->
                <div class="col-span-1">
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    주파수
                  </label>
                  <input
                    v-model="formData.frequency"
                    type="text"
                    placeholder="주파수 입력"
                    class="w-full px-4 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                  />
                </div>
               
                <div class="col-span-1"></div>

                <!-- 시험자 -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    시험자
                  </label>
                  <input
                    v-model="formData.tester"
                    type="text"
                    placeholder="시험자 이름"
                    class="w-full px-4 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                  />
                </div>

                <!-- 승인자 -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    승인자
                  </label>
                  <input
                    v-model="formData.approver"
                    type="text"
                    placeholder="승인자 이름"
                    class="w-full px-4 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                  />
                </div>

                <!-- SN -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    SN
                  </label>
                  <input
                    v-model="formData.sn"
                    type="text"
                    placeholder="시리얼 넘버"
                    class="w-full px-4 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                  />
                </div>

                <!-- 제조일 -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    제조일
                  </label>
                  <input
                    v-model="formData.manufactureDate"
                    type="text"
                    placeholder="YYYY-MM-DD"
                    class="w-full px-4 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                  />
                </div>

                <!-- 표준기기명 -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    표준기기명
                  </label>
                  <input
                    v-model="formData.StandardEquipmentName"
                    type="text"
                    placeholder="표준기기명 입력"
                    class="w-full px-4 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                  />
                </div>

                <!-- 불확도 -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    불확도
                  </label>
                  <input
                    v-model="formData.Uncertainty"
                    type="text"
                    placeholder="불확도 값"
                    class="w-full px-4 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                  />
                </div>
              </div>

              <!-- 언어 선택 -->
              <div class="pt-3 border-t border-gray-200 dark:border-gray-700">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  언어 선택
                </label>
                <div class="flex items-center gap-6">
                  <label class="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="radio"
                      v-model="selectedLanguage"
                      value="kr"
                      class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600 cursor-pointer"
                    />
                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      한국어
                    </span>
                  </label>
                  <label class="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="radio"
                      v-model="selectedLanguage"
                      value="en"
                      class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600 cursor-pointer"
                    />
                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      English
                    </span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="px-6 py-4 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
            <button
              @click="closeModal"
              class="px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-500 hover:shadow-md transition-all duration-200"
            >
              취소
            </button>
            <button
              @click="handleSendReport"
              :disabled="isSending"
              class="px-6 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transition-all duration-200"
            >
              <span v-if="!isSending">전송하기</span>
              <span v-else class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                전송 중...
              </span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, watch } from 'vue';
import axios from 'axios';

export default {
  name: 'SendReportModal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    reportData: {
      type: Object,
      default: () => ({
        tester: '',
        approver: '',
        sn: '',
        manufactureDate: '',
        StandardEquipmentName: '',
        Uncertainty: '',
        frequency: ''
      })
    }
  },
  emits: ['close', 'send'],
  setup(props, { emit }) {
    const selectedLanguage = ref('kr');
    const isSending = ref(false);
    
    // 입력 폼 데이터
    const formData = ref({
      tester: '',
      approver: '',
      sn: '',
      manufactureDate: '',
      StandardEquipmentName: '',
      Uncertainty: '',
      frequency: ''
    });

    // props가 변경될 때 formData 업데이트
    watch(() => props.reportData, (newData) => {
      formData.value = { ...newData };
    }, { immediate: true, deep: true });

    const closeModal = () => {
      if (!isSending.value) {
        emit('close');
      }
    };

    const handleSendReport = async () => {
      isSending.value = true;
      
      try {
        // API 호출
        const response = await axios.post('/api/send-report', {
          ...formData.value,
          language: selectedLanguage.value
        });

        if (response.data.success) {
          alert('리포트가 성공적으로 전송되었습니다.');
          emit('send', {
            ...formData.value,
            language: selectedLanguage.value
          });
          closeModal();
        } else {
          alert('리포트 전송에 실패했습니다: ' + response.data.message);
        }
      } catch (error) {
        console.error('Failed to send report:', error);
        alert('리포트 전송 중 오류가 발생했습니다.');
      } finally {
        isSending.value = false;
      }
    };

    return {
      selectedLanguage,
      isSending,
      formData,
      closeModal,
      handleSendReport
    };
  }
};
</script>

<style scoped>
/* Modal Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active > div > div,
.modal-leave-active > div > div {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-enter-from > div > div,
.modal-leave-to > div > div {
  transform: scale(0.9) translateY(-20px);
}
</style>