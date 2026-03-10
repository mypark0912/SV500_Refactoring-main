<template>
  <div class="grow dark:text-white">
    <!-- Panel body -->
    <div class="p-6 space-y-6">
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

            <!-- FTP Toast Notification -->
            <div
              v-if="showFTPToast"
              class="ml-4 flex items-center px-2 py-1 bg-blue-50 border border-blue-200 rounded-md shadow-sm transition-all duration-300 ease-in-out whitespace-nowrap"
            >
              <div class="flex items-center">
                <div
                  class="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center mr-1"
                >
                  <svg
                    class="w-2.5 h-2.5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <span class="text-xs font-medium text-blue-800">
                  {{ t("config.plansPanel.info") }}
                </span>
              </div>
            </div>

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

        <div class="grid grid-cols-12 gap-6">

          <!-- ① Device Information -->
          <div
            class="relative col-span-full xl:col-span-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg"
          >
            <div class="absolute top-0 left-0 right-0 h-0.5 bg-green-500" aria-hidden="true"></div>
            <div class="px-5 pt-5 pb-6 border-b border-gray-200 dark:border-gray-700/60">
              <header class="flex items-center mb-2">
                <div class="w-6 h-6 rounded-full shrink-0 bg-green-500 mr-3">
                  <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24">
                    <path d="M12 17a.833.833 0 01-.833-.833 3.333 3.333 0 00-3.334-3.334.833.833 0 110-1.666 3.333 3.333 0 003.334-3.334.833.833 0 111.666 0 3.333 3.333 0 003.334 3.334.833.833 0 110 1.666 3.333 3.333 0 00-3.334 3.334c0 .46-.373.833-.833.833z" />
                  </svg>
                </div>
                <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">
                  {{ t("config.plansPanel.devInformation.title") }}
                </h3>
              </header>
            </div>
            <div class="px-4 py-4 space-y-3">
              <div class="text-xs text-gray-800 dark:text-gray-100 font-semibold uppercase mb-1 mt-2">Basic</div>
              <div>
                <label class="block text-sm font-medium mb-2" for="device-model">
                  {{ t("config.plansPanel.devInformation.name") }}
                </label>
                <input
                  v-model="inputDict.deviceInfo.name"
                  class="form-input w-full"
                  type="text"
                  placeholder="Enter name"
                  maxlength="20"
                />
              </div>
              <div>
                <label class="block text-sm font-medium mb-2" for="location">
                  {{ t("config.plansPanel.devInformation.loc") }}
                </label>
                <input
                  v-model="inputDict.deviceInfo.location"
                  class="form-input w-full"
                  type="text"
                  placeholder="Enter location"
                  maxlength="20"
                />
              </div>
              <div class="flex space-x-3">
                <div>
                  <label class="block text-sm font-medium mb-2" for="serial-number">
                    {{ t("config.plansPanel.devInformation.sn") }}
                  </label>
                  <input readonly v-model="inputDict.deviceInfo.serial_number" class="form-input w-full" type="text" />
                </div>
                <div>
                  <label class="block text-sm font-medium mb-2" for="mac-address">
                    {{ t("config.plansPanel.devInformation.mac") }}
                  </label>
                  <input readonly v-model="inputDict.deviceInfo.mac_address" class="form-input w-full" type="text" />
                </div>
              </div>
              <div class="text-xs text-gray-800 dark:text-gray-100 font-semibold uppercase mb-1 mt-2">Measurement</div>
              <div class="flex space-x-3">
                <div class="flex-1">
                  <label class="block text-sm font-medium mb-1.5">PF Sign</label>
                  <select
                    v-model.number="inputDict.pf_sign"
                    class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option :value="0">IEC</option>
                    <option :value="1">IEEE</option>
                  </select>
                </div>
                <div class="flex-1">
                  <label class="block text-sm font-medium mb-1.5">VA type</label>
                  <select
                    v-model.number="inputDict.va_type"
                    class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option :value="0">RMS</option>
                    <option :value="1">vector</option>
                  </select>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium mb-1.5">Unbalance</label>
                <select
                  v-model.number="inputDict.unbalance"
                  class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option :value="0">Nema</option>
                  <option :value="1">Sequence Components</option>
                </select>
              </div>
            </div>
          </div>

          <!-- ② 통신설정 + Modbus TCP 묶음 -->
          <div class="relative col-span-full xl:col-span-3 flex flex-col gap-6">

            <!-- 통신설정 카드 -->
            <div class="relative bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg">
              <div class="absolute top-0 left-0 right-0 h-0.5 bg-sky-500" aria-hidden="true"></div>
              <div class="px-5 pt-5 pb-6 border-b border-gray-200 dark:border-gray-700/60">
                <header class="flex items-center mb-2">
                  <div class="w-6 h-6 rounded-full shrink-0 bg-sky-500 mr-3">
                    <svg class="w-6 h-6 shrink-0 fill-current text-white" viewBox="0 0 24 24">
                      <path d="M12 20c.83 0 1.5.67 1.5 1.5S12.83 23 12 23s-1.5-.67-1.5-1.5S11.17 20 12 20Zm-5.5-4.5a1 1 0 0 0 1.41 0 5.99 5.99 0 0 1 8.18 0 1 1 0 1 0 1.41-1.41 7.99 7.99 0 0 0-11 0 1 1 0 0 0 0 1.41Zm-3.54-3.54a1 1 0 0 0 1.41 0 10.93 10.93 0 0 1 15.44 0 1 1 0 0 0 1.42-1.42 12.93 12.93 0 0 0-18.28 0 1 1 0 0 0 0 1.42Z" />
                    </svg>
                  </div>
                  <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">
                    {{ t("config.plansPanel.communication.title") }}
                  </h3>
                </header>
              </div>
              <div class="px-4 py-4 space-y-3">
                <!-- DHCP Toggle -->
                <div class="flex items-center justify-between">
                  <label class="block text-sm font-medium">DHCP</label>
                  <div
                    class="relative inline-flex items-center cursor-pointer"
                    @click="inputDict.tcpip.dhcp = inputDict.tcpip.dhcp === 1 ? 0 : 1"
                  >
                    <div
                      class="w-11 h-6 rounded-full transition-colors duration-200"
                      :class="inputDict.tcpip.dhcp === 1 ? 'bg-sky-500' : 'bg-gray-300 dark:bg-gray-600'"
                    ></div>
                    <div
                      class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
                      :class="inputDict.tcpip.dhcp === 1 ? 'translate-x-5' : 'translate-x-0'"
                    ></div>
                  </div>
                </div>
                <!-- DHCP 활성화 시 안내 메시지 -->
                <div
                  v-if="inputDict.tcpip.dhcp === 1"
                  class="flex items-center px-3 py-2 bg-sky-50 dark:bg-sky-900/20 border border-sky-200 dark:border-sky-700/50 rounded-md"
                >
                  <svg class="w-4 h-4 text-sky-500 mr-2 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span class="text-xs text-sky-700 dark:text-sky-300">
                    {{ t("config.plansPanel.dhcp") }}
                  </span>
                </div>
                <!-- Static IP 설정 -->
                <template v-if="inputDict.tcpip.dhcp !== 1">
                  <div class="flex gap-2">
                    <div class="flex-1 min-w-0">
                      <label class="block text-sm font-medium mb-2">
                        {{ t("config.plansPanel.communication.ip") }}
                      </label>
                      <input v-model="inputDict.tcpip.ip_address" class="form-input w-full" type="text" maxlength="20" />
                    </div>
                    <div class="flex-1 min-w-0">
                      <label class="block text-sm font-medium mb-2">
                        {{ t("config.plansPanel.communication.sm") }}
                      </label>
                      <input v-model="inputDict.tcpip.subnet_mask" class="form-input w-full" type="text" maxlength="20" />
                    </div>
                  </div>
                  <div class="flex gap-2">
                    <div class="flex-1 min-w-0">
                      <label class="block text-sm font-medium mb-2">
                        {{ t("config.plansPanel.communication.gw") }}
                      </label>
                      <input v-model="inputDict.tcpip.gateway" class="form-input w-full" type="text" maxlength="20" />
                    </div>
                    <div class="flex-1 min-w-0">
                      <label class="block text-sm font-medium mb-2">
                        {{ t("config.plansPanel.communication.dns") }}
                      </label>
                      <input v-model="inputDict.tcpip.dnsserver" class="form-input w-full" type="text" maxlength="20" />
                    </div>
                  </div>
                </template>
              </div>
            </div>

            <!-- Modbus TCP 카드 -->
            <div class="relative bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg flex flex-col flex-1">
              <div class="absolute top-0 left-0 right-0 h-0.5 bg-violet-500" aria-hidden="true"></div>
              <div class="px-5 pt-5 pb-6 border-b border-gray-200 dark:border-gray-700/60">
                <header class="flex items-center mb-2">
                  <div class="w-6 h-6 rounded-full shrink-0 bg-violet-500 mr-3">
                    <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24">
                      <path d="M4 12h16m-4-4 4 4-4 4M8 8l-4 4 4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </div>
                  <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">Modbus TCP</h3>
                </header>
              </div>
              <div class="px-4 py-4 space-y-3">
                <div class="flex items-center justify-between">
                  <label class="block text-sm font-medium">Log enable</label>
                  <div
                    class="relative inline-flex items-center cursor-pointer"
                    @click="inputDict.modbus.tcp_log = inputDict.modbus.tcp_log === 1 ? 0 : 1"
                  >
                    <div
                      class="w-11 h-6 rounded-full transition-colors duration-200"
                      :class="inputDict.modbus.tcp_log === 1 ? 'bg-sky-500' : 'bg-gray-300 dark:bg-gray-600'"
                    ></div>
                    <div
                      class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
                      :class="inputDict.modbus.tcp_log === 1 ? 'translate-x-5' : 'translate-x-0'"
                    ></div>
                  </div>
                </div>
                <div>
                  <label class="block text-sm font-medium mb-2">
                    {{ t("config.plansPanel.modbus.tcp") }}
                  </label>
                  <input
                    v-model.number="inputDict.modbus.tcp_port"
                    class="form-input w-full"
                    type="number"
                    maxlength="20"
                  />
                </div>
              </div>
            </div>

          </div>

          <!-- ③ Modbus Serial -->
          <div class="relative col-span-full xl:col-span-3 flex flex-col gap-6">
            <div class="relative bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg flex flex-col flex-1">
              <div class="absolute top-0 left-0 right-0 h-0.5 bg-violet-500" aria-hidden="true"></div>
              <div class="px-5 pt-5 pb-6 border-b border-gray-200 dark:border-gray-700/60">
                <header class="flex items-center mb-2">
                  <div class="w-6 h-6 rounded-full shrink-0 bg-violet-500 mr-3">
                    <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24">
                      <path d="M4 12h16m-4-4 4 4-4 4M8 8l-4 4 4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </div>
                  <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">Modbus Serial</h3>
                </header>
              </div>
              <div class="px-4 py-3 space-y-4">

                <!-- Serial Log enable + 사용 한 줄 -->
                <div class="flex gap-3">
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-2">Log enable</label>
                    <div
                      class="relative inline-flex items-center cursor-pointer"
                      @click="inputDict.modbus.serial_log = inputDict.modbus.serial_log === 1 ? 0 : 1"
                    >
                      <div
                        class="w-11 h-6 rounded-full transition-colors duration-200"
                        :class="inputDict.modbus.serial_log === 1 ? 'bg-sky-500' : 'bg-gray-300 dark:bg-gray-600'"
                      ></div>
                      <div
                        class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
                        :class="inputDict.modbus.serial_log === 1 ? 'translate-x-5' : 'translate-x-0'"
                      ></div>
                    </div>
                  </div>
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-2">{{ t("config.plansPanel.modbus.rtu_use") }}</label>
                    <select
                      v-model.number="inputDict.modbus.rtu_use"
                      class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-violet-500 focus:border-violet-500"
                    >
                      <option :value="0">{{ t("config.plansPanel.modbus.no") }}</option>
                      <option :value="1">{{ t("config.plansPanel.modbus.yes") }}</option>
                    </select>
                  </div>
                </div>

                <!-- Baud Rate + Parity -->
                <div class="flex space-x-3">
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-2">{{ t("config.plansPanel.modbus.baudrate") }}</label>
                    <select
                      :disabled="inputDict.modbus.rtu_use == 0"
                      v-model.number="inputDict.modbus.baud_rate"
                      class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-violet-500 focus:border-violet-500"
                    >
                      <option :value="0">9600</option>
                      <option :value="1">19200</option>
                      <option :value="2">38400</option>
                      <option :value="3">57600</option>
                      <option :value="4">115200</option>
                    </select>
                  </div>
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-2">{{ t("config.plansPanel.modbus.parity") }}</label>
                    <select
                      :disabled="inputDict.modbus.rtu_use == 0"
                      v-model.number="inputDict.modbus.parity"
                      class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-violet-500 focus:border-violet-500"
                    >
                      <option :value="0">None</option>
                      <option :value="1">Odd</option>
                      <option :value="2">Even</option>
                    </select>
                  </div>
                </div>

                <!-- Data Bits + Stop Bits -->
                <div class="flex space-x-3">
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-2">{{ t("config.plansPanel.modbus.dbits") }}</label>
                    <select
                      :disabled="inputDict.modbus.rtu_use == 0"
                      v-model.number="inputDict.modbus.data_bits"
                      class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-violet-500 focus:border-violet-500"
                    >
                      <option :value="7">7</option>
                      <option :value="8">8</option>
                    </select>
                  </div>
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-2">{{ t("config.plansPanel.modbus.sbits") }}</label>
                    <select
                      :disabled="inputDict.modbus.rtu_use == 0"
                      v-model.number="inputDict.modbus.stop_bits"
                      class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-violet-500 focus:border-violet-500"
                    >
                      <option :value="1">1</option>
                      <option :value="2">2</option>
                    </select>
                  </div>
                </div>

