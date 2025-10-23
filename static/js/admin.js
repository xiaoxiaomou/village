// 管理后台JavaScript功能

// 全局变量
let currentPage = 1;
let currentSection = 'dashboard';

// 页面切换功能
function showSection(sectionName) {
    // 隐藏所有内容区域
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // 移除所有导航链接的active类
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // 显示目标内容区域
    document.getElementById(sectionName).classList.add('active');
    
    // 添加active类到对应的导航链接
    event.target.classList.add('active');
    
    currentSection = sectionName;
    
    // 根据不同的section加载对应数据
    switch(sectionName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'news':
            loadNews();
            loadCategories();
            break;
        case 'categories':
            loadCategories();
            break;
        case 'messages':
            loadMessages();
            break;
        case 'services':
            loadServices();
            break;
        case 'government':
            loadGovernment();
            break;
        case 'village':
            loadVillage();
            break;
        case 'users':
            loadUsers();
            break;
    }
}

// 退出登录
function logout() {
    if (confirm('确定要退出登录吗？')) {
        fetch('/admin/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            alert(data.msg);
            window.location.href = '/admin/login';
        })
        .catch(error => {
            console.error('退出登录失败:', error);
        });
    }
}

// 仪表盘功能
function loadDashboard() {
    loadStats();
    loadRecentNews();
    loadRecentMessages();
}

function loadStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            const statsCards = document.getElementById('stats-cards');
            statsCards.innerHTML = `
                <div class="col-md-3 mb-3">
                    <div class="card text-white bg-primary">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h4>${data.news_count || 0}</h4>
                                    <p>新闻总数</p>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-newspaper fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card text-white bg-success">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h4>${data.message_count || 0}</h4>
                                    <p>留言总数</p>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-comments fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card text-white bg-warning">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h4>${data.unread_message_count || 0}</h4>
                                    <p>待回复留言</p>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-exclamation-triangle fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card text-white bg-info">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h4>${data.user_count || 0}</h4>
                                    <p>用户总数</p>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-users fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error('加载统计数据失败:', error);
        });
}

function refreshStats() {
    loadStats();
}

function loadRecentNews() {
    fetch('/admin/news')
        .then(response => response.json())
        .then(data => {
            const recentNews = document.getElementById('recent-news');
            if (data.length > 0) {
                const newsHtml = data.slice(0, 5).map(news => `
                    <div class="mb-2">
                        <h6 class="mb-1">${news.title}</h6>
                        <small class="text-muted">${formatDate(news.create_time)}</small>
                    </div>
                `).join('');
                recentNews.innerHTML = newsHtml;
            } else {
                recentNews.innerHTML = '<p class="text-muted">暂无新闻</p>';
            }
        })
        .catch(error => {
            console.error('加载最近新闻失败:', error);
        });
}

function loadRecentMessages() {
    fetch('/admin/messages')
        .then(response => response.json())
        .then(data => {
            const recentMessages = document.getElementById('recent-messages');
            if (data.length > 0) {
                const messagesHtml = data.slice(0, 5).map(message => `
                    <div class="mb-2">
                        <h6 class="mb-1">${message.name}</h6>
                        <p class="mb-1 small">${truncateText(message.content, 50)}</p>
                        <small class="text-muted">${formatDate(message.create_time)}</small>
                        ${!message.reply ? '<span class="badge bg-warning ms-2">待回复</span>' : ''}
                    </div>
                `).join('');
                recentMessages.innerHTML = messagesHtml;
            } else {
                recentMessages.innerHTML = '<p class="text-muted">暂无留言</p>';
            }
        })
        .catch(error => {
            console.error('加载最近留言失败:', error);
        });
}

// 新闻管理功能
function loadNews(page = 1, search = '', categoryId = '') {
    let url = `/admin/news?page=${page}&per_page=10`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (categoryId) url += `&category_id=${categoryId}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('news-table-body');
            if (data.data && data.data.length > 0) {
                const newsHtml = data.data.map(news => `
                    <tr>
                        <td>${news.id}</td>
                        <td>${news.title}</td>
                        <td>${news.category_name || '未分类'}</td>
                        <td>${news.author || '系统'}</td>
                        <td>${formatDate(news.create_time)}</td>
                        <td class="table-actions">
                            <button class="btn btn-sm btn-outline-primary" onclick="editNews(${news.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteNews(${news.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
                tbody.innerHTML = newsHtml;
                
                // 更新分页
                if (data.pagination) {
                    updatePagination('news-pagination', data.pagination, loadNews);
                }
            } else {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">暂无数据</td></tr>';
            }
        })
        .catch(error => {
            console.error('加载新闻失败:', error);
        });
}

function searchNews() {
    const search = document.getElementById('newsSearch').value;
    const categoryId = document.getElementById('newsCategoryFilter').value;
    loadNews(1, search, categoryId);
}

function showNewsModal(newsId = null) {
    const isEdit = newsId !== null;
    const title = isEdit ? '编辑新闻' : '添加新闻';
    
    const modalHtml = `
        <div class="modal fade" id="newsModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="newsForm">
                            <div class="form-group">
                                <label for="newsTitle">标题</label>
                                <input type="text" class="form-control" id="newsTitle" required>
                            </div>
                            <div class="form-group">
                                <label for="newsCategory">分类</label>
                                <select class="form-select" id="newsCategory">
                                    <option value="">请选择分类</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="newsContent">内容</label>
                                <textarea class="form-control" id="newsContent" rows="10" required></textarea>
                            </div>
                            <div class="form-group">
                                <label for="newsImage">图片</label>
                                <input type="file" class="form-control" id="newsImage" accept="image/*">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="saveNews(${newsId})">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('modal-container').innerHTML = modalHtml;
    
    // 加载分类选项
    loadCategoryOptions('newsCategory');
    
    // 如果是编辑模式，加载新闻数据
    if (isEdit) {
        loadNewsData(newsId);
    }
    
    const modal = new bootstrap.Modal(document.getElementById('newsModal'));
    modal.show();
}

function saveNews(newsId) {
    const title = document.getElementById('newsTitle').value;
    const categoryId = document.getElementById('newsCategory').value;
    const content = document.getElementById('newsContent').value;
    const imageFile = document.getElementById('newsImage').files[0];
    
    if (!title || !content) {
        alert('请填写标题和内容');
        return;
    }
    
    const newsData = {
        title: title,
        category_id: categoryId || null,
        content: content
    };
    
    const url = newsId ? `/admin/news/${newsId}` : '/admin/news';
    const method = newsId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(newsData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.msg) {
            alert(data.msg);
            bootstrap.Modal.getInstance(document.getElementById('newsModal')).hide();
            loadNews();
        }
    })
    .catch(error => {
        console.error('保存新闻失败:', error);
        alert('保存失败');
    });
}

function editNews(newsId) {
    showNewsModal(newsId);
}

function deleteNews(newsId) {
    if (confirm('确定要删除这条新闻吗？')) {
        fetch(`/admin/news/${newsId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.msg);
            loadNews();
        })
        .catch(error => {
            console.error('删除新闻失败:', error);
        });
    }
}

// 分类管理功能
function loadCategories() {
    fetch('/admin/categories')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('categories-table-body');
            if (data.length > 0) {
                const categoriesHtml = data.map(category => `
                    <tr>
                        <td>${category.id}</td>
                        <td>${category.name}</td>
                        <td class="table-actions">
                            <button class="btn btn-sm btn-outline-primary" onclick="editCategory(${category.id}, '${category.name}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteCategory(${category.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
                tbody.innerHTML = categoriesHtml;
            } else {
                tbody.innerHTML = '<tr><td colspan="3" class="text-center">暂无数据</td></tr>';
            }
            
            // 更新新闻管理页面的分类筛选器
            updateCategoryFilter(data);
        })
        .catch(error => {
            console.error('加载分类失败:', error);
        });
}

