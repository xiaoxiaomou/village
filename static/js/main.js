// 乡村记忆系统 - 主JS文件

const API_BASE = '';

// 通用API请求
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(API_BASE + url, { ...defaultOptions, ...options });
        if (!response.ok) {
            const text = await response.text();
            throw new Error(`HTTP ${response.status}: ${text}`);
        }
        return await response.json();
    } catch (error) {
        console.warn('API Request failed:', url, error.message);
        return null;
    }
}

// 加载记忆列表
async function loadMemories(page = 1, perPage = 10, tag = '', search = '') {
    let url = `/api/memories?page=${page}&per_page=${perPage}`;
    if (tag) url += `&tag=${tag}`;
    if (search) url += `&search=${search}`;
    
    const data = await apiRequest(url);
    return data;
}

// 加载时间轴
async function loadTimeline() {
    const data = await apiRequest('/api/memories/timeline');
    return data;
}

// 加载标签列表
async function loadTags() {
    const data = await apiRequest('/api/tags');
    return data;
}

// 加载人物列表
async function loadPeople() {
    const data = await apiRequest('/api/people');
    return data;
}

// 创建记忆
async function createMemory(formData) {
    const data = await apiRequest('/api/memories', {
        method: 'POST',
        body: JSON.stringify(formData)
    });
    return data;
}

// 上传文件
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error('Upload failed');
        return await response.json();
    } catch (error) {
        console.error('Upload Error:', error);
        alert('上传失败');
        return null;
    }
}

// 导出备份
async function exportBackup() {
    try {
        const response = await fetch('/api/backups/export', {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Export failed');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = '乡村记忆备份_' + new Date().toISOString().split('T')[0] + '.zip';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Export Error:', error);
        alert('导出失败');
    }
}

// 搜索记忆
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', () => {
            const search = searchInput.value.trim();
            if (search) {
                window.location.href = `/memories?search=${encodeURIComponent(search)}`;
            }
        });
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchBtn.click();
        });
    }
}

// 标签筛选
function setupTagFilter() {
    const tagLinks = document.querySelectorAll('.tag-filter-link');
    tagLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tag = link.dataset.tag;
            window.location.href = `/memories?tag=${encodeURIComponent(tag)}`;
        });
    });
}

// 表单验证
function validateMemoryForm() {
    const title = document.getElementById('memoryTitle');
    const content = document.getElementById('memoryContent');
    const memoryDate = document.getElementById('memoryDate');
    
    if (title && !title.value.trim()) {
        alert('请输入记忆标题');
        title.focus();
        return false;
    }
    if (content && !content.value.trim()) {
        alert('请输入记忆内容');
        content.focus();
        return false;
    }
    if (memoryDate && !memoryDate.value) {
        alert('请选择记忆日期');
        memoryDate.focus();
        return false;
    }
    return true;
}

// 图片预览
function setupImagePreview() {
    const previewContainer = document.getElementById('imagePreview');
    const fileInput = document.getElementById('photoUpload');
    
    if (fileInput && previewContainer) {
        fileInput.addEventListener('change', (e) => {
            previewContainer.innerHTML = '';
            const files = e.target.files;
            for (let file of files) {
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.style.maxWidth = '200px';
                        img.style.margin = '5px';
                        previewContainer.appendChild(img);
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    }
}

// 语音录制
function setupVoiceRecorder() {
    const recordBtn = document.getElementById('voiceRecordBtn');
    const stopBtn = document.getElementById('voiceStopBtn');
    
    if (recordBtn && stopBtn) {
        let mediaRecorder;
        let audioChunks = [];
        
        recordBtn.addEventListener('click', async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (e) => {
                    audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    uploadFile(audioBlob).then(result => {
                        if (result) {
                            console.log('Voice uploaded:', result);
                        }
                    });
                };
                
                mediaRecorder.start();
                recordBtn.disabled = true;
                stopBtn.disabled = false;
            } catch (error) {
                alert('无法访问麦克风');
            }
        });
        
        stopBtn.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                recordBtn.disabled = false;
                stopBtn.disabled = true;
            }
        });
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    setupSearch();
    setupTagFilter();
    setupImagePreview();
    setupVoiceRecorder();
});

// 显示加载中
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '<div class="loading"></div>';
    }
}

// 显示消息
function showMessage(message, type = 'info') {
    const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
    alert(`${icon} ${message}`);
}
