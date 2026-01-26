dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Assignment API Dashboard</title>
    <style>
        :root {
            --primary-color: #2563eb;
            --secondary-color: #475569;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --success-color: #22c55e;
            --border-color: #e2e8f0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--background-color);
            margin: 0;
            padding: 20px;
            color: #1e293b;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 1.5rem;
            color: #0f172a;
            margin: 0;
        }

        .status-badge {
            background-color: #dcfce7;
            color: #166534;
            padding: 6px 12px;
            border-radius: 9999px;
            font-weight: 500;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: #22c55e;
            border-radius: 50%;
            display: inline-block;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: var(--card-background);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color);
        }

        .card-title {
            color: var(--secondary-color);
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #0f172a;
        }

        .message-list {
            margin-top: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            text-align: left;
            padding: 12px;
            color: var(--secondary-color);
            font-weight: 600;
            border-bottom: 2px solid var(--border-color);
        }

        td {
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
        }

        tr:last-child td {
            border-bottom: none;
        }

        .refresh-btn {
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: background-color 0.2s;
        }

        .refresh-btn:hover {
            background-color: #1d4ed8;
        }
        
        pre {
            background: #f1f5f9;
            padding: 8px;
            border-radius: 6px;
            margin: 0;
            font-size: 0.85rem;
            white-space: pre-wrap;
            word-break: break-all;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>API Dashboard</h1>
                <p style="color: var(--secondary-color); margin-top: 4px;">Monitor your application status and messages</p>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <button class="refresh-btn" onclick="fetchData()">Refresh Data</button>
                <div class="status-badge">
                    <span class="status-dot"></span>
                    Online
                </div>
            </div>
        </header>

        <div class="grid">
            <div class="card">
                <div class="card-title">Total Messages</div>
                <div class="stat-value" id="total-messages">-</div>
            </div>
            <div class="card">
                <div class="card-title">Average Message Length</div>
                <div class="stat-value" id="avg-len">-</div>
            </div>
            <div class="card">
                <div class="card-title">Top Domain</div>
                <div class="stat-value" id="top-domain">-</div>
                <div style="font-size: 0.875rem; color: var(--secondary-color); margin-top: 4px;" id="top-domain-count"></div>
            </div>
        </div>

        <div class="card">
            <div class="card-title" style="margin-bottom: 20px;">Recent Messages</div>
            <div style="overflow-x: auto;">
                <table id="messages-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Sender</th>
                            <th>Content</th>
                            <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody id="messages-body">
                        <tr><td colspan="4" style="text-align: center; color: var(--secondary-color);">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        async function fetchStats() {
            try {
                const response = await fetch('/stats');
                const data = await response.json();
                
                document.getElementById('total-messages').textContent = data.total_messages || 0;
                document.getElementById('avg-len').textContent = Math.round(data.avg_message_length || 0);
                
                if (data.top_email_domains && data.top_email_domains.length > 0) {
                    const top = data.top_email_domains[0];
                    document.getElementById('top-domain').textContent = top._id;
                    document.getElementById('top-domain-count').textContent = `${top.count} emails`;
                } else {
                    document.getElementById('top-domain').textContent = '-';
                    document.getElementById('top-domain-count').textContent = '';
                }
            } catch (error) {
                console.error('Error fetching stats:', error);
            }
        }

        async function fetchMessages() {
            try {
                const response = await fetch('/messages?limit=10');
                const result = await response.json();
                const messages = result.data;
                const tbody = document.getElementById('messages-body');
                
                tbody.innerHTML = '';
                
                if (messages.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 20px;">No messages found</td></tr>';
                    return;
                }

                messages.forEach(msg => {
                    const row = document.createElement('tr');
                    const date = new Date(msg.timestamp * 1000).toLocaleString();
                    row.innerHTML = `
                        <td style="font-family: monospace; font-size: 0.85rem;">${msg.message_id.substring(0, 8)}...</td>
                        <td>${msg.sender_email}</td>
                        <td><pre>${msg.content}</pre></td>
                        <td style="font-size: 0.85rem; color: var(--secondary-color);">${date}</td>
                    `;
                    tbody.appendChild(row);
                });
            } catch (error) {
                console.error('Error fetching messages:', error);
                document.getElementById('messages-body').innerHTML = 
                    '<tr><td colspan="4" style="text-align: center; color: red;">Error loading messages</td></tr>';
            }
        }

        function fetchData() {
            fetchStats();
            fetchMessages();
        }

        // Initial load
        document.addEventListener('DOMContentLoaded', fetchData);
        
        // Auto refresh every 30 seconds
        setInterval(fetchData, 30000);
    </script>
</body>
</html>
"""
