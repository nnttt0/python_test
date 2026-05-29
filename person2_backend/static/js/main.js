let currentData = null;
let currentFileContent = null;

// 切换标签
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.card').forEach(card => card.classList.remove('active'));

    if (tab === 'single') {
        document.querySelectorAll('.tab-btn')[0].classList.add('active');
        document.getElementById('singleCard').classList.add('active');
    } else {
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
        document.getElementById('batchCard').classList.add('active');
    }
}

// 加载动画
function showLoading(show) {
    document.getElementById('loading').classList.toggle('show', show);
}

// 生成图表
async function generateChart(chartType) {
    if (!currentFileContent) {
        alert('请先进行批量预测');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch('/generate_chart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                chart_type: chartType,
                file_data: currentFileContent
            })
        });
        const data = await response.json();

        if (data.success) {
            const chartContainer = document.getElementById('chartContainer');
            chartContainer.innerHTML = `<img src="data:image/png;base64,${data.image}" style="max-width:100%; border-radius:8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">`;
        } else {
            alert('生成图表失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error);
    }

    showLoading(false);
}

// 绑定图表按钮事件
function bindChartButtons() {
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.removeEventListener('click', btn._listener);
        const chartType = btn.dataset.chart;
        const listener = () => generateChart(chartType);
        btn.addEventListener('click', listener);
        btn._listener = listener;
    });
}

// 单条预测
document.getElementById('predictForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    showLoading(true);

    const formData = new FormData(e.target);

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.success) {
            document.getElementById('predictResult').innerHTML = `
                <div class="risk-card ${data.level}">
                    <h3>评估结果</h3>
                    <div class="risk-percent">${data.risk_percent}%</div>
                    <div class="risk-bar-container">
                        <div class="risk-bar" style="width: ${data.risk_percent}%"></div>
                    </div>
                    <p style="font-weight:500;margin-top:8px;">${data.suggestion}</p>
                    <p style="font-size:13px;margin-top:8px;opacity:0.9;">${data.message}</p>
                </div>
            `;
        } else {
            alert('预测失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error);
    }

    showLoading(false);
});

// 文件上传
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');

uploadArea.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        uploadArea.innerHTML = `
            <p>已选择：${file.name}</p>
            <small>点击重新选择</small>
            <input type="file" id="fileInput" accept=".csv" style="display:none">
        `;
        uploadArea.style.borderColor = '#00B42A';

        // 读取文件内容用于图表生成
        currentFileContent = await file.text();
    }
});

// 批量预测
document.getElementById('batchPredictBtn').addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
        alert('请先选择文件');
        return;
    }

    showLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.success) {
            currentData = data.data;

            document.getElementById('batchResult').innerHTML = `
                <div>
                    <div class="stats">
                        <div class="stat-card">
                            <h3>${data.total}</h3>
                            <p>总人数</p>
                        </div>
                        <div class="stat-card">
                            <h3 style="color:var(--danger)">${data.high_count}</h3>
                            <p>高风险</p>
                        </div>
                        <div class="stat-card">
                            <h3 style="color:var(--warning)">${data.medium_count}</h3>
                            <p>中风险</p>
                        </div>
                        <div class="stat-card">
                            <h3 style="color:var(--success)">${data.low_count}</h3>
                            <p>低风险</p>
                        </div>
                    </div>
                    <div class="table-container">
                        ${data.html_table}
                    </div>
                </div>
            `;

            // 显示可视化区域、导出按钮和聚类分析
            document.getElementById('visualizationSection').style.display = 'block';
            document.getElementById('exportBtn').style.display = 'inline-block';
            document.getElementById('clusterSection').style.display = 'block';

            // 绑定图表按钮
            bindChartButtons();
        } else {
            alert('预测失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error);
    }

    showLoading(false);
});

// 导出结果
document.getElementById('exportBtn').addEventListener('click', async () => {
    if (!currentData) return;
    showLoading(true);

    try {
        const response = await fetch('/export', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(currentData)
        });
        const data = await response.json();

        if (data.success) {
            const blob = new Blob([data.csv_data], {type: 'text/csv;charset=utf-8;'});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = '中风风险预测结果.csv';
            link.click();
            URL.revokeObjectURL(link.href);
        } else {
            alert('导出失败：' + data.error);
        }
    } catch (error) {
        alert('导出失败：' + error);
    }

    showLoading(false);
});

// 页面加载完成后绑定图表按钮
document.addEventListener('DOMContentLoaded', () => {
    bindChartButtons();
});

// 聚类分析
document.getElementById('clusterBtn').addEventListener('click', async () => {
    if (!currentFileContent) {
        alert('请先进行批量预测');
        return;
    }

    const nClusters = parseInt(document.getElementById('nClusters').value);
    showLoading(true);

    try {
        const response = await fetch('/cluster', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                file_data: currentFileContent,
                n_clusters: nClusters
            })
        });
        const data = await response.json();

        if (data.success) {
            const result = data.result;
            let html = `
                <div class="stats">
                    <div class="stat-card">
                        <h3>${result.total}</h3>
                        <p>总样本数</p>
                    </div>
                    <div class="stat-card">
                        <h3>${result.n_clusters}</h3>
                        <p>聚类数量</p>
                    </div>
                </div>
                
                <h4 style="margin-top: 20px;">聚类特征：</h4>
                <p style="color: #666; font-size: 13px; margin: 8px 0;">
                    基于以下数值特征进行聚类：${result.cluster_features.join('、')}
                </p>
                
                <h4 style="margin-top: 20px;">各簇大小：</h4>
                <ul style="list-style: none; padding: 0;">
            `;
            
            for (const [cluster, size] of Object.entries(result.cluster_sizes)) {
                html += `<li style="padding: 8px; margin: 5px 0; background: #f8f9fa; border-radius: 4px;">簇 ${cluster}: ${size} 个样本</li>`;
            }
            
            html += '</ul>';
            
            // 显示簇的特征中心
            if (result.cluster_centers_info) {
                html += '<h4 style="margin-top: 20px;">各簇特征中心：</h4>';
                result.cluster_centers_info.forEach(cluster_info => {
                    html += `<div style="margin: 10px 0; padding: 12px; background: #fff; border: 1px solid #e5e6eb; border-radius: 6px;">`;
                    html += `<strong>簇 ${cluster_info.cluster_id}</strong> (${cluster_info.size} 个样本)<br>`;
                    html += `<small style="color: #666;">`;
                    for (const [feature, value] of Object.entries(cluster_info.center)) {
                        html += `${feature}: ${value}<br>`;
                    }
                    html += `</small></div>`;
                });
            }
            
            // 显示聚类图表
            if (data.image) {
                html += `
                    <div style="margin-top: 20px;">
                        <h4>聚类可视化：</h4>
                        <img src="data:image/png;base64,${data.image}" style="max-width:100%; border-radius:8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-top: 10px;">
                    </div>
                `;
            }
            
            document.getElementById('clusterResult').innerHTML = html;
        } else {
            alert('聚类失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error);
    }

    showLoading(false);
});