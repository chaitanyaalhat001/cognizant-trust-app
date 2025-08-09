# CognizantTrust - Blockchain-Based Donation Platform

A transparent, blockchain-powered donation platform that records trust-related financial transactions on the Ethereum testnet for public accountability and tamper-proof transparency.

## 🚀 Features

- **Transparent Donations**: All donations are recorded on the Ethereum blockchain
- **MetaMask Integration**: Admin uses MetaMask to sign and send blockchain transactions
- **Public Audit Trail**: Anyone can verify donations on the blockchain
- **Modern UI**: Cognizant-inspired design with Bootstrap 5
- **Mocked Payments**: UPI payment simulation for prototype demonstration
- **Real-time Updates**: Live status tracking from donation to blockchain recording

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Backend**: Django 4.2.7 (Python)
- **Blockchain**: Solidity smart contract on Ethereum Sepolia testnet
- **Web3**: Web3.js for blockchain interaction
- **Wallet**: MetaMask for transaction signing
- **Database**: SQLite (Django default)

## 🏗️ Project Structure

```
cognizanttrust/
├── contracts/                  # Solidity smart contracts
│   └── TrustTransactionRecorder.sol
├── donations/                  # Django app for donation management
│   ├── models.py              # Database models
│   ├── views.py               # API endpoints and views
│   └── urls.py                # URL routing
├── web3_integration/          # Web3 utilities and blockchain interaction
│   └── web3_utils.py
├── templates/                 # HTML templates
│   ├── base.html              # Base template with Cognizant styling
│   └── donations/
│       ├── home.html          # Donor donation form
│       ├── admin_dashboard.html # Admin dashboard
│       └── public_audit.html  # Public audit trail
├── static/                    # Static files (CSS, JS, images)
├── cognizanttrust/           # Django project settings
└── requirements.txt          # Python dependencies
```

## 🔧 Installation & Setup

### Prerequisites

- Python 3.8+
- Node.js (for MetaMask integration)
- MetaMask browser extension
- Access to Ethereum Sepolia testnet

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd cognizanttrust

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Create sample data and admin user
python create_sample_data.py
```

### 2. Admin Credentials

- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@cognizanttrust.com`

### 3. Start Development Server

```bash
python manage.py runserver
```

Visit: `http://localhost:8000`

## 🌐 Smart Contract Deployment

### Contract Details

- **Name**: `TrustTransactionRecorder`
- **Network**: Ethereum Sepolia Testnet
- **Functions**:
  - `recordTransaction()`: Records donation on blockchain
  - `getTransaction()`: Retrieves transaction details
  - `getTotalTransactions()`: Gets total transaction count

### Deployment Steps

1. **Compile Contract**: Use Remix IDE or Hardhat
2. **Deploy to Sepolia**: Using MetaMask and Sepolia ETH
3. **Update Settings**: Add contract address to `cognizanttrust/settings.py`

```python
# In settings.py
CONTRACT_ADDRESS = 'YOUR_DEPLOYED_CONTRACT_ADDRESS'
WEB3_PROVIDER_URL = 'https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID'
```

## 📱 Usage Guide

### For Donors (Public Users)

1. **Visit Homepage**: Navigate to the donation form
2. **Fill Details**: Enter name, amount, and purpose
3. **Submit Donation**: Payment is mocked (shows success immediately)
4. **Track Status**: View donation in public audit trail

### For Admins

1. **Login**: Use admin credentials to access dashboard
2. **Connect MetaMask**: Click "Connect MetaMask" button
3. **Review Donations**: See all pending donations
4. **Record on Blockchain**: Click "Record on Blockchain" for pending donations
5. **Confirm Transaction**: Approve the transaction in MetaMask
6. **Verify**: Check transaction hash on Etherscan

### Public Verification

1. **Visit Audit Trail**: Check `/audit/` page
2. **View Verified Donations**: See all blockchain-recorded donations
3. **Verify on Etherscan**: Click transaction hash links
4. **Independent Verification**: Anyone can verify the authenticity

## 🔐 Security Features

- **Blockchain Immutability**: Records cannot be altered once on blockchain
- **MetaMask Security**: Admin wallet controls transaction signing
- **Public Verification**: All transactions verifiable on Etherscan
- **Data Integrity**: Hash-based transaction verification
- **Admin Authentication**: Protected admin dashboard

## 🎨 UI/UX Design

### Cognizant-Inspired Styling

- **Colors**: Official Cognizant blue (#003366) and orange (#FF6600)
- **Typography**: Inter font family for modern, clean look
- **Components**: Bootstrap 5 with custom CSS overrides
- **Responsive**: Mobile-first design approach
- **Accessibility**: ARIA labels and semantic HTML

### Key Design Elements

- Gradient headers with corporate branding
- Card-based layout for information organization
- Status badges for transaction states
- Interactive blockchain verification buttons
- Professional color scheme and typography

## 🧪 Testing

### Sample Data Included

- 5 pre-loaded sample donations
- Mix of pending and recorded transactions
- Sample UPI reference IDs
- Mock blockchain transaction hashes

### Manual Testing Checklist

- [ ] Donor form submission
- [ ] Admin login and dashboard access
- [ ] MetaMask connection
- [ ] Blockchain transaction recording
- [ ] Public audit trail display
- [ ] Responsive design on mobile
- [ ] Cross-browser compatibility

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Move sensitive settings to environment variables
2. **Database**: Migrate from SQLite to PostgreSQL
3. **Static Files**: Configure static file serving
4. **HTTPS**: Implement SSL certificates
5. **Real Payments**: Integrate actual payment gateway
6. **Gas Optimization**: Optimize smart contract for lower gas costs

### Environment Variables

```bash
# Required for production
DJANGO_SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
WEB3_PROVIDER_URL=your-infura-or-alchemy-url
CONTRACT_ADDRESS=your-deployed-contract-address
```

## 📊 Architecture Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Donor     │────│   Django     │────│   Database      │
│   (Public)  │    │   Backend    │    │   (SQLite)      │
└─────────────┘    └──────────────┘    └─────────────────┘
                           │
                           │
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Admin     │────│   MetaMask   │────│   Ethereum      │
│ (Dashboard) │    │   (Web3.js)  │    │   Blockchain    │
└─────────────┘    └──────────────┘    └─────────────────┘
                                               │
                           ┌─────────────────────┘
                           │
                   ┌──────────────┐
                   │   Public     │
                   │ Verification │
                   │ (Etherscan)  │
                   └──────────────┘
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is created for educational and prototype purposes.

## 📞 Support

For questions and support:
- Email: admin@cognizanttrust.com
- GitHub Issues: Use the repository issue tracker

## 🏆 Future Enhancements

- [ ] Real payment gateway integration (Razorpay/Stripe)
- [ ] Multi-token support (ERC-20 tokens)
- [ ] Advanced reporting and analytics
- [ ] Email notifications for donors
- [ ] Multi-language support
- [ ] Mobile app development
- [ ] IPFS integration for document storage
- [ ] Advanced admin roles and permissions

---

**Built with ❤️ using Django, Ethereum, and modern web technologies** 