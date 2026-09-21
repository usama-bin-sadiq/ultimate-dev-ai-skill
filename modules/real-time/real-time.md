---
name: real-time
description: >
  Real-time communication, WebSockets, Server-Sent Events, polling, push notifications, live data, collaboration features. Technology-agnostic.
triggers: [WebSocket, real-time, live, push notification, Server-Sent Events, polling, collaboration, chat, live data]
anti_triggers: [batch processing, static pages, API design, database schema]
last_verified: 2026-09-21
---

# Real-Time Communication Module (pattern-based)

## Core Principles (technology-agnostic)

1. **Connection management** — handle connects, disconnects, reconnects
2. **Scalability** — horizontal scaling with sticky sessions or pub/sub
3. **Fallback** — SSE → long polling → short polling
4. **Security** — authenticate connections, validate messages
5. **Observability** — track connections, message rates, latency

## Key Patterns

### Connection Patterns
- WebSocket (bidirectional)
- Server-Sent Events (one-way)
- Long polling (fallback)
- Short polling (simple)
- WebRTC (peer-to-peer)

### Scaling Patterns
- Sticky sessions
- Redis pub/sub for broadcast
- Message queues for fan-out
- Connection pooling
- Load balancer configuration

### State Patterns
- Room/channel management
- Presence detection
- Cursor/position sync
- Operational Transform (OT)
- Conflict-free Replicated Data Types (CRDT)

### Message Patterns
- JSON payloads
- Binary payloads
- Message compression
- Message batching
- Heartbeat/ping-pong

### Security Patterns
- Token-based authentication
- Rate limiting per connection
- Message validation
- IP filtering
- CORS configuration

## Anti-Patterns
- Bad: "No reconnection logic" — violates connection management
- Good: "Exponential backoff reconnection" — satisfies connection management

- Bad: "Broadcast to all connections" — violates scalability
- Good: "Room-based broadcasting" — satisfies scalability

## Output Contract
- Connection architecture diagrams
- Message flow diagrams
- Scaling configuration
- Security configuration
- Monitoring dashboards