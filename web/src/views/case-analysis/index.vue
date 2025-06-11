<template>
    <div class="min-h-screen p-4">
        <!-- 上部分操作区域 -->
        <div class="mb-8 p-6 bg-white rounded-lg shadow-md">
            <div class="flex flex-col md:flex-row gap-4">
                <!-- 上传按钮 -->
                <label class="flex items-center px-4 py-2 bg-blue-500 text-white rounded cursor-pointer">
                    <i class="fas fa-upload mr-2"></i>
                    <span>上传笔录文件</span>
                    <input 
                        type="file" 
                        class="hidden" 
                        accept=".txt" 
                        @change="handleFileUpload"
                    >
                </label>

                <!-- 案件编号输入 -->
                <div class="flex flex-col w-full md:w-auto">
                    <input 
                        type="text" 
                        v-model="keyNumber"
                        placeholder="请输入案件编号"
                        class="px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                </div>

                <!-- 搜索按钮 -->
                <button 
                    @click="searchByKey"
                    class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
                >
                    <i class="fas fa-search mr-2"></i>搜索笔录
                </button>

                <!-- 开始分析按钮 -->
                <button 
                    @click="startAnalysis"
                    class="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors self-end md:self-auto"
                >
                    <i class="fas fa-brain mr-2"></i>开始分析
                </button>
            </div>
        </div>

        <!-- 下部分文本展示区域 -->
        <div class="bg-gray-100 p-6 rounded-lg min-h-[400px] flex flex-col md:flex-row gap-6">
            <!-- 右上角下拉框 -->
            <div v-if="cases.length > 0" class="absolute top-4 right-4 z-10">
                <select 
                    v-model="currentCaseIndex"
                    class="px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option v-for="(caseItem, index) in cases" :key="index" :value="index">
                        第{{ index + 1 }}篇
                    </option>
                </select>
            </div>

            <!-- 左侧原文展示 -->
            <div class="flex-1 min-h-[300px]">
                <div
                    contenteditable="true" 
                    @input="handleTextUpdate"
                    class="w-full h-full p-4 border rounded-lg bg-white text-gray-900 overflow-y-auto max-h-[600px]"
                    :class="{'min-h-[300px]': true}"
                >
                    {{ currentText }}
                </div>
            </div>

            <!-- 右侧分析结果 -->
            <div class="flex-1 min-h-[300px]">
                <div v-if="analysisResult" class="p-4 bg-white rounded-lg h-full overflow-auto">
                    <h3 class="text-lg font-bold mb-4">分析结果</h3>
                    <table class="w-full border-collapse">
                        <tr v-for="(value, key) in analysisResult" :key="key" class="border-b">
                            <td class="py-2 font-medium w-1/3">{{ key }}</td>
                            <td class="py-2">
                                <!-- 处理数组和对象 -->
                                <template v-if="Array.isArray(value)">
                                    <ul class="pl-4 list-disc">
                                        <li v-for="(item, idx) in value" :key="idx">
                                            {{ item }}
                                        </li>
                                    </ul>
                                </template>
                                <template v-else-if="typeof value === 'object'">
                                    <table class="w-full mt-2">
                                        <tr v-for="(v, k) in value" :key="k" class="border-b">
                                            <td class="py-1 font-medium w-1/3">{{ k }}</td>
                                            <td class="py-1">{{ v }}</td>
                                        </tr>
                                    </table>
                                </template>
                                <template v-else>
                                    {{ value }}
                                </template>
                            </td>
                        </tr>
                    </table>
                </div>
                <div v-else class="p-4 bg-white rounded-lg h-full flex items-center justify-center">
                    <p class="text-gray-500">等待分析结果...</p>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { ref, computed } from 'vue';
    //import { ElMessage } from 'element-plus';
    import api from '@/api';
   
    // 响应式变量
    const keyNumber = ref('');
    const cases = ref([]);
    const currentCaseIndex = ref(0);
    const analysisResult = ref(null);

    // 当前显示的文本内容（来自上传或搜索）
    const currentText = computed(() => {
        if (cases.value.length === 0) return '';
        return cases.value[currentCaseIndex.value]?.content || '';
    });

    // 处理文件上传
    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('files', file);
    
        try {
            const res = await api.uploadCaseFile(formData);
            cases.value = res.data.map(item => ({ content: item }));
            currentCaseIndex.value = 0;
            e.target.value = ''; // 清空文件选择
        } catch (err) {
            console.error('文件上传失败:', err);
        }
    };

    // 处理文本编辑
    const handleTextUpdate = (e) => {
        const newText = e.target.innerHTML;
        cases.value[currentCaseIndex.value].content = newText;
    };

    // 按案件编号搜索
    const searchByKey = async () => {
        const caseNumber = keyNumber.value.trim();
        if (!caseNumber) {
            $message.warning('请输入案件编号')
            return;
        }
        // 检查案件编号格式  A3303026900002023035082
        const regex = /^A\d{22}$/; // 示例正则：以大写字母A开头，后跟22个数字
        if (!regex.test(caseNumber)) {
            $message.error('案件编号格式不正确')
            return;
        }
        
        try {
            const res = await api.getCaseByKey({caseNumber : caseNumber});
            cases.value = res.data.map(item => ({ content: item }));
            currentCaseIndex.value = 0;
        } catch (err) {
            console.error('搜索笔录失败:', err);
            cases.value = [];
        }
    };

    // 开始分析
    const startAnalysis = async () => {
        if (!currentText.value) {
            $message.warning('请先加载笔录内容')
            return;
        }
        try {
            const res = await api.analyzeCase(currentText.value);
            analysisResult.value = res.data;
            $message.success('分析完成')
        } catch (err) {
            console.error('分析失败:', err);
            $message.error('分析失败')
        }
    };
</script>

<style scoped>
    [contenteditable]:focus {
        outline: 2px solid #3b82f6;
    }

    table {
        table-layout: fixed;
        word-break: break-word;
    }

    td {
        max-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
</style>