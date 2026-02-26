<!-- API COST TRACKER WIDGET -->
<div id="api-cost-widget" class="widget api-cost-widget">
  <div class="widget-header">
    <h2>💰 API Cost Tracker</h2>
    <button onclick="refreshCostWidget()" title="Refresh">⟳</button>
  </div>

  <div class="widget-body">
    <!-- Quick Stats -->
    <div class="cost-stats">
      <div class="stat-card">
        <div class="stat-label">Today's Spend</div>
        <div class="stat-value" id="today-spend">$0.00</div>
        <div class="stat-detail" id="today-budget">0% of $5.00</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">This Week</div>
        <div class="stat-value" id="week-spend">$0.00</div>
        <div class="stat-detail" id="week-trend">0% of budget</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Monthly Projection</div>
        <div class="stat-value" id="month-projection">$0.00</div>
        <div class="stat-detail" id="month-status">On track</div>
      </div>
    </div>

    <!-- Progress Bar (Daily) -->
    <div class="cost-progress">
      <label>Daily Budget ($5.00)</label>
      <div class="progress-bar">
        <div class="progress-fill" id="daily-progress-fill" style="width: 0%"></div>
      </div>
      <div class="progress-text">
        <span id="progress-amount">$0.00</span>
        <span id="progress-percent">0%</span>
      </div>
    </div>

    <!-- By Model Breakdown -->
    <div class="cost-breakdown">
      <h3>By Model</h3>
      <table class="breakdown-table">
        <thead>
          <tr>
            <th>Model</th>
            <th>Cost</th>
            <th>Tokens</th>
            <th>% of Total</th>
          </tr>
        </thead>
        <tbody id="model-breakdown">
          <tr><td colspan="4" style="text-align:center">Loading...</td></tr>
        </tbody>
      </table>
    </div>

    <!-- By Agent Breakdown -->
    <div class="cost-breakdown">
      <h3>By Agent</h3>
      <table class="breakdown-table">
        <thead>
          <tr>
            <th>Agent</th>
            <th>Cost</th>
            <th>Tokens</th>
            <th>% of Total</th>
          </tr>
        </thead>
        <tbody id="agent-breakdown">
          <tr><td colspan="4" style="text-align:center">Loading...</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Alerts -->
    <div id="cost-alerts" class="cost-alerts"></div>

    <!-- Last Updated -->
    <div class="widget-footer">
      <small>Last updated: <span id="last-update">Never</span></small>
    </div>
  </div>
</div>

<style>
.api-cost-widget {
  background: #1a1a2e;
  border: 1px solid #16213e;
  border-radius: 8px;
  padding: 20px;
  margin: 10px 0;
  color: #eee;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.widget-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.widget-header button {
  background: #16213e;
  border: 1px solid #0f3460;
  color: #00d4ff;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cost-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  background: #16213e;
  border: 1px solid #0f3460;
  border-radius: 6px;
  padding: 15px;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #aaa;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 22px;
  font-weight: bold;
  color: #00ff00;
  margin-bottom: 5px;
}

.stat-value.warning {
  color: #ffaa00;
}

.stat-value.danger {
  color: #ff4444;
}

.stat-detail {
  font-size: 11px;
  color: #777;
}

.cost-progress {
  margin: 20px 0;
}

.cost-progress label {
  display: block;
  font-size: 12px;
  color: #aaa;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.progress-bar {
  height: 24px;
  background: #0f3460;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
  border: 1px solid #16213e;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00ff00 0%, #00ff00 50%, #ffaa00 75%, #ff4444 100%);
  transition: width 0.3s ease;
}

.progress-text {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #aaa;
}

.cost-breakdown {
  margin: 20px 0;
}