function showCategoryModal(categoryId = null, categoryName = '') {
    const isEdit = categoryId !== null;
    const title = isEdit ? '编辑分类' : '添加分类';
    
    const modalHtml = `
        <div class="modal fade" id="categoryModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="categoryForm">
                            <div class="form-group">
                                <label for="categoryName">分类名称</label>
                                <input type="text" class="form-control" id="categoryName" value="${categoryName}" required>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="saveCategory(${categoryId})">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('modal-container').innerHTML = modalHtml;
    const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
    modal.show();
}

function saveCategory(categoryId) {
    const name = document.getElementById('categoryName').value;
    
    if (!name) {
        alert('请填写分类名称');
        return;
    }
    
    const categoryData = { name: name };
    const url = categoryId ? `/admin/categories/${categoryId}` : '/admin/categories';
    const method = categoryId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(categoryData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.msg);
        bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
        loadCategories();
    })
    .catch(error => {
        console.error('保存分类失败:', error);
        alert('保存失败');
    });
}

function editCategory(categoryId, categoryName) {
    showCategoryModal(categoryId, categoryName);
}

function deleteCategory(categoryId) {
    if (confirm('确定要删除这个分类吗？')) {
        fetch(`/admin/categories/${categoryId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.msg);
            loadCategories();
        })
        .catch(error => {
            console.error('删除分类失败:', error);
        });
    }
}

// 留言管理功能
function loadMessages() {
    fetch('/admin/messages')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('messages-table-body');
            if (data.length > 0) {
                const messagesHtml = data.map(message => `
                    <tr>
                        <td>${message.id}</td>
                        <td>${message.name}</td>
                        <td>${message.contact || '未提供'}</td>
                        <td>${truncateText(message.content, 50)}</td>
                        <td>${formatDate(message.create_time)}</td>
                        <td>
                            ${message.reply ? 
                                '<span class="badge bg-success">已回复</span>' : 
                                '<span class="badge bg-warning">待回复</span>'
                            }
                        </td>
                        <td class="table-actions">
                            <button class="btn btn-sm btn-outline-info" onclick="viewMessage(${message.id})">
                                <i class="fas fa-eye"></i>
                            </button>
                            ${!message.reply ? 
                                `<button class="btn btn-sm btn-outline-primary" onclick="replyMessage(${message.id})">
                                    <i class="fas fa-reply"></i>
                                </button>` : ''
                            }
                        </td>
                    </tr>
                `).join('');
                tbody.innerHTML = messagesHtml;
            } else {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无数据</td></tr>';
            }
        })
        .catch(error => {
            console.error('加载留言失败:', error);
        });
}

function viewMessage(messageId) {
    fetch(`/admin/messages`)
        .then(response => response.json())
        .then(data => {
            const message = data.find(m => m.id === messageId);
            if (message) {
                const modalHtml = `
                    <div class="modal fade" id="messageViewModal" tabindex="-1">
                        <div class="modal-dialog modal-lg">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">查看留言</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="mb-3">
                                        <strong>姓名：</strong>${message.name}
                                    </div>
                                    <div class="mb-3">
                                        <strong>联系方式：</strong>${message.contact || '未提供'}
                                    </div>
                                    <div class="mb-3">
                                        <strong>留言时间：</strong>${formatDate(message.create_time)}
                                    </div>
                                    <div class="mb-3">
                                        <strong>留言内容：</strong>
                                        <div class="border p-2 mt-1">${message.content}</div>
                                    </div>
                                    ${message.reply ? `
                                        <div class="mb-3">
                                            <strong>回复内容：</strong>
                                            <div class="border p-2 mt-1 bg-light">${message.reply}</div>
                                        </div>
                                    ` : ''}
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                                    ${!message.reply ? 
                                        `<button type="button" class="btn btn-primary" onclick="replyMessage(${messageId})">回复</button>` : ''
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                document.getElementById('modal-container').innerHTML = modalHtml;
                const modal = new bootstrap.Modal(document.getElementById('messageViewModal'));
                modal.show();
            }
        })
        .catch(error => {
            console.error('加载留言详情失败:', error);
        });
}

function replyMessage(messageId) {
    const modalHtml = `
        <div class="modal fade" id="replyModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">回复留言</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="replyForm">
                            <div class="form-group">
                                <label for="replyContent">回复内容</label>
                                <textarea class="form-control" id="replyContent" rows="5" required></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="saveReply(${messageId})">发送回复</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('modal-container').innerHTML = modalHtml;
    const modal = new bootstrap.Modal(document.getElementById('replyModal'));
    modal.show();
}

function saveReply(messageId) {
    const reply = document.getElementById('replyContent').value;
    
    if (!reply) {
        alert('请填写回复内容');
        return;
    }
    
    fetch(`/admin/messages/${messageId}/reply`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reply: reply })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.msg);
        bootstrap.Modal.getInstance(document.getElementById('replyModal')).hide();
        loadMessages();
    })
    .catch(error => {
        console.error('回复失败:', error);
        alert('回复失败');
    });
}

