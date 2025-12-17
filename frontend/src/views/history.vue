<script setup>
import {ref, onMounted} from 'vue';
import apiClient, {getImageUrl} from '@/api.js';

const historyLogs = ref([]);
const loading = ref(true);

const fetchHistory = async () => {
  try {
    const res = await apiClient.get('/api/history');
    historyLogs.value = res.data;
  } catch (error) {
    console.error("Failed to fetch history:", error);
  } finally {
    loading.value = false;
  }
};

// 格式化時間字串
const formatDate = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleString();
};

onMounted(() => {
  fetchHistory();
});
</script>

<template>
  <div class="w-full font-sans">
    <header class="mb-10 text-center md:text-left pb-6">
      <h1 class="text-3xl font-extrabold tracking-tight text-[#102d47]">
        違規紀錄查詢
      </h1>
      <p class="mt-2 text-[#668199] text-sm font-medium uppercase tracking-wide">
        Violation History Log
      </p>
    </header>

    <div v-if="loading" class="text-center text-[#668199] py-10 animate-pulse">
      載入紀錄中...
    </div>

    <div v-else-if="historyLogs.length === 0"
         class="text-center py-20 bg-white rounded-2xl border border-gray-100 shadow-sm">
      <h3 class="text-xl font-bold text-[#102d47]">目前沒有違規紀錄</h3>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

      <div
          v-for="log in historyLogs"
          :key="log.id"
          class="bg-white rounded-2xl shadow-[0px_3px_20px_0px_#8e9ca90d] border border-gray-100 overflow-hidden hover:-translate-y-1 transition-transform duration-300"
      >
        <div class="relative h-48 bg-gray-100 border-b border-gray-100 group">
          <img
              :src="getImageUrl(log.image_url)"
              alt="Evidence"
              class="w-full h-full object-cover"
              loading="lazy"
          />
          <div
              class="absolute top-3 left-3 bg-red-600/90 text-white text-xs font-bold px-3 py-1 rounded-full shadow-md backdrop-blur-sm">
            VIOLATION
          </div>
          <a :href="getImageUrl(log.image_url)" target="_blank"
             class="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white font-bold cursor-zoom-in">
            點擊查看大圖
          </a>
        </div>

        <div class="p-5">
          <div class="flex justify-between items-start mb-3">
            <div>
              <p class="text-xs font-bold text-[#668199] uppercase tracking-wider mb-1">Detected Time</p>
              <p class="text-[#102d47] font-bold font-mono">{{ formatDate(log.timestamp) }}</p>
            </div>
            <span class="text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded font-mono">
              ID: #{{ log.id }}
            </span>
          </div>

          <div class="pt-3 border-t border-gray-100">
            <p class="text-sm text-gray-600">
              <span class="font-bold text-red-500">Reason:</span> {{ log.status }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>