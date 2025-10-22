# Enterprise Trading Platform

Multi-user algorithmic trading platform built from the ground up. Currently live in production serving multiple users for 4+ months.

## What It Does

- Enables non-technical users to deploy automated trading strategies
- Real-time WebSocket connections for live price monitoring
- TradingView webhook integration for signal processing
- Multi-user platform with isolated accounts and strategies
- Sophisticated hedging system for complex risk management
- Live dashboard with real-time metrics and strategy monitoring

## Technical Architecture

- **Backend**: FastAPI (async/await), PostgreSQL, SQLAlchemy (async)
- **Frontend**: React, TypeScript, Vite, React Router
- **Real-time**: WebSocket connections for price streaming and live dashboard updates
- **Security**: IP whitelisting, rate limiting, auto-banning system, Redis-based auth, JWT
- **Deployment**: Railway with GitHub CI/CD, auto-scaling
- **APIs**: TradingView webhooks, Bitget exchange API integration

## Key Features

- Production-grade security (IP filtering, rate limits, authentication layers, JWT)
- Real-time dashboard showing win rate, signal counts, and performance metrics
- Database abstraction layer reduces strategy deployment from days to hours
- Handles real trading decisions for multiple concurrent users
- Connection recovery and error handling for 24/7 uptime
- Protected routes with authentication context for secure user sessions

**Tech**: Python, FastAPI, PostgreSQL, Redis, WebSockets, React, TypeScript, Vite, Railway
