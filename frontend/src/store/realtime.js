// store/realtime.js
import { defineStore } from 'pinia'
import axios from 'axios'

export const useRealtimeStore = defineStore('realtime', {
  state: () => ({
    meterDictMain: {},
    meterDictSub: {},
    isMainDataLoaded: false,
    isSubDataLoaded: false,
    isLoading: false,
    updateInterval: null,
    lastUpdateTime: null,
    error: null
  }),

  getters: {
    // 데이터 준비 완료 상태
    isDataReady: (state) => (channelState, opMode) => {
      if (!opMode || opMode === '') {
        return false
      }

      if (opMode === 'device2') {
        return state.isMainDataLoaded
      } else {
        const needsSubData = channelState?.SubEnable
        return state.isMainDataLoaded && (needsSubData ? state.isSubDataLoaded : true)
      }
    },

    // Main 데이터 getter
    getMainData: (state) => state.meterDictMain || {},

    // Sub 데이터 getter
    getSubData: (state) => state.meterDictSub || {},

    // 특정 채널 데이터 가져오기
    getChannelData: (state) => (channel) => {
      //return channel === 'Main' ? state.meterDictMain : state.meterDictSub
      const data = channel === 'Main' ? state.meterDictMain : state.meterDictSub
       return data || {}  // null/undefined 방지
    }
  },

  actions: {
    // 데이터 페칭 함수
    async fetchChannelData(channel, opMode, channelState) {
      if (opMode === '') {
        return false
      }

      try {
        const response = await axios.get(`/api/getMeterRedisNew/${channel}/${opMode}`)
        
        if (response.data.success) {
          const newData = response.data.data
          
          if (channel === 'Main') {
            // 변경된 데이터만 업데이트 (재렌더링 최소화)
            const hasChanges = JSON.stringify(this.meterDictMain) !== JSON.stringify(newData)
            if (hasChanges) {
              this.meterDictMain = { ...this.meterDictMain, ...newData }
              if (!channelState?.SubEnable && this.meterDictMain.P4) {
                this.meterDictMain.P4 = (this.meterDictMain.P4 / 1000).toFixed(2)
              }
            }
            this.isMainDataLoaded = true
          } else {
            // Sub 채널 데이터
            const hasChanges = JSON.stringify(this.meterDictSub) !== JSON.stringify(newData)
            if (hasChanges) {
              this.meterDictSub = { ...this.meterDictSub, ...newData }
              if (this.meterDictSub.P4) {
                this.meterDictSub.P4 = (this.meterDictSub.P4 / 1000).toFixed(2)
              }
            }
            this.isSubDataLoaded = true
          }
          
          this.lastUpdateTime = new Date()
          return true
        } else {
          console.log(`❌ ${channel} 채널: 서버에서 success=false 응답`)
          return false
        }
      } catch (error) {
        console.error(`❌ ${channel} 채널 데이터 가져오기 실패:`, error)
        this.error = error
        return false
      }
    },

    // 초기 데이터 로딩
    async loadInitialData(opMode, channelState) {
      if (!opMode || opMode === '') {
        console.log('❌ 초기 조건 불만족으로 데이터 로딩 중단')
        return
      }

      console.log('🔄 초기 데이터 로딩 시작')
      this.isLoading = true
      this.error = null
      
      try {
        if (opMode === 'device2') {
          await this.fetchChannelData('Main', opMode, channelState)
        } else {
          await this.fetchChannelData('Main', opMode, channelState)
          if (channelState?.SubEnable) {
            await this.fetchChannelData('Sub', opMode, channelState)
          } else {
            this.isSubDataLoaded = true // Sub 데이터가 필요없으면 완료로 표시
          }
        }
      } catch (error) {
        console.error('초기 데이터 로딩 실패:', error)
        this.error = error
      } finally {
        this.isLoading = false
      }
    },

    // 주기적 업데이트 시작
    startPolling(opMode, channelState, interval = 10000) {
      // 기존 인터벌 정리
      this.stopPolling()

      // 초기 데이터 로드
      this.loadInitialData(opMode, channelState)

      // 주기적 업데이트 설정
      this.updateInterval = setInterval(async () => {
        if (!opMode) return

        await this.fetchChannelData('Main', opMode, channelState)
        if (channelState?.SubEnable) {
          await this.fetchChannelData('Sub', opMode, channelState)
        }
      }, interval)
    },

    // 주기적 업데이트 중지
    stopPolling() {
      if (this.updateInterval) {
        clearInterval(this.updateInterval)
        this.updateInterval = null
      }
    },

    // 데이터 초기화
    resetData() {
      this.meterDictMain = {}
      this.meterDictSub = {}
      this.isMainDataLoaded = false
      this.isSubDataLoaded = false
      this.error = null
    },

    // 채널 상태 변경 시 호출
    async onChannelStateChange(opMode, channelState) {
      // 데이터 상태 초기화
      this.isMainDataLoaded = false
      this.isSubDataLoaded = false
      
      // 데이터 다시 로딩 및 폴링 재시작
      this.startPolling(opMode, channelState)
    }
  }
})