.cost-breakdown h3 {
  font-size: 13px;
  color: #00d4ff;
  margin: 10px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.breakdown-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.breakdown-table thead {
  background: #16213e;
  border-bottom: 1px solid #0f3460;
}

.breakdown-table th {
  padding: 8px;
  text-align: left;
  color: #aaa;
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.breakdown-table td {
  padding: 8px;
  border-bottom: 1px solid #16213e;
  color: #ddd;
}

.breakdown-table tbody tr:hover {
  background: #0f3460;
}

.cost-alerts {
  margin: 15px 0;
  padding: 10px;
  background: #16213e;
  border-radius: 4px;
  border-left: 3px solid #ffaa00;
  color: #ffaa00;
  font-size: 12px;
}

.cost-alerts.danger {
  border-left-color: #ff4444;
  color: #ff4444;
}

.widget-footer {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #16213e;
  font-size: 11px;
  color: #aaa;
}
</style>

<script>
async function refreshCostWidget() {
  try {
    const response = await fetch('/api/usage/anthropic?days=1');
    const data = await response.json();

    if (!response.ok) {
      console.error('[COST WIDGET] Error:', data);
      return;
    }

    // Update quick stats
    const todaySpend = data.total?.total_cost || 0;
    const todayBudget = 5.00;
    const budgetPercent = ((todaySpend / todayBudget) * 100).toFixed(1);

    document.getElementById('today-spend').textContent = `$${todaySpend.toFixed(2)}`;
    document.getElementById('today-budget').textContent = `${budgetPercent}% of $${todayBudget.toFixed(2)}`;

    // Update progress bar
    const progressPercent = Math.min(100, budgetPercent);
    document.getElementById('daily-progress-fill').style.width = `${progressPercent}%`;
    document.getElementById('progress-amount').textContent = `$${todaySpend.toFixed(2)}`;
    document.getElementById('progress-percent').textContent = `${budgetPercent}%`;

    // Color coding
    const statValue = document.getElementById('today-spend').parentElement;
    statValue.classList.remove('warning', 'danger');
    if (budgetPercent > 80) {
      statValue.classList.add('danger');
    } else if (budgetPercent > 60) {
      statValue.classList.add('warning');
    }

    // By model breakdown
    const modelBody = document.getElementById('model-breakdown');
    if (data.by_model && data.by_model.length > 0) {
      const totalCost = data.total?.total_cost || 0;
      modelBody.innerHTML = data.by_model.map(m => {
        const pct = totalCost > 0 ? ((m.total_cost / totalCost) * 100).toFixed(1) : 0;
        return `
          <tr>
            <td>${m.model.replace('claude-', '')}</td>
            <td>$${(m.total_cost || 0).toFixed(2)}</td>
            <td>${m.total_tokens || 0}</td>
            <td>${pct}%</td>
          </tr>
        `;
      }).join('');
    }

    // By agent breakdown
    const agentBody = document.getElementById('agent-breakdown');
    if (data.by_agent && data.by_agent.length > 0) {
      const totalCost = data.total?.total_cost || 0;
      agentBody.innerHTML = data.by_agent.map(a => {
        const pct = totalCost > 0 ? ((a.total_cost / totalCost) * 100).toFixed(1) : 0;
        return `
          <tr>
            <td>${a.agent_id || 'unknown'}</td>
            <td>$${(a.total_cost || 0).toFixed(2)}</td>
            <td>${a.total_tokens || 0}</td>
            <td>${pct}%</td>
          </tr>
        `;
      }).join('');
    }

    // Alerts
    const alertsDiv = document.getElementById('cost-alerts');
    alertsDiv.innerHTML = '';
    if (budgetPercent > 100) {
      alertsDiv.classList.add('danger');
      alertsDiv.textContent = `⚠️ Daily budget exceeded! $${(todaySpend - todayBudget).toFixed(2)} over.`;
    } else if (budgetPercent > 80) {
      alertsDiv.classList.remove('danger');
      alertsDiv.textContent = `⚠️ Approaching daily budget. ${(100 - budgetPercent).toFixed(1)}% remaining.`;
    }

    // Last update
    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();

    // Weekly projection
    const weeklyResponse = await fetch('/api/usage/summary?days=7');
    const weeklyData = await weeklyResponse.json();
    const weeklySpend = weeklyData.grand_total?.total_cost || 0;
    const monthlyProjection = (weeklySpend / 7) * 30;
    document.getElementById('week-spend').textContent = `$${weeklySpend.toFixed(2)}`;
    document.getElementById('month-projection').textContent = `$${monthlyProjection.toFixed(2)}`;
    
    const budgetStatus = monthlyProjection > 150 ? '🔴 OVER' : '🟢 ON TRACK';
    document.getElementById('month-status').textContent = budgetStatus;
  } catch (err) {
    console.error('[COST WIDGET] Error:', err);
  }
}

// Auto-refresh every 5 minutes
document.addEventListener('DOMContentLoaded', () => {
  refreshCostWidget();
  setInterval(refreshCostWidget, 300000);
});
</script>