// 服务管理功能
function loadServices() {
    fetch('/admin/services')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('services-table-body');
            if (data.length > 0) {
                const servicesHtml = data.map(service => `
                    <tr>
                        <td>${service.id}</td>
                        <td>${service.name}</td>
                        <td>${truncateText(service.description || '', 50)}</td>
                        <td>${service.file_url ? `<a href="${service.file_url}" target="_blank">查看文件</a>` : '无'}</td>
                        <td class="table-actions">
                            <button class="btn btn-sm btn-outline-primary" onclick="editService(${service.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteService(${service.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
                tbody.innerHTML = servicesHtml;
            } else {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">暂无数据</td></tr>';
            }
        })
        .catch(error => {
            console.error('加载服务失败:', error);
        });
}

function showServiceModal(serviceId = null) {
    const isEdit = serviceId !== null;
    const title = isEdit ? '编辑服务' : '添加服务';
    
    const modalHtml = `
        <div class="modal fade" id="serviceModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="serviceForm">
                            <div class="form-group">
                                <label for="serviceName">服务名称</label>
                                <input type="text" class="form-control" id="serviceName" required>
                            </div>
                            <div class="form-group">
                                <label for="serviceDescription">服务描述</label>
                                <textarea class="form-control" id="serviceDescription" rows="5"></textarea>
                            </div>
                            <div class="form-group">
                                <label for="serviceFile">服务文件</label>
                                <input type="file" class="form-control" id="serviceFile">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="saveService(${serviceId})">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('modal-container').innerHTML = modalHtml;
    
    if (isEdit) {
        loadServiceData(serviceId);
    }
    
    const modal = new bootstrap.Modal(document.getElementById('serviceModal'));
    modal.show();
}

function saveService(serviceId) {
    const name = document.getElementById('serviceName').value;
    const description = document.getElementById('serviceDescription').value;
    
    if (!name) {
        alert('请填写服务名称');
        return;
    }
    
    const serviceData = {
        name: name,
        description: description,
        file_url: '' // 这里可以扩展文件上传功能
    };
    
    const url = serviceId ? `/admin/services/${serviceId}` : '/admin/services';
    const method = serviceId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(serviceData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.msg);
        bootstrap.Modal.getInstance(document.getElementById('serviceModal')).hide();
        loadServices();
    })
    .catch(error => {
        console.error('保存服务失败:', error);
        alert('保存失败');
    });
}

function editService(serviceId) {
    showServiceModal(serviceId);
}

