<script setup>
import {ref, computed} from 'vue';
import apiClient from '@/api.js';

const selectedFile = ref(null);
const uploadStatus = ref("");
const isUploading = ref(false);
const testResult = ref(null);

const testResultClass = computed(() => {
  if (!testResult.value) return '';
  return testResult.value.violation_detected ? 'text-red-600 font-bold' : 'text-green-600 font-bold';
});

const handleFileChange = (event) => {
  const file = event.target.files[0];
  if (file) {
    selectedFile.value = file;
    testResult.value = null;
    uploadStatus.value = "";
  }
};

const uploadImage = async () => {
  if (!selectedFile.value) {
    alert("請先選擇一張照片！");
    return;
  }

  isUploading.value = true;
  uploadStatus.value = "分析中...";

  const formData = new FormData();
  formData.append("file", selectedFile.value);

  try {
    const res = await apiClient.post('/api/upload_form', formData, {
      headers: {'Content-Type': 'multipart/form-data'}
    });

    testResult.value = res.data;
    uploadStatus.value = "分析完成！";

  } catch (error) {
    console.error("Upload Error", error);
    uploadStatus.value = "上傳失敗，請檢查後端是否開啟";
  } finally {
    isUploading.value = false;
  }
};
</script>

<template>
  <div class="w-full font-sans">
    <header class="mb-10 text-center md:text-left pb-6">
      <h1 class="text-3xl font-extrabold tracking-tight text-[#102d47]">
        手動上傳測試
      </h1>
      <p class="mt-2 text-[#668199] text-sm font-medium uppercase tracking-wide">
        Manual Violation Detection Test
      </p>
    </header>

    <div class=" mx-auto">
      <div class="bg-white p-8 rounded-2xl shadow-[0px_3px_20px_0px_#8e9ca90d] border border-gray-100">
        <h3 class="text-lg font-bold text-[#102d47] mb-6 border-b border-gray-100 pb-2">
          Upload Image
        </h3>

        <div class="flex flex-col gap-6">

          <div class="space-y-2">
            <label class="text-sm font-bold text-gray-500">選擇圖片</label>
            <input
                type="file"
                @change="handleFileChange"
                accept="image/*"
                class="block w-full text-sm text-gray-500
                file:mr-4 file:py-3 file:px-6
                file:rounded-xl file:border-0
                file:text-sm file:font-bold
                file:bg-[#2f73f2]/10 file:text-[#2f73f2]
                hover:file:bg-[#2f73f2]/20
                cursor-pointer transition-colors border border-dashed border-gray-300 rounded-xl p-2"
            />
          </div>

          <div v-if="selectedFile" class="text-sm text-gray-500 flex items-center gap-2">
            <span>📄</span> {{ selectedFile.name }}
          </div>

          <button
              @click="uploadImage"
              :disabled="isUploading || !selectedFile"
              class="w-full bg-[#2f73f2] text-white px-6 py-4 rounded-xl font-bold text-lg hover:bg-blue-600 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-500/20 active:scale-95 flex justify-center items-center gap-2"
          >
            <span v-if="isUploading"
                  class="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></span>
            {{ isUploading ? '正在分析...' : '開始偵測 (Start Detection)' }}
          </button>
        </div>

        <div v-if="testResult" class="mt-8 bg-gray-50 p-6 rounded-xl border border-gray-200 animate-fade-in">
          <h4 class="text-gray-500 font-bold mb-4 text-sm uppercase tracking-wider">Analysis Result</h4>

          <div class="flex items-center justify-between mb-2">
            <span class="text-gray-600 font-medium">Message:</span>
            <span class="text-lg" :class="testResultClass">{{ testResult.message }}</span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-gray-600 font-medium">Violation:</span>
            <span
                class="px-3 py-1 rounded-full text-sm font-bold"
                :class="testResult.violation_detected ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'"
            >
              {{ testResult.violation_detected ? 'DETECTED' : 'SAFE' }}
            </span>
          </div>
        </div>
        <p v-else-if="uploadStatus" class="text-sm text-[#668199] text-center pt-6 font-medium">{{ uploadStatus }}</p>
      </div>
    </div>
  </div>
</template>