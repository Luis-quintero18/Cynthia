from flask import Flask, request, render_template, jsonify
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import io
import base64

app = Flask(__name__)

# Load the dataset and preprocess it as before
DATA_PATH = 'C:/Users/lquin/PycharmProjects/Cynthia Blockchain/data/data2.csv'
data = pd.read_csv(DATA_PATH)
data['Value_OUT(ETH)'] = pd.to_numeric(data['Value_OUT(ETH)'], errors='coerce')
transaction_data = data[['From', 'To', 'Value_OUT(ETH)', 'DateTime (UTC)']].dropna()

# Build network graph
G = nx.DiGraph()
for _, row in transaction_data.iterrows():
    sender, receiver, value = row['From'], row['To'], row['Value_OUT(ETH)']
    if G.has_edge(sender, receiver):
        G[sender][receiver]['weight'] += value
    else:
        G.add_edge(sender, receiver, weight=value)

# Helper functions for advanced analytics
def calculate_analytics(wallet_address):
    # Filter transactions for the given wallet
    outgoing = transaction_data[transaction_data['From'] == wallet_address]
    incoming = transaction_data[transaction_data['To'] == wallet_address]

    # Transaction Summary
    num_outgoing = len(outgoing)
    num_incoming = len(incoming)
    avg_outgoing_value = outgoing['Value_OUT(ETH)'].mean() if not outgoing.empty else 0
    avg_incoming_value = incoming['Value_OUT(ETH)'].mean() if not incoming.empty else 0
    largest_transaction = max(outgoing['Value_OUT(ETH)'].max(), incoming['Value_OUT(ETH)'].max(), 0)

    # Network Metrics
    degree_centrality = nx.degree_centrality(G).get(wallet_address, 0)
    betweenness_centrality = nx.betweenness_centrality(G).get(wallet_address, 0)
    pagerank = nx.pagerank(G).get(wallet_address, 0)

    # Top Counterparties
    top_counterparties = outgoing.groupby('To')['Value_OUT(ETH)'].sum().nlargest(5).reset_index()

    return {
        'num_outgoing': num_outgoing,
        'num_incoming': num_incoming,
        'avg_outgoing_value': avg_outgoing_value,
        'avg_incoming_value': avg_incoming_value,
        'largest_transaction': largest_transaction,
        'degree_centrality': degree_centrality,
        'betweenness_centrality': betweenness_centrality,
        'pagerank': pagerank,
        'top_counterparties': top_counterparties.to_dict(orient='records')
    }

def plot_transaction_trends(wallet_address):
    # Filter transactions
    wallet_data = transaction_data[
        (transaction_data['From'] == wallet_address) | (transaction_data['To'] == wallet_address)
    ]

    if wallet_data.empty:
        return None

    # Group by date and sum transaction values
    wallet_data['DateTime (UTC)'] = pd.to_datetime(wallet_data['DateTime (UTC)'])
    wallet_data.set_index('DateTime (UTC)', inplace=True)
    trend = wallet_data.resample('D')['Value_OUT(ETH)'].sum().fillna(0)

    # Plot the trends
    fig, ax = plt.subplots(figsize=(10, 6))
    trend.plot(ax=ax, color='blue', label='Daily Transaction Volume')
    ax.set_title('Transaction Volume Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('ETH Volume')
    ax.legend()

    # Convert plot to image
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)
    return img_base64

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analytics', methods=['POST'])
def analytics():
    wallet_address = request.form['wallet_address'].strip().lower()
    if wallet_address not in G.nodes:
        return jsonify({'error': 'Wallet address not found'}), 404

    # Calculate analytics
    analytics_data = calculate_analytics(wallet_address)
    trend_plot = plot_transaction_trends(wallet_address)

    return jsonify({'analytics': analytics_data, 'trend_plot': trend_plot})

if __name__ == '__main__':
    app.run(debug=True)