function deleteService(serviceId) {
    if (confirm('确定要删除这个服务吗？')) {
        fetch(`/admin/services/${serviceId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.msg);
            loadServices();
        })
        .catch(error => {
            console.error('删除服务失败:', error);
        });
    }
}

// 政务管理功能
function loadGovernment() {
    fetch('/admin/government')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('government-table-body');
            if (data.length > 0) {
                const governmentHtml = data.map(gov => `
                    <tr>
                        <td>${gov.id}</td>
                        <td>${gov.title}</td>
                        <td>${truncateText(gov.content || '', 50)}</td>
                        <td>${gov.file_url ? `<a href="${gov.file_url}" target="_blank">查看文件</a>` : '无'}</td>
                        <td>${formatDate(gov.create_time)}</td>
                        <td class="table-actions">
                            <button class="btn btn-sm btn-outline-primary" onclick="editGovernment(${gov.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteGovernment(${gov.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
                tbody.innerHTML = governmentHtml;
            } else {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">暂无数据</td></tr>';
            }
        })
        .catch(error => {
            console.error('加载政务信息失败:', error);
        });
}

function showGovernmentModal(govId = null) {
    const isEdit = govId !== null;
    const title = isEdit ? '编辑政务信息' : '添加政务信息';
    
    const modalHtml = `
        <div class="modal fade" id="governmentModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="governmentForm">
                            <div class="form-group">
                                <label for="governmentTitle">标题</label>
                                <input type="text" class="form-control" id="governmentTitle" required>
                            </div>
                            <div class="form-group">
                                <label for="governmentContent">内容</label>
                                <textarea class="form-control" id="governmentContent" rows="8"></textarea>
                            </div>
                            <div class="form-group">
                                <label for="governmentFile">相关文件</label>
                                <input type="file" class="form-control" id="governmentFile">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="saveGovernment(${govId})">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('modal-container').innerHTML = modalHtml;
    
    if (isEdit) {
        loadGovernmentData(govId);
    }
    
    const modal = new bootstrap.Modal(document.getElementById('governmentModal'));
    modal.show();
}

function saveGovernment(govId) {
    const title = document.getElementById('governmentTitle').value;
    const content = document.getElementById('governmentContent').value;
    
    if (!title) {
        alert('请填写标题');
        return;
    }
    
    const govData = {
        title: title,
        content: content,
        file_url: '' // 这里可以扩展文件上传功能
    };
    
    const url = govId ? `/admin/government/${govId}` : '/admin/government';
    const method = govId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(govData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.msg);
        bootstrap.Modal.getInstance(document.getElementById('governmentModal')).hide();
        loadGovernment();
    })
    .catch(error => {
        console.error('保存政务信息失败:', error);
        alert('保存失败');
    });
}

function editGovernment(govId) {
    showGovernmentModal(govId);
}

function deleteGovernment(govId) {
    if (confirm('确定要删除这条政务信息吗？')) {
        fetch(`/admin/government/${govId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.msg);
            loadGovernment();
        })
        .catch(error => {
            console.error('删除政务信息失败:', error);
        });
    }
}

