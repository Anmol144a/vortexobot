<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>💫 Vortex Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
body { background: #0f0f1a; color: #fff; font-family: 'Inter', sans-serif; }
.card { background: #1a1a2e; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #333; }
th { font-weight: bold; }
a { color: #4f46e5; text-decoration: none; }
a:hover { text-decoration: underline; }
</style>
</head>
<body class="p-6">
<div class="max-w-6xl mx-auto">
    <h1 class="text-4xl font-bold mb-6">💫 Vortex Dashboard • Made by Anmol</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Wallets -->
        <div class="card">
            <h2 class="text-xl font-semibold mb-4">Wallets Tracked</h2>
            {% if wallets %}
            <table>
                <thead>
                    <tr><th>User</th><th>Label</th><th>Address</th><th>Last Balance</th></tr>
                </thead>
                <tbody>
                    {% for w in wallets %}
                    <tr>
                        <td>{{ w['user_id'] }}</td>
                        <td>{{ w['label'] }}</td>
                        <td>{{ w['address'] }}</td>
                        <td>{{ w['last_balance'] or "0" }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p>No wallets tracked yet.</p>
            {% endif %}
        </div>

        <!-- Transactions -->
        <div class="card">
            <h2 class="text-xl font-semibold mb-4">Recent Transactions</h2>
            {% if txs %}
            <table>
                <thead>
                    <tr><th>TxID</th><th>Address</th><th>Amount</th><th>Time</th></tr>
                </thead>
                <tbody>
                    {% for tx in txs %}
                    <tr>
                        <td>
                            <a href="https://blockchair.com/litecoin/transaction/{{ tx['txid'] }}" target="_blank">
                                {{ tx['txid'][:10] }}...
                            </a>
                        </td>
                        <td>{{ tx['address'] }}</td>
                        <td>{{ tx['amount'] }}</td>
                        <td>{{ tx['timestamp'] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p>No recent transactions yet.</p>
            {% endif %}
        </div>
    </div>
</div>
</body>
</html>
