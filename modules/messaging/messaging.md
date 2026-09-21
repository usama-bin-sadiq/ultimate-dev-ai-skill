---
name: messaging
description: >
  Message queues, event streaming, pub/sub patterns, message brokers, async communication, event-driven architecture, saga patterns. Works with ANY messaging technology.
triggers: [message queue, event streaming, pub/sub, async communication, event-driven, saga, message broker, async processing]
anti_triggers: [synchronous API, REST endpoint, database queries, frontend UI]
last_verified: 2026-09-21
---

# Messaging & Event-Driven Module

## Core Principles (technology-agnostic)

1. **Message durability** — persist messages before processing
2. **Idempotency** — handle duplicate messages gracefully
3. **Backpressure** — handle load spikes without crashing
4. **Schema evolution** — version message schemas, backward compatible
5. **Observability** — track message flow, latency, errors

## Key Patterns

### Message Patterns
- Publish/Subscribe
- Request/Reply
- Saga (distributed transactions)
- CQRS (command query separation)
- Event Sourcing

### Any Technology
- Traditional brokers (RabbitMQ, ActiveMQ)
- Event streaming (Kafka, Pulsar, NATS)
- Cloud managed (SQS, SNS, Pub/Sub)
- In-memory (Redis Streams, BullMQ, Agenda)
- Lightweight (ZeroMQ, nanomsg)

### Best Practices (apply to ALL)
- Message size limits
- Dead letter queues
- Message TTL
- Consumer groups
- Partitioning strategies

## Anti-Patterns
- Bad: "Process messages synchronously" — violates async principle
- Good: "Use async processing with acknowledgments" — satisfies async

- Bad: "Ignore message ordering" — violates schema evolution
- Good: "Use partition keys for ordering" — satisfies schema evolution

## Output Contract
- Message flow diagrams
- Broker configurations (generic)
- Consumer/producer code (adapter pattern)
- Schema definitions
- Monitoring dashboards