# Iron Condor Trading Bot - Project Summary

## Overview

An automated options trading system that executes iron condor strategies on SPX (S&P 500 Index) options using Interactive Brokers API. The bot runs autonomously during market hours, managing position entry, monitoring, and exit with built-in risk management.

## Key Achievements

- **Automated Trading**: Fully autonomous execution of complex 4-leg option spreads
- **Risk Management**: OCO (One-Cancels-Other) stop-loss orders with profit target monitoring
- **High Reliability**: Connection recovery, state persistence, and position reconciliation
- **Real-time Monitoring**: Web dashboard and Telegram notifications
- **Production Ready**: Deployed on cloud infrastructure with systemd service management

## Technical Architecture

### Core Components

1. **Trading Engine** (`src/main.py`)

   - Market hours detection and scheduling
   - Trading cycle orchestration
   - Position monitoring and reconciliation
   - First-trade profit targeting (50% within first hour)

2. **Option Scanner** (`src/strategy/option_scanner.py`)

   - Greeks-based strike selection (delta targeting)
   - Real-time option chain analysis
   - CBOE exchange integration for SPX options

3. **Iron Condor Strategy** (`src/strategy/iron_condor.py`)

   - Multi-leg spread construction
   - Premium balance validation
   - Credit target enforcement ($100-$200 range)
   - Wing width optimization

4. **Order Execution** (`src/execution/order_manager.py`)

   - 4-leg BAG orders with Fill-or-Kill (FOK)
   - Commission calculation
   - Execution verification with 15-second timeout
   - Partial fill prevention

5. **Risk Management** (`src/risk/stop_manager.py`)

   - OCO stop-loss orders (stop-limit + stop-market backup)
   - Profit target monitoring ($0.05 close threshold)
   - Stop order verification after placement
   - Automatic stop cancellation on position close

6. **Position Tracking** (`src/risk/position_tracker.py`)

   - In-memory position state management
   - Orphaned long detection
   - Partial IC tracking
   - Position summary reporting

7. **State Persistence** (`src/utils/error_handling/state_manager.py`)

   - JSON-based state file with atomic writes
   - Position reconciliation with broker
   - Automatic cleanup of old positions
   - Recovery from unexpected restarts

8. **Connection Recovery** (`src/utils/error_handling/recovery.py`)

   - Automatic reconnection with exponential backoff
   - Connection health monitoring
   - Error recovery with state preservation
   - Graceful degradation

9. **Web Dashboard** (`app.py`)

   - Real-time position monitoring
   - PnL tracking
   - Trade history visualization
   - Manual controls (stop/restart bot)

10. **Notifications** (`src/notifications/telegram_bot.py`)
    - Trade execution alerts
    - Stop-loss triggers
    - Daily P&L summaries
    - Error notifications

### Technology Stack

**Backend:**

- Python 3.10+
- ib_insync (Interactive Brokers API wrapper)
- Flask (web framework)
- asyncio (asynchronous I/O)

**Data & State:**

- Lightweight JSON for state persistence
- File-based logging with rotation

**Infrastructure:**

- Linux systemd for process management
- DigitalOcean droplet (cloud hosting)
- Nginx reverse proxy (optional)

**External APIs:**

- Interactive Brokers TWS/Gateway
- Telegram Bot API

## Key Features

### Trading Logic

- **Entry Criteria**: Greeks-based strike selection with configurable parameters
- **Position Sizing**: Configurable contract quantity per trade
- **Max Positions**: Configurable concurrent position limit
- **Credit Targets**: Configurable credit range validation
- **Wing Width**: Adjustable spread width with flexible sizing
- **Premium Balance**: Automated balance validation between spread sides

### Risk Controls

- **Stop Loss**: Configurable stop-loss levels with OCO order structure
- **Profit Target**: Automated profit-taking at configurable thresholds
- **First Trade Rule**: Special profit targeting for initial daily position
- **Expiration Safety**: ITM detection and forced closure near expiration
- **Position Reconciliation**: Periodic broker sync during market hours

### Operational Features

- **Market Hours**: 9:30 AM - 4:00 PM ET, weekdays only
- **Hibernate Mode**: Auto-sleep when market closed
- **State Clearing**: Automatic daily reset at 9:27 AM
- **Graceful Shutdown**: State persistence on exit
- **Error Recovery**: Automatic reconnection and position sync

## Technical Challenges Solved

### 1. Asynchronous API Integration

**Challenge**: Interactive Brokers uses async event-driven API
**Solution**: Implemented ib_insync wrapper with proper event handling and timeouts

### 2. Position State Management

**Challenge**: Maintain accurate position state across restarts and disconnections
**Solution**:

- Atomic JSON state file writes with temp file pattern
- Periodic reconciliation with broker positions
- In-memory tracker sync from persistent state

### 3. Stop Loss Reliability

**Challenge**: Ensure stop orders remain active and correctly priced
**Solution**:

- OCO orders with stop-limit primary and stop-market backup
- Post-placement verification queries
- Automatic cancellation when positions close manually

### 4. Partial Fill Prevention

**Challenge**: Multi-leg orders can partially fill, creating unbalanced risk
**Solution**:

- FOK (Fill-or-Kill) order type for 4-leg BAG orders
- 15-second timeout with automatic cancellation
- Position cleanup on failed execution

### 5. Connection Resilience

**Challenge**: Network/broker disconnections during trading hours
**Solution**:

- Exponential backoff reconnection (1s, 5s, 15s delays)
- Connection check before each trading cycle
- State preservation during disconnection

### 6. Real-time Greeks Calculation

**Challenge**: Options Greeks change throughout the day
**Solution**:

- Live market data requests to CBOE exchange
- Timeout protection (5s max wait per contract)
- Fail-safe validation (no trading without real-time Greeks)

### 7. Timezone Handling

**Challenge**: Market hours in ET, server may be in different timezone
**Solution**:

- pytz library for ET timezone conversion
- All time comparisons in ET
- Holiday calendar integration

### 8. Gateway Access & Security

**Challenge**: Client needs to login to IB Gateway daily while maintaining security and automation
**Solution**:

- VNC server for remote GUI access
- Time-restricted firewall (6-hour morning window before trading)
- IP whitelist + password authentication (3 security layers)
- Automated cron schedule with daylight savings support
- VNC service runs 24/7 to keep Gateway alive
- Firewall blocks access outside window (bot continues trading)

## Code Quality & Best Practices

- **Logging**: Structured logging with loguru (DEBUG/INFO/WARNING/ERROR levels)
- **Error Handling**: Try-catch blocks with recovery logic
- **Configuration**: YAML-based config (not hardcoded)
- **Separation of Concerns**: Modular architecture with clear responsibilities
- **Documentation**: Inline comments, docstrings, and .md summary files
- **Type Hints**: Used throughout codebase (Python 3.10+)
- **Testing**: Integration tests for core components

## Deployment

### Production Environment

- **Platform**: DigitalOcean Droplet (Ubuntu, 2GB RAM)
- **Process Management**: systemd services
- **Auto-restart**: On failure with 10-second delay
- **Logging**: Both file-based and systemd journal
- **Monitoring**: Web UI + Telegram alerts
- **Gateway Access**: VNC with time-restricted firewall access

### Systemd Services

1. `iron-condor-bot.service` - Main trading bot
2. `iron-condor-web.service` - Web dashboard
3. `vncserver@1.service` - IB Gateway GUI access (for daily login)

All configured for automatic startup on boot and restart on failure.

### Remote Access & Security

**Tailscale Private Network** (production implementation):

The system uses **Tailscale** for zero-trust remote access, eliminating public internet exposure:

- **Encrypted mesh VPN**: All traffic encrypted via WireGuard protocol
- **Zero configuration NAT traversal**: Works behind firewalls without port forwarding
- **Multi-device support**: Access from laptop, phone, tablet seamlessly
- **Cross-platform**: Windows, Mac, Linux, iOS, Android clients

**Why Tailscale?**

Traditional VPN setups require complex port forwarding, dynamic DNS, and expose services to the internet. Tailscale provides:

1. **Security by default**: No public IPs, no open ports, no attack surface
2. **Simplicity**: One-time setup, works everywhere automatically
3. **Performance**: Direct peer-to-peer connections when possible
4. **Reliability**: Automatic failover and reconnection

**Access Architecture**:

1. **Web UI (24/7)** - `http://100.x.x.x:8080` (Tailscale IP)
   - Real-time monitoring, configuration changes, log viewing
   - Password-protected, accessible from any Tailscale-connected device
2. **VNC (Time-restricted)** - `100.x.x.x:5901` (Tailscale IP)
   - Remote desktop for IB Gateway login (3:30-9:30 AM ET, weekdays)
   - Time-based firewall + Tailscale IP whitelist
3. **SSH (Advanced)** - `ssh root@100.x.x.x` (Tailscale IP)
   - Direct server access for configuration and troubleshooting

**Security Layers**:

1. **Tailscale mesh network** - Traffic never touches public internet
2. **Time-based firewall rules** - VNC only accessible during trading hours
3. **IP whitelist** - Only approved Tailscale IPs can connect
4. **Password authentication** - VNC and Web UI password-protected
5. **Automated scheduling** - Cron jobs with DST support

**Daily Workflow**:

- Client connects via Tailscale (always on, secure)
- VNC firewall opens automatically at 3:30 AM ET
- Client logs into IB Gateway via VNC desktop
- VNC firewall closes at 9:30 AM ET (bot continues trading)
- Client monitors via Web UI throughout the day (24/7 access)

## Results & Performance

- **Uptime**: Designed for 24/7 operation with automatic market hour detection
- **Reliability**: Connection recovery tested under various failure scenarios
- **Execution Speed**: Orders placed within seconds of signal generation
- **Position Accuracy**: 100% state reconciliation via periodic broker sync

## Future Enhancements (Potential)

1. **Stop Order Persistence**: Save stop order IDs to state file for restart resilience
2. **Position Sizing**: Dynamic contract quantity based on account size
3. **Multi-Symbol Support**: Extend beyond SPX to other indices
4. **Backtesting**: Historical data replay for strategy validation
5. **Advanced Greeks**: Implement vega, theta-based adjustments
6. **Performance Analytics**: Trade metrics and strategy optimization

## Lessons Learned

1. **State Management is Critical**: Persistent state with reconciliation prevents orphaned positions
2. **Broker APIs are Complex**: Async event handling requires careful timeout and error management
3. **Options Trading Nuances**: Greeks, expiration, settlement all need special handling
4. **Reliability > Features**: Connection recovery and state persistence more valuable than advanced features
5. **Observability Matters**: Logging and notifications essential for production confidence

## Skills Demonstrated

- **Python Programming**: Advanced async/await, dataclasses, type hints
- **API Integration**: Complex third-party API (Interactive Brokers)
- **Financial Markets**: Options trading, Greeks, risk management
- **System Design**: Modular architecture, separation of concerns
- **DevOps**: Linux systemd, process management, deployment automation
- **Security**: Multi-layer authentication, firewall management, time-based access control, zero-trust networking
- **Network Engineering**: Tailscale mesh VPN, VNC setup, UFW firewall rules, cron scheduling
- **Modern Networking**: WireGuard protocol, NAT traversal, private mesh networks
- **Error Handling**: Resilient systems with recovery logic
- **Real-time Systems**: Event-driven architecture with time-sensitive operations
- **Web Development**: Flask dashboard with real-time updates
- **Testing**: Integration testing for financial systems
- **Infrastructure**: Cloud deployment (DigitalOcean), secure remote access architecture

## Project Timeline

- **Development**: 2 weeks
- **Testing**: Paper trading validation
- **Deployment**: Production-ready on cloud infrastructure
- **Status**: Operational and monitoring live trades

---

_This project demonstrates end-to-end development of a production trading system, from strategy implementation to deployment and monitoring._
