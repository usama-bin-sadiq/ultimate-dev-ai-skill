---
name: blockchain
description: >
  Blockchain development, smart contracts, Web3, DeFi, NFTs, token standards, gas optimization, security auditing, decentralized applications. Works with ANY blockchain platform.
triggers: [blockchain, smart contract, Web3, DeFi, NFT, token, gas, decentralized, dApp, Solidity, EVM, consensus, distributed ledger]
anti_triggers: [traditional backend, centralized database, frontend UI, mobile app]
last_verified: 2026-09-21
---

# Blockchain/Web3 Module (pattern-based)

## Core Principles (technology-agnostic)

1. **Security first** — smart contracts are immutable, bugs are permanent
2. **Gas optimization** — minimize transaction costs
3. **Decentralization** — design for trustless systems
4. **Transparency** — all transactions are public
5. **Testing** — comprehensive test coverage, formal verification

## Key Patterns

### Smart Contract Patterns
- Upgradeable proxies (UUPS, Transparent)
- Access control (roles, owners)
- Pausable/emergency stop
- Pull over push (payment patterns)
- Factory patterns

### Token Standards
- Fungible tokens (ERC-20, SPL)
- Non-fungible tokens (ERC-721, ERC-1155)
- Soulbound tokens
- Governance tokens
- Revenue share tokens

### DeFi Patterns
- Automated Market Makers (AMM)
- Lending/Borrowing protocols
- Yield farming
- Liquidity pools
- Flash loans

### Security Patterns
- Reentrancy guards
- Integer overflow protection
- Input validation
- Access control
- Audit trail

### Gas Optimization
- Storage packing
- Batch operations
- Event logging over storage
- Lazy evaluation
- Assembly optimization

### Testing Patterns
- Unit tests (Hardhat, Foundry)
- Integration tests (fork testing)
- Formal verification
- Fuzz testing
- Security audits

## Anti-Patterns
- Bad: "Skip security audit" — violates security first
- Good: "Audit before mainnet deployment" — satisfies security first

- Bad: "Store everything on-chain" — violates gas optimization
- Good: "Store hashes on-chain, data off-chain" — satisfies gas optimization

- Bad: "Upgrade without governance" — violates decentralization
- Good: "DAO governance for upgrades" — satisfies decentralization

## Output Contract
- Smart contract code
- Security audit reports
- Gas optimization analysis
- Test coverage reports
- Deployment scripts