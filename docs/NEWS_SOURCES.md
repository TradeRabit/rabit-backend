# News Sources Configuration

## Overview

SearXNG dikonfigurasi dengan **40 news sources** (20 general + 20 crypto) untuk comprehensive news coverage.

## General News Media (Top 20)

| No | Media | Shortcut | URL | Focus |
|----|-------|----------|-----|-------|
| 1 | BBC | `bbc` | bbc.com | International news |
| 2 | CNN | `cnn` | cnn.com | US & world news |
| 3 | New York Times | `nyt` | nytimes.com | In-depth journalism |
| 4 | Al Jazeera | `aj` | aljazeera.com | Middle East & world |
| 5 | Reuters | `rt` | reuters.com | Breaking news |
| 6 | Associated Press | `ap` | apnews.com | Wire service |
| 7 | The Guardian | `gd` | theguardian.com | UK & world news |
| 8 | Bloomberg | `bb` | bloomberg.com | Business & finance |
| 9 | CNBC | `cnbc` | cnbc.com | Business news |
| 10 | Fox News | `fox` | foxnews.com | US news |
| 11 | NHK | - | nhk.or.jp | Japan news |
| 12 | Deutsche Welle | - | dw.com | German news |
| 13 | France 24 | - | france24.com | French news |
| 14 | Washington Post | - | washingtonpost.com | US politics |
| 15 | Wall Street Journal | - | wsj.com | Business |
| 16 | USA Today | - | usatoday.com | US news |
| 17 | Sky News | - | news.sky.com | UK news |
| 18 | Times of India | - | timesofindia.com | India news |
| 19 | South China Morning Post | - | scmp.com | Asia news |
| 20 | El País | - | elpais.com | Spanish news |

## Crypto News Media (Top 20)

| No | Media | Shortcut | URL | Focus |
|----|-------|----------|-----|-------|
| 1 | CoinDesk | `cd` | coindesk.com | Crypto news leader |
| 2 | Cointelegraph | `ct` | cointelegraph.com | Blockchain news |
| 3 | CryptoSlate | `cs` | cryptoslate.com | Crypto analysis |
| 4 | The Block | `tb` | theblock.co | Research & news |
| 5 | Decrypt | `dc` | decrypt.co | Web3 news |
| 6 | Bitcoin Magazine | `btcmag` | bitcoinmagazine.com | Bitcoin focus |
| 7 | NewsBTC | `nbtc` | newsbtc.com | Crypto news |
| 8 | CryptoPotato | `cp` | cryptopotato.com | Market news |
| 9 | BeInCrypto | `bic` | beincrypto.com | Crypto news |
| 10 | U.Today | `ut` | u.today | Crypto updates |
| 11 | AMB Crypto | `amb` | ambcrypto.com | Analysis |
| 12 | Crypto Briefing | `cb` | cryptobriefing.com | Research |
| 13 | CoinJournal | - | coinjournal.net | Crypto news |
| 14 | Crypto News | - | cryptonews.com | Daily news |
| 15 | Blockworks | `bw` | blockworks.co | Institutional |
| 16 | CoinGape | - | coingape.com | Market news |
| 17 | CryptoRank | - | cryptorank.io | Data & news |
| 18 | Bitcoinist | `btcn` | bitcoinist.com | Bitcoin news |
| 19 | Crypto Daily | - | cryptodaily.co.uk | Daily updates |
| 20 | The Crypto Times | - | cryptotimes.io | Crypto news |

## Usage

### Search Specific Source

```python
# Search CoinDesk only
results = await client.search("Bitcoin !cd")

# Search CNN only
results = await client.search("market news !cnn")

# Search multiple crypto sources
results = await client.search("Ethereum !cd !ct !cs")
```

### Search All News

```python
# General news
results = await client.search_news("Bitcoin regulation")

# Crypto news (auto-filtered)
results = await client.search_crypto("Solana DeFi")
```

### Agent Usage

```python
# Agent automatically searches relevant sources
agent = TradingAgent(scope_id="global")

# User asks
response = await agent.process_trading_query(
    "What's the latest Bitcoin news?"
)

# Agent searches: CoinDesk, Cointelegraph, CryptoSlate, etc.
```

## Configuration

### Enable/Disable Sources

Edit `searxng/settings.yml`:

```yaml
# Disable a source
- name: foxnews
  disabled: true

# Enable a source
- name: coindesk
  disabled: false
```

### Add Custom Source

```yaml
- name: custom_news
  engine: xpath
  search_url: https://example.com/search?q={query}
  url_xpath: //article//a/@href
  title_xpath: //article//h2/text()
  content_xpath: //article//p/text()
  shortcut: cn
  categories: [news]
  disabled: false
```

## Search Strategies

### 1. Broad Search (All Sources)

```python
results = await client.search("Bitcoin price prediction")
# Searches all 40 sources
```

### 2. Crypto-Focused

```python
results = await client.search_crypto("Ethereum upgrade")
# Prioritizes crypto sources
```

### 3. Specific Source

```python
results = await client.search("Bitcoin !cd")
# Only CoinDesk
```

### 4. Multiple Sources

```python
results = await client.search("Solana !cd !ct !tb")
# CoinDesk + Cointelegraph + The Block
```

## Quality Ranking

### Tier 1 (Most Reliable)

**General:**
- Reuters
- Associated Press
- Bloomberg
- BBC

**Crypto:**
- CoinDesk
- The Block
- Cointelegraph
- Decrypt

### Tier 2 (Reliable)

**General:**
- CNN
- CNBC
- The Guardian
- New York Times

**Crypto:**
- CryptoSlate
- Bitcoin Magazine
- Blockworks
- Crypto Briefing

### Tier 3 (Good)

**General:**
- Fox News
- Al Jazeera
- Washington Post

**Crypto:**
- NewsBTC
- CryptoPotato
- BeInCrypto
- AMB Crypto

## Response Time

| Source Type | Avg Response | Notes |
|-------------|--------------|-------|
| Search engines | < 1s | Google, Bing, DuckDuckGo |
| Major news | 1-2s | BBC, CNN, Reuters |
| Crypto news | 1-3s | CoinDesk, Cointelegraph |
| Smaller sites | 2-4s | May be slower |

## Troubleshooting

### Source Not Working

```bash
# Test specific source
curl "http://localhost:8888/search?q=test&engines=coindesk&format=json"

# Check logs
docker-compose logs searxng | grep coindesk
```

### Slow Responses

```yaml
# Increase timeout in settings.yml
outgoing:
  request_timeout: 5.0  # Increase from 3.0
  max_request_timeout: 15.0  # Increase from 10.0
```

### XPath Not Working

Some sites may change their HTML structure. Update XPath in `settings.yml`:

```yaml
- name: coindesk
  url_xpath: //article//a/@href  # Update if changed
  title_xpath: //article//h6/text()  # Update if changed
```

## Summary

✅ **40 News Sources** - 20 general + 20 crypto
✅ **Comprehensive Coverage** - Major news outlets
✅ **Crypto-Focused** - Top crypto news sites
✅ **Flexible Search** - All sources or specific
✅ **Quality Ranked** - Tier 1, 2, 3 sources
✅ **Fast** - 1-3s average response

**Perfect for:**
- Market news monitoring
- Crypto research
- Trading signals
- Sentiment analysis
- General information

---

**Last Updated:** 2026-04-14
**Version:** 1.0.0
**Status:** ✅ Production Ready
