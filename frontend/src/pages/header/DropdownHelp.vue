<template>
  <div class="relative inline-flex">
    <button
      ref="trigger"
      class="w-8 h-8 flex items-center justify-center hover:bg-gray-100 lg:hover:bg-gray-200 dark:hover:bg-gray-700/50 dark:lg:hover:bg-gray-800 rounded-full"
      :class="{ 'bg-gray-200 dark:bg-gray-800': dropdownOpen }"
      aria-haspopup="true"
      @click.prevent="dropdownOpen = !dropdownOpen"
      :aria-expanded="dropdownOpen"
    >
      <span class="sr-only">Info</span>
      <svg 
        class="fill-current rotate-90 text-gray-500/80 dark:text-gray-400/80"
        xmlns="http://www.w3.org/2000/svg" 
        width="16" 
        height="16" 
        viewBox="0 0 16 16"
      >
        <path d="M7.586 9H1a1 1 0 1 1 0-2h6.586L6.293 5.707a1 1 0 0 1 1.414-1.414l3 3a1 1 0 0 1 0 1.414l-3 3a1 1 0 1 1-1.414-1.414L7.586 9ZM3.075 4.572a1 1 0 1 1-1.64-1.144 8 8 0 1 1 0 9.144 1 1 0 0 1 1.64-1.144 6 6 0 1 0 0-6.856Z" />
      </svg>
    </button>
    <transition
      enter-active-class="transition ease-out duration-200 transform"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-out duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-show="dropdownOpen" class="origin-top-right z-10 absolute top-full min-w-44 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 py-1.5 rounded-lg shadow-lg overflow-hidden mt-1"  :class="align === 'right' ? 'right-0' : 'left-0'">
        <div class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase pt-1.5 pb-2 px-3">{{t('header.link.msg') }}</div>
        <ul
          ref="dropdown"
          @focusin="dropdownOpen = true"
          @focusout="dropdownOpen = false"
        >
          <li>
            <router-link class="font-medium text-sm text-violet-500 hover:text-violet-600 dark:hover:text-violet-400 flex items-center py-1 px-3" to="#0" @click="dropdownOpen = false">
              <svg class="w-3 h-3 fill-current text-violet-500 shrink-0 mr-2" viewBox="0 0 12 12">
                <rect y="3" width="12" height="9" rx="1" />
                <path d="M2 0h8v2H2z" />
              </svg>
              <span> {{t('header.link.catalog') }}</span>
            </router-link>
          </li>
          <li>
            <router-link class="font-medium text-sm text-violet-500 hover:text-violet-600 dark:hover:text-violet-400 flex items-center py-1 px-3" to="#0" @click="dropdownOpen = false">
              <svg class="w-3 h-3 fill-current text-violet-500 shrink-0 mr-2" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
                  <path d="M5 4a1 1 0 0 0 0 2h6a1 1 0 1 0 0-2H5Z" />
                  <path d="M4 0a4 4 0 0 0-4 4v8a4 4 0 0 0 4 4h8a4 4 0 0 0 4-4V4a4 4 0 0 0-4-4H4ZM2 4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4Z" />
              </svg> 
              <span>{{t('header.link.manual') }}</span>
            </router-link>
          </li>
          <!-- 용어설명집 추가 -->
          <li>
            <a 
              class="font-medium text-sm text-violet-500 hover:text-violet-600 dark:hover:text-violet-400 flex items-center py-1 px-3 cursor-pointer" 
              @click="openGlossary"
            >
              <svg class="w-3 h-3 fill-current text-violet-500 shrink-0 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
                <path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2zm2 0v12h8V2H4zm2 2h4v1H6V4zm0 3h4v1H6V7zm0 3h4v1H6v-1z"/>
              </svg>
              <span>{{ t('header.link.glossary') }}</span>
            </a>
          </li>
        </ul>
      </div> 
    </transition>

    <!-- 용어설명집 모달 -->
    <GlossaryModal :isOpen="showGlossary" @close="showGlossary = false" />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import GlossaryModal from './GlossaryModal.vue'

export default {
  name: 'DropdownHelp',
  props: ['align'],
  components: {
    GlossaryModal
  },
  setup() {
    const { t } = useI18n();
    const dropdownOpen = ref(false)
    const trigger = ref(null)
    const dropdown = ref(null)
    const showGlossary = ref(false)

    const openGlossary = () => {
      showGlossary.value = true
      dropdownOpen.value = false
    }

    // close on click outside
    const clickHandler = ({ target }) => {
      if (!dropdownOpen.value || dropdown.value.contains(target) || trigger.value.contains(target)) return
      dropdownOpen.value = false
    }

    // close if the esc key is pressed
    const keyHandler = ({ keyCode }) => {
      if (!dropdownOpen.value || keyCode !== 27) return
      dropdownOpen.value = false
    }

    onMounted(() => {
      document.addEventListener('click', clickHandler)
      document.addEventListener('keydown', keyHandler)
    })

    onUnmounted(() => {
      document.removeEventListener('click', clickHandler)
      document.removeEventListener('keydown', keyHandler)
    })

    return {
      dropdownOpen,
      trigger,
      dropdown,
      showGlossary,
      openGlossary,
      t,
    }
  }
}
</script>