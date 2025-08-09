# Blockchain Setup Guide for CognizantTrust

## 🚀 Deploy Smart Contract to Sepolia Testnet

### Prerequisites
- MetaMask browser extension installed
- Sepolia ETH for gas fees (get from [Sepolia Faucet](https://sepoliafaucet.com/))
- Access to [Remix IDE](https://remix.ethereum.org/)

### Step 1: Deploy Contract via Remix

1. **Open Remix IDE**: Go to https://remix.ethereum.org/
2. **Create New File**: Create `TrustTransactionRecorder.sol`
3. **Copy Contract Code**: Copy the content from `contracts/TrustTransactionRecorder.sol`
4. **Compile Contract**:
   - Go to "Solidity Compiler" tab
   - Select compiler version 0.8.19 or higher
   - Click "Compile TrustTransactionRecorder.sol"
5. **Deploy Contract**:
   - Go to "Deploy & Run Transactions" tab
   - Select "Injected Provider - MetaMask" as environment
   - Make sure MetaMask is connected to Sepolia testnet
   - Select "TrustTransactionRecorder" contract
   - Click "Deploy"
   - Confirm transaction in MetaMask

### Step 2: Get Contract Address

After deployment, copy the deployed contract address from Remix.

### Step 3: Update Django Settings

Replace the contract address in two places:

1. **Django Settings** (`cognizanttrust/settings.py`):
```python
CONTRACT_ADDRESS = 'YOUR_DEPLOYED_CONTRACT_ADDRESS'
WEB3_PROVIDER_URL = 'https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID'
```

2. **Admin Dashboard** (`templates/donations/admin_dashboard.html`):
```javascript
const CONTRACT_ADDRESS = 'YOUR_DEPLOYED_CONTRACT_ADDRESS';
```

### Step 4: Get Infura/Alchemy Endpoint

1. **Create Infura Account**: Go to https://infura.io/
2. **Create New Project**: Select "Web3 API"
3. **Get Endpoint URL**: Copy the Sepolia testnet endpoint
4. **Update Settings**: Add the URL to Django settings

### Step 5: Test Blockchain Recording

1. **Start Django Server**: `python manage.py runserver`
2. **Login as Admin**: Use credentials `admin` / `admin123`
3. **Connect MetaMask**: Click "Connect MetaMask" in admin dashboard
4. **Record Transaction**: Click "Record on Blockchain" for any pending donation
5. **Confirm in MetaMask**: Approve the transaction
6. **Verify on Etherscan**: Check transaction hash on https://sepolia.etherscan.io/

## 🔧 Alternative: Use Pre-deployed Contract

For testing purposes, you can use this pre-deployed contract:

**Contract Address**: `0x123...abc` (example)
**Network**: Sepolia Testnet
**Explorer**: https://sepolia.etherscan.io/address/CONTRACT_ADDRESS

## 📝 Current Status

✅ Smart contract code ready
✅ MetaMask integration implemented
✅ Admin dashboard with recording functionality
❌ Contract not deployed to testnet
❌ Settings not configured with real contract address

## 🎯 What Happens After Setup

1. **User Donates**: Payment processed (mocked) and stored in Django database
2. **Admin Reviews**: Sees pending donation in admin dashboard
3. **Blockchain Recording**: Admin clicks "Record on Blockchain"
4. **MetaMask Signs**: Admin confirms transaction with MetaMask
5. **Blockchain Storage**: Transaction recorded permanently on Ethereum
6. **Public Verification**: Anyone can verify on Etherscan
7. **Audit Trail**: Shows in public audit page with transaction hash

## 🛡️ Security Features

- **Immutable Records**: Cannot be changed once on blockchain
- **Public Verification**: Anyone can verify transactions
- **Admin Control**: Only admin can record transactions
- **Gas Optimization**: Efficient contract design
- **Event Logging**: Blockchain events for confirmation 