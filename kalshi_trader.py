import os
import sys
import json
import datetime
import requests

# Configuration
TOP_N_MARKETS = 5
BET_CAP = 25.0          # max per bet
DAILY_EXPOSURE_LIMIT = 100.0  # max total exposure per day

# Kalshi API endpoints
# Using a public endpoint for listing events. This might require a read-only API key for some endpoints.
BASE_API = "https://api.elections.kalshi.com/trade-api/v2"

def get_api_key():
    '''Retrieves Kalshi API key from environment variables.'''
    # IMPORTANT: This function WILL ONLY WORK when run in an environment where KALSHI_API_KEY is set.
    # From this environment, I cannot access your local machine's environment variables.
    key = os.environ.get("KALSHI_API_KEY")
    if not key:
        raise ValueError("KALSHI_API_KEY environment variable not set.")
    return key

def fetch_public_weather_markets(api_key):
    '''Fetches public weather markets from Kalshi API.
       Prioritizing public endpoints and will use API key if required for listings.
    '''
    url = f"{BASE_API}/events_list?category=weather&status=open"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # Using a timeout for safety
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        # In case of auth issues or API endpoint changes, provide feedback.
        print(f"Error fetching Kalshi markets: {e}", file=sys.stderr)
        print("Please ensure your API key is valid and the endpoint is accessible.", file=sys.stderr)
        return {"events": []}

def select_top_markets(markets, n=TOP_N_MARKETS):
    '''Selects top N markets based on liquidity.'''
    if not markets or 'events' not in markets:
        return []

    events = markets['events']
    # Sort by liquidity (24h volume) to find active markets.
    # Fallback: if liquidity is not present, sort by event ID or name for consistency.
    sorted_events = sorted(events, key=lambda x: float(x.get('volume_24h', 0)), reverse=True)
    
    return sorted_events[:n]

def simulate_bet(market, stake):
    '''Simulates a bet for demonstration. This does NOT place real trades.
       Calculates a simplified EV proxy.
    '''
    yes_price = float(market.get('yes_price', 0.5)) # Default to 0.5 if missing
    p_yes = yes_price # Implied probability is just the yes price in a clean market
    
    # Naive EV calculation: replace with real edge calculation if needed.
    # This simply shows deviation from a 50/50 odds.
    ev = (p_yes - 0.5) * stake
    
    return {
        "market_id": market.get('id', 'N/A'),
        "event": market.get('name', 'Unknown Market'),
        "stake": stake,
        "yes_price": yes_price,
        "implied_prob_yes": p_yes * 100,
        "ev_per_bet": ev
    }

def main():
    '''Main function to orchestrate fetching, simulation, and reporting.'''
    try:
        api_key = get_api_key()
    except ValueError as e:
        print(f"Setup Error: {e}", file=sys.stderr)
        print("Please ensure the KALSHI_API_KEY environment variable is set.", file=sys.stderr)
        sys.exit(1)

    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Fetching public Kalshi weather markets...")
    markets_data = fetch_public_weather_markets(api_key)
    
    top_markets = select_top_markets(markets_data, TOP_N_MARKETS)
    
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Processing for top {TOP_N_MARKETS} markets...")
    
    if not top_markets:
        print("No weather markets found or API call failed. Please check API key and endpoint.", file=sys.stderr)
        return

    total_exposure_today = 0.0
    placed_bets = []

    for market in top_markets:
        market_id = market.get('id', 'N/A')
        name = market.get('name', 'Unknown Market')
        yes_price = market.get('yes_price', None)
        no_price = market.get('no_price', None)
        liquidity = market.get('volume_24h', 'N/A')
        expiration_date = market.get('expiration_date', 'N/A')

        # Determine stake for this bet, respecting daily limits
        stake = min(BET_CAP, DAILY_EXPOSURE_LIMIT - total_exposure_today)
        if stake <= 0:
            print("Daily exposure limit reached.")
            break
        
        # Simulate the bet
        bet = simulate_bet(market, stake)
        total_exposure_today += stake
        placed_bets.append(bet)

    # Build summary for chat output AND log file
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    summary_lines = [
        f"--- Kalshi Bet Simulation Summary ({date_str}) ---",
        f"Daily Exposure Cap: ${DAILY_EXPOSURE_LIMIT:.2f}",
        f"Max Bet Cap: ${BET_CAP:.2f}",
        "Simulated Bets Placed:"
    ]
    for b in placed_bets:
        summary_lines.append(
            f"- {b['event']} (ID: {b['market_id']}): Stake=${b['stake']:.2f}, Yes Price={b['yes_price']:.3f}, Implied Prob={b['implied_prob_yes']:.1f}%, EV={b['ev_per_bet']:.2f}")
    
    summary_lines.append(f"Total Simulated Exposure Today: ${total_exposure_today:.2f}")
    
    final_summary = "\n".join(summary_lines)
    print(final_summary)

    # Log to file
    log_file_path = os.path.join("C:\\Users\\chead\\.openclaw\\workspace", "kalshi_sim_run.log")
    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(final_summary + "\n\n")
    except IOError as e:
        print(f"Error writing to log file {log_file_path}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