// 乡村概况管理功能
function loadVillage() {
    fetch('/admin/village')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('village-table-body');
            if (data.length > 0) {
                const villageHtml = data.map(village => `
                    <tr>
                        <td>${village.id}</td>
                        <td>${village.title}</td>
                        <td>${truncateText(village.content, 50)}</td>
                        <td>${village.image_url ? `<a href="${village.image_url}" target="_blank">查看图片</a>` : '无'}</td>
                        <td class="table-actions">
                            <button class="btn btn-sm btn-outline-primary" onclick="editVillage(${village.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteVillage(${village.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
                tbody.innerHTML = villageHtml;
            } else {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">暂无数据</td></tr>';
            }
        })
        .catch(error => {
            console.error('加载乡村概况失败:', error);
        });
}

function showVillageModal(villageId = null) {
    const isEdit = villageId !== null;
    const title = isEdit ? '编辑乡村概况' : '添加乡村概况';
    
    const modalHtml = `
        <div class="modal fade" id="villageModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="villageForm">
                            <div class="form-group">
                                <label for="villageTitle">标题</label>
                                <input type="text" class="form-control" id="villageTitle" required>
                            </div>
                            <div class="form-group">
                                <label for="villageContent">内容</label>
                                <textarea class="form-control" id="villageContent" rows="10" required></textarea>
                            </div>
                            <div class="form-group">
                                <label for="villageImage">图片</label>
                                <input type="file" class="form-control" id="villageImage" accept="image/*">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="saveVillage(${villageId})">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('modal-container').innerHTML = modalHtml;
    
    if (isEdit) {
        loadVillageData(villageId);
    }
    
    const modal = new bootstrap.Modal(document.getElementById('villageModal'));
    modal.show();
}

function saveVillage(villageId) {
    const title = document.getElementById('villageTitle').value;
    const content = document.getElementById('villageContent').value;
    
    if (!title || !content) {
        alert('请填写标题和内容');
        return;
    }
    
    const villageData = {
        title: title,
        content: content,
        image_url: '' // 这里可以扩展图片上传功能
    };
    
    const url = villageId ? `/admin/village/${villageId}` : '/admin/village';
    const method = villageId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(villageData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.msg);
        bootstrap.Modal.getInstance(document.getElementById('villageModal')).hide();
        loadVillage();
    })
    .catch(error => {
        console.error('保存乡村概况失败:', error);
        alert('保存失败');
    });
}

function editVillage(villageId) {
    showVillageModal(villageId);
}

function deleteVillage(villageId) {
    if (confirm('确定要删除这条乡村概况吗？')) {
        fetch(`/admin/village/${villageId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.msg);
            loadVillage();
        })
        .catch(error => {
            console.error('删除乡村概况失败:', error);
        });
    }
}

// 用户管理功能
function loadUsers() {
    fetch('/admin/users')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('users-table-body');
            if (data.length > 0) {
                const usersHtml = data.map(user => `
                    <tr>
                        <td>${user.id}</td>
                        <td>${user.username}</td>
                        <td>
                            <span class="badge ${user.role === 'admin' ? 'bg-danger' : 'bg-secondary'}">
                                ${user.role === 'admin' ? '管理员' : '普通用户'}
                            </span>
                        </td>
                        <td>${formatDate(user.create_time)}</td>
                    </tr>
                `).join('');
                tbody.innerHTML = usersHtml;
            } else {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center">暂无数据</td></tr>';
            }
        })
        .catch(error => {
            console.error('加载用户失败:', error);
        });
}

// 工具函数
function formatDate(dateString) {
    if (!dateString) return '未知';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function updatePagination(containerId, pagination, loadFunction) {
    const container = document.getElementById(containerId);
    if (!container || !pagination) return;
    
    let paginationHtml = '';
    
    // 上一页
    if (pagination.page > 1) {
        paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="${loadFunction.name}(${pagination.page - 1})">上一页</a></li>`;
    }
    
    // 页码
    for (let i = 1; i <= pagination.pages; i++) {
        const active = i === pagination.page ? 'active' : '';
        paginationHtml += `<li class="page-item ${active}"><a class="page-link" href="#" onclick="${loadFunction.name}(${i})">${i}</a></li>`;
    }
    
    // 下一页
    if (pagination.page < pagination.pages) {
        paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="${loadFunction.name}(${pagination.page + 1})">下一页</a></li>`;
    }
    
    container.innerHTML = paginationHtml;
}

function loadCategoryOptions(selectId) {
    fetch('/api/categories')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById(selectId);
            if (select) {
                let options = '<option value="">请选择分类</option>';
                data.forEach(category => {
                    options += `<option value="${category.id}">${category.name}</option>`;
                });
                select.innerHTML = options;
            }
        })
        .catch(error => {
            console.error('加载分类选项失败:', error);
        });
}

function updateCategoryFilter(categories) {
    const filter = document.getElementById('newsCategoryFilter');
    if (filter) {
        let options = '<option value="">所有分类</option>';
        categories.forEach(category => {
            options += `<option value="${category.id}">${category.name}</option>`;
        });
        filter.innerHTML = options;
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
});