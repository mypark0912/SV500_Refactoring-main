<template>
  <div class="grid grid-cols-12 gap-6">
    <!-- device4: 인버터 계측장치 레이아웃 -->
    <!-- TODO: 시안 확정 후 카드 구성 -->
    <div class="col-span-12 text-center text-sm text-slate-400 py-8">
      인버터 계측장치 대시보드 레이아웃 (준비 중)
    </div>
  </div>
</template>

<script>
export default {
  name: 'InverterLayout',
  props: {
    channelState: {
      type: Object,
      required: true
    },
    channel: {
      type: String,
      required: true
    }
  },
}
</script>