<!-- Serial Type 테이블 -->
<div :class="inputDict.modbus.rtu_use == 0 ? 'opacity-40 pointer-events-none' : ''">
  <div class="text-xs text-gray-800 dark:text-gray-100 font-semibold uppercase mb-2">Serial Device Info</div>
  <div class="border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
    <!-- 헤더 -->
    <div class="grid text-center text-xs font-semibold text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50" style="grid-template-columns: 55px 1fr 80px">
      <div class="px-1 py-2 border-r border-gray-200 dark:border-gray-600">idx</div>
      <div class="px-2 py-2 border-r border-gray-200 dark:border-gray-600">type</div>
      <div class="px-1 py-2">devId</div>
    </div>
    <!-- 행 -->
    <div
      v-for="item in inputDict.modbus.serialinfo"
      :key="item.id"
      class="grid text-center text-sm border-t border-gray-200 dark:border-gray-700"
      style="grid-template-columns: 55px 1fr 80px"
    >
      <div class="px-1 py-1.5 border-r border-gray-200 dark:border-gray-600 flex items-center justify-center text-gray-700 dark:text-gray-200">
        {{ item.id }}
      </div>
      <div class="px-2 py-1.5 border-r border-gray-200 dark:border-gray-600 flex items-center justify-center">
        <select
          v-model.number="item.type"
          :disabled="inputDict.modbus.rtu_use == 0"
          class="form-select w-full text-sm bg-white dark:bg-gray-700 border-gray-300 rounded focus:ring-violet-500 focus:border-violet-500 py-0.5"
        >
          <option :value="0">ExtIO</option>
          <option :value="1">P300-C</option>
        </select>
      </div>
      <div class="px-1 py-1.5 flex items-center justify-center">
        <input
          v-model.number="item.devId"
          type="number"
          min="1"
          max="255"
          :disabled="inputDict.modbus.rtu_use == 0"
          class="form-input w-full text-sm text-center py-0.5"
        />
      </div>
    </div>
  </div>
</div>

              </div>
            </div>
          </div>

          <!-- ④ MQTT -->
          <div class="relative col-span-full xl:col-span-3 flex flex-col gap-6">
            <div class="relative xl:col-span-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg flex flex-col flex-1">
              <div class="absolute top-0 left-0 right-0 h-0.5 bg-blue-500" aria-hidden="true"></div>
              <div class="px-5 pt-5 pb-6 border-b border-gray-200 dark:border-gray-700/60">
                <header class="flex items-center mb-2">
                  <div class="w-6 h-6 rounded-full shrink-0 bg-blue-500 mr-3">
                    <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 20h18M5 16l4-4 4 4 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </div>
                  <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">MQTT</h3>
                </header>
              </div>
              <div class="px-4 py-3 space-y-4">
                <div class="text-xs text-gray-800 dark:text-gray-100 font-semibold uppercase mb-1">MQTT</div>

                <!-- Use -->
                <div class="flex space-x-3">
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-1.5">Use</label>
                    <select
                      v-model="inputDict.MQTT.Use"
                      class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option :value="0">{{ t("config.plansPanel.modbus.no") }}</option>
                      <option :value="1">{{ t("config.plansPanel.modbus.yes") }}</option>
                    </select>
                  </div>
                </div>

                <!-- LTE Use -->
                <div v-if="inputDict.MQTT.Use === 1 && inputDict.MQTT.Type >= 1" class="flex items-center justify-between">
                  <label class="block text-sm font-medium">LTE Use</label>
                  <div
                    class="relative inline-flex items-center cursor-pointer"
                    @click="inputDict.MQTT.lteuse = inputDict.MQTT.lteuse === 1 ? 0 : 1"
                  >
                    <div
                      class="w-11 h-6 rounded-full transition-colors duration-200"
                      :class="inputDict.MQTT.lteuse === 1 ? 'bg-sky-500' : 'bg-gray-300 dark:bg-gray-600'"
                    ></div>
                    <div
                      class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
                      :class="inputDict.MQTT.lteuse === 1 ? 'translate-x-5' : 'translate-x-0'"
                    ></div>
                  </div>
                </div>

                <!-- Type -->
                <div class="flex-1" v-if="inputDict.MQTT.Use === 1">
                  <label class="block text-sm font-medium mb-1.5">Type</label>
                  <select
                    v-model="inputDict.MQTT.Type"
                    class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option :value="0">Local</option>
                    <option :value="1">public</option>
                    <option :value="2">AWSIoTCore</option>
                  </select>
                </div>

                <!-- Host -->
                <div v-if="inputDict.MQTT.Use === 1">
                  <label class="block text-sm font-medium mb-1.5">Host</label>
                  <input v-model="inputDict.MQTT.host" class="form-input w-full" type="text" placeholder="Enter MQTT host" />
                </div>

                <!-- Port & Device ID -->
                <div v-if="inputDict.MQTT.Use === 1" class="flex space-x-3">
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-1.5">Port</label>
                    <input v-model.number="inputDict.MQTT.port" class="form-input w-full" type="number" placeholder="1883" />
                  </div>
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-1.5">Device ID</label>
                    <input :value="inputDict.MQTT.device_id" class="form-input w-full bg-gray-100 dark:bg-gray-700" type="text" readonly />
                  </div>
                </div>

                <!-- externalPort & externalUrl (public) -->
                <div v-if="inputDict.MQTT.Use === 1 && inputDict.MQTT.Type === 1" class="flex space-x-3">
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-1.5">externalPort</label>
                    <input v-model="inputDict.MQTT.externalport" class="form-input w-full" type="number" placeholder="Enter external port" />
                  </div>
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-1.5">externalUrl</label>
                    <input v-model="inputDict.MQTT.url" class="form-input w-full" type="text" placeholder="Enter url" />
                  </div>
                </div>

                <!-- Username & Password (Local) -->
                <div v-if="inputDict.MQTT.Use === 1 && inputDict.MQTT.Type === 0" class="flex space-x-3">
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-1.5">Username</label>
                    <input v-model="inputDict.MQTT.username" class="form-input w-full" type="text" placeholder="Enter username" />
                  </div>
                  <div class="flex-1">
                    <label class="block text-sm font-medium mb-1.5">Password</label>
                    <input v-model="inputDict.MQTT.password" class="form-input w-full" type="password" placeholder="Enter password" />
                  </div>
                </div>

                <!-- AWS IoT Core Certificates -->
                <div v-if="inputDict.MQTT.Use === 1 && inputDict.MQTT.Type === 2" class="space-y-3">
                  <div class="text-xs text-gray-800 dark:text-gray-100 font-semibold uppercase">Certificates</div>
                  <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4">
                    <input
                      type="file"
                      multiple
                      accept=".pem,.crt,.key,.cert"
                      @change="handleCertUpload"
                      class="hidden"
                      ref="certFileInput"
                    />
                    <div class="text-center">
                      <svg class="mx-auto h-10 w-10 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                      <button type="button" @click="$refs.certFileInput.click()" class="mt-2 btn-sm bg-blue-500 text-white hover:bg-blue-600">
                        Select Certificate Files
                      </button>
                      <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">.pem, .crt, .key, .cert files</p>
                    </div>
                  </div>
                  <div v-if="uploadedCerts.length > 0" class="space-y-2">
                    <div class="text-xs font-medium text-gray-600 dark:text-gray-300">Uploaded Files:</div>
                    <div
                      v-for="(cert, index) in uploadedCerts"
                      :key="index"
                      class="flex items-center justify-between bg-gray-50 dark:bg-gray-700 rounded px-3 py-2"
                    >
                      <div class="flex items-center space-x-2">
                        <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span class="text-sm text-gray-700 dark:text-gray-200">{{ cert.filename }}</span>
                      </div>
                      <button @click="removeCert(index)" class="text-red-500 hover:text-red-700">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <div v-if="certUploadMessage" :class="certUploadSuccess ? 'text-green-600' : 'text-red-600'" class="text-sm">
                    {{ certUploadMessage }}
                  </div>
                </div>

              </div>
            </div>
          </div>

          <WaveformFTPCard
            :showFTP="inputDict.useFuction.ftp === 1 || inputDict.useFuction.ftp === true"
          />
          <SNTPCard
            :showSNTP="inputDict.useFuction.sntp === 1 || inputDict.useFuction.sntp === true"
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
    const uploadedCerts = ref([]);
    const certUploadMessage = ref('');
    const certUploadSuccess = ref(false);
    const certFileInput = ref(null);
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

    const defaultSerialtype = [
      { id: 1, type: 0, devId: 1 },
      { id: 2, type: 0, devId: 2 },
      { id: 3, type: 0, devId: 3 },
      { id: 4, type: 0, devId: 4 },
    ];

    const ensureSerialtype = () => {
      if (!inputDict.value.modbus) return;
      if (!inputDict.value.modbus.serialinfo || inputDict.value.modbus.serialinfo.length === 0) {
        inputDict.value.modbus.serialinfo = defaultSerialtype.map(item => ({ ...item }));
      }
    };

    // 서버에서 데이터 로드 후에도 serialinfo 없으면 채워넣기
    watch(
      () => inputDict.value.modbus,
      () => { ensureSerialtype(); },
      { immediate: true, deep: false }
    );

    onMounted(() => {
      ensureSerialtype();
    });

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

    const handleCertUpload = async (event) => {
      const files = event.target.files;
      if (!files || files.length === 0) return;
      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      try {
        certUploadMessage.value = 'Uploading...';
        certUploadSuccess.value = false;
        const response = await axios.post('/setting/uploadCerts', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        if (response.data.passOK === 1) {
          certUploadSuccess.value = true;
          certUploadMessage.value = `${response.data.uploaded.length} file(s) uploaded successfully`;
          await loadCertList();
        } else {
          certUploadMessage.value = response.data.error || 'Upload failed';
        }
      } catch (error) {
        certUploadMessage.value = 'Upload failed: ' + (error.response?.data?.error || error.message);
      }
      event.target.value = '';
    };

    const loadCertList = async () => {
      try {
        const response = await axios.get('/setting/listCerts');
        if (response.data.passOK === 1) {
          uploadedCerts.value = response.data.files;
        }
      } catch (error) {
        console.error('Failed to load cert list:', error);
      }
    };

    const removeCert = async (index) => {
      const cert = uploadedCerts.value[index];
      if (!confirm(`Delete ${cert.filename}?`)) return;
      try {
        const response = await axios.delete(`/setting/deleteCert/${cert.filename}`);
        if (response.data.passOK === 1) {
          uploadedCerts.value.splice(index, 1);
          certUploadMessage.value = 'File deleted';
          certUploadSuccess.value = true;
        }
      } catch (error) {
        certUploadMessage.value = 'Delete failed';
        certUploadSuccess.value = false;
      }
    };

    watch(
      () => inputDict.value.MQTT?.Type,
      (newVal) => {
        if (newVal === 'AWSIoTCore') {
          loadCertList();
        }
      },
      { immediate: true }
    );

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
      uploadedCerts,
      certUploadMessage,
      certUploadSuccess,
      certFileInput,
      handleCertUpload,
      removeCert,
    };
  },
};
</script>