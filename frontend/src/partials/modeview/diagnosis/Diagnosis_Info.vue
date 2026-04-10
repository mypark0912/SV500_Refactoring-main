<template>
  <div class="card-wrap col-span-full xl:col-span-12 bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 shadow-lg rounded-xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
    <div class="card-header flex justify-between items-center px-4 py-2.5">
      <h2 class="card-title meter-accent-blue text-base font-bold text-gray-800 dark:text-white flex items-center gap-2">
        {{ t('diagnosis.info.name') }}
      </h2>
    </div>
    <div class="card-body px-4 py-3">
      <div class="flex items-center gap-5">
        <!-- 장비 이미지 -->
        <img :src="equipImageSrc" alt="장비 이미지"
          class="w-20 h-20 object-cover rounded-lg shadow-md border border-gray-300 dark:border-gray-600" />

        <!-- 장비 이름 & 타입 (수직 정렬) -->
        <div class="flex flex-col space-y-2">
          <!-- 이름 -->
          <div class="flex flex-col">
            <div class="flex flex-row space-x-6">
              <div class="flex flex-col">
                <span class="text-xs font-bold text-gray-500 dark:text-white uppercase">{{ t('diagnosis.info.name') }}</span>
                <span class="text-lg font-bold text-gray-800 dark:text-gray-100">{{ thisAsset.name }}</span>
              </div>
              <div class="flex flex-col">
                <span class="text-xs font-bold text-gray-500 dark:text-white uppercase">{{ t('diagnosis.info.type') }}</span>
                <span class="text-lg font-bold text-gray-800 dark:text-gray-100">{{ thisAsset.type }}</span>
              </div>
              <div v-if="!thisAsset.type?.includes('Transformer')" class="flex flex-col">
                <span class="text-xs font-bold text-gray-500 dark:text-white uppercase">{{ t('diagnosis.info.drivetype') }}</span>
                <span class="text-lg font-bold text-gray-800 dark:text-gray-100">{{ driveType == 'DOL'? t('diagnosis.info.dr1') : t('diagnosis.info.dr2') }}</span>
              </div>
            </div>
          </div>
          <!-- 타입 -->
          <div class="flex flex-col">
            <div class="flex items-center gap-5 py-3">
              <div v-for="item in AssetInfo" :key="item.Title" class="flex flex-col space-y-3">
                <div class="flex flex-col">
                  <span class="text-xs font-bold text-gray-500 dark:text-white uppercase">{{ t(`diagnosis.info.${item.Title}`) }}</span>
                  <span class="text-lg font-bold text-gray-800 dark:text-gray-100">{{ item.Value }} {{ item.Unit }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<script>
import { ref, computed, inject } from 'vue'
import motorImg from '@/images/motor_m.png'
import fanImg from '@/images/fan_m.png'
import pumpImg from '@/images/pump_m.png'
import compImg from '@/images/comp_m.png'
import powerImg from '@/images/power_m.png'
import defaultImg from '@/images/cleaned_logo.png'
import transImg from '@/images/trans.png'
import { useI18n } from 'vue-i18n'

export default {
  name: 'Diagnosis_Info',
  props: {
    asset:{
      type: Object,
      default: () => {}
    },
    data:{
      type: Object,
      default: () => []
    },
    channel:{
      type:String,
      default: ''
    },
  },
  setup(props){
    const { t } = useI18n();
    const channel = ref(props.channel);
    const asset = ref(props.asset);
    const driveType = inject('driveType');
    //console.log(channel.value,'-', driveType.value);
    // ✅ props 직접 사용 또는 computed로 감싸야 반응함
    const thisAsset = computed(() => {
      const chName = props.channel === 'Main' ? props.asset.assetNickname_main : props.asset.assetNickname_sub;
      const chType = props.channel === 'Main' ? props.asset.assetType_main : props.asset.assetType_sub;
      return { name: chName, type: chType };
    });
    const AssetInfo = computed(() => props.data); // ✅ 반응형 props 연결
    const equipImageSrc = computed(() => {
      switch (thisAsset.value.type) {
        case 'Motor':
          return motorImg;
        case 'MotorFeed':
          return motorImg;
        case 'Pump':
          return pumpImg;//'/images/motor_pump.png';
        case 'Fan':
          return fanImg;
        case 'Compressor':
          return compImg;//'/images/fan_m.png';
        case 'PSupply':
          return powerImg;//'/images/power.png';
        case 'PowerSupply':
          return powerImg;//'/images/power.png';
        case 'PrimaryTransformer':
          return transImg;//'/images/trans.png';
        case 'Transformer':
          return transImg;//'/images/trans.png';
        default:
          return defaultImg;//'@/images/cleaned_logo.png'
      }
    });

    return {
      thisAsset,
      AssetInfo,
      equipImageSrc,
      channel,
      t,
      driveType,
    }
  }
}
</script>

<style scoped>
.meter-accent-blue::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 1.1em;
  border-radius: 2px;
  @apply bg-blue-500;
}
</style>
