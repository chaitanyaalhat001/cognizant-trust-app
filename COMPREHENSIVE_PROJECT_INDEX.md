# Cognizant Trust - Comprehensive Project Index

## Project Overview
A Django-based blockchain-integrated donation and trust management platform with transparency features, social spending tracking, and automated verification systems.

## 🏗️ Project Architecture

### Core Framework
- **Framework**: Django
- **Database**: SQLite3 (db.sqlite3)
- **Blockchain Integration**: Web3.py with Ethereum smart contracts
- **Frontend**: HTML/CSS/JavaScript with Bootstrap

---

## 📁 Directory Structure & Components

### 1. Root Level Files

| File | Purpose | Size |
|------|---------|------|
| `manage.py` | Django management script | 692B |
| `requirements.txt` | Python dependencies | 155B |
| `db.sqlite3` | SQLite database file | 216KB |
| `create_sample_data.py` | Sample data generation script | 4.0KB |
| `.credentials.enc` | Encrypted credentials | 332B |
| `.salt` | Encryption salt | 16B |

### 2. Documentation Files

| File | Purpose | Size |
|------|---------|------|
| `README.md` | Main project documentation | 8.7KB |
| `PROJECT_INDEX.md` | Existing project index | 10KB |
| `AUTO_SCANNER_USAGE.md` | Auto scanner documentation | 3.5KB |
| `SPENDING_CONTRACT_SETUP.md` | Smart contract setup guide | 5.2KB |
| `CONTRACT_VERIFICATION.md` | Contract verification guide | 3.6KB |
| `FINAL_CONFIGURATION.md` | Final setup configuration | 4.5KB |
| `METAMASK_SETUP_GUIDE.md` | MetaMask integration guide | 8.6KB |
| `BLOCKCHAIN_SETUP.md` | Blockchain setup instructions | 3.5KB |

### 3. Core Django Application (`cognizanttrust/`)

**Purpose**: Main Django project configuration and security

| File | Purpose | Lines |
|------|---------|-------|
| `settings.py` | Django settings configuration | 151 |
| `urls.py` | Main URL routing | 24 |
| `crypto_utils.py` | Cryptographic utilities | 141 |
| `security_config.py` | Security configuration | 223 |
| `wsgi.py` | WSGI configuration | 17 |
| `asgi.py` | ASGI configuration | 17 |

### 4. Donations App (`donations/`)

**Purpose**: Core donation management and user interface

#### Core Application Files
| File | Purpose | Lines |
|------|---------|-------|
| `models.py` | Database models | 299 |
| `views.py` | View controllers | 1,628 |
| `forms.py` | Django forms | 205 |
| `urls.py` | URL routing | 41 |
| `admin.py` | Django admin config | 4 |
| `apps.py` | App configuration | 54 |

#### Specialized Components
| File | Purpose | Lines |
|------|---------|-------|
| `pdf_generator.py` | PDF report generation | 487 |
| `auto_scanner.py` | Automated scanning system | 207 |

#### Management Commands (`donations/management/commands/`)
| Command | Purpose | Lines |
|---------|---------|-------|
| `auto_scan_background.py` | Background scanning service | 177 |
| `auto_record_pending.py` | Pending transaction recording | 143 |
| `verify_pending_transactions.py` | Transaction verification | 101 |

#### Template Tags (`donations/templatetags/`)
| File | Purpose | Lines |
|------|---------|-------|
| `currency_filters.py` | Currency formatting filters | 60 |

### 5. Web3 Integration App (`web3_integration/`)

**Purpose**: Blockchain and Web3 connectivity

| File | Purpose | Lines |
|------|---------|-------|
| `auto_recorder.py` | Automated blockchain recording | 451 |
| `web3_utils.py` | Web3 utility functions | 144 |

### 6. Blockchain App (`blockchain/`)

**Purpose**: Basic blockchain models and configuration

| File | Purpose | Lines |
|------|---------|-------|
| `models.py` | Blockchain data models | 4 |
| `views.py` | Blockchain views | 4 |
| `admin.py` | Admin configuration | 4 |

### 7. Smart Contracts (`contracts/`)

**Purpose**: Ethereum smart contracts for transparency

#### SpendingRecorder.sol (129 lines)
- **Purpose**: Ultra-minimal spending transaction recording
- **Storage Optimization**: ~37 bytes per record (90% reduction from previous approach)
- **Features**:
  - Compressed data structure (amount in paisa, 8-bit category ID, 32-bit timestamp)
  - 10 predefined categories (Education, Healthcare, Food, Shelter, etc.)
  - Gas-optimized storage with enum-based categories
  - Event-based logging for transparency
- **Functions**: recordSpending(), getSpending(), getAllSpendings()

#### TrustTransactionRecorder.sol (115 lines)
- **Purpose**: Complete donation transaction recording
- **Features**:
  - Full donor information storage (name, amount, purpose, UPI reference)
  - Admin wallet tracking
  - Transaction hash generation and verification
  - Comprehensive event emission
- **Functions**: recordTransaction(), getTransaction(), getTotalTransactions()

#### Contract Security
- **Solidity Version**: ^0.8.19 (latest stable)
- **Access Control**: onlyAdmin modifier for write operations
- **Validation**: Input validation for all parameters
- **Events**: Comprehensive event logging for audit trails

### 8. Templates (`templates/`)

**Purpose**: HTML templates for user interface

#### Base Template (`base.html` - 1,791 lines)
**Foundation**: Complete UI framework with Cognizant design system
**Features**:
- **Design System**: Authentic Cognizant brand colors and gradients
- **Responsive Layout**: Bootstrap 5.3 with custom responsive utilities
- **Dark/Light Mode**: Complete theme switching with CSS variables
- **Typography**: Professional font system (Poppins, Inter)
- **Components**: Reusable cards, buttons, navigation, and form elements
- **Accessibility**: ARIA compliance and keyboard navigation support
- **Performance**: Optimized CSS loading and minimal external dependencies

#### Donation Templates (`templates/donations/`)

**UI Framework**: Bootstrap 5.3 with Cognizant Design System
**Typography**: Poppins & Inter fonts matching Cognizant branding
**Color Scheme**: Cognizant brand colors with dark/light mode support

| Template | Purpose | Lines | Key Features |
|----------|---------|-------|--------------|
| `admin_dashboard.html` | Admin dashboard interface | 1,950 | Statistics cards, navigation panels, blockchain controls, CSRF protection |
| `social_spending.html` | Social spending transparency | 896 | Interactive spending visualization, category filtering, public transparency |
| `donation_management.html` | Donation management interface | 835 | Transaction management, status tracking, bulk operations |
| `verified_spending.html` | Verified spending display | 683 | Blockchain-verified transactions, verification badges |
| `verified_donations.html` | Verified donations display | 682 | Donation verification status, receipt management |
| `user_donate.html` | User donation interface | 549 | Donation form, UPI integration, receipt generation |
| `home.html` | Homepage | 522 | Landing page, feature overview, navigation |
| `admin_login.html` | Admin login page | 465 | Secure admin authentication, form validation |
| `public_audit.html` | Public audit interface | 466 | Public transparency dashboard, audit trails |
| `user_dashboard.html` | User dashboard | 305 | Personal donation history, profile management |
| `spending_transparency.html` | Spending transparency | 204 | Public spending overview, category breakdowns |
| `user_profile.html` | User profile page | 131 | Profile editing, preference management |
| `user_register.html` | User registration | 172 | User onboarding, form validation |
| `user_login.html` | User login page | 78 | User authentication, session management |

### 9. Static Files (`static/`)

**Purpose**: Static assets (images, CSS, JavaScript)

| Directory/File | Purpose |
|----------------|---------|
| `images/logo.png` | Application logo |

### 10. Temporary Files (`temp/`)

**Purpose**: Temporary storage and development files

| File | Purpose | Size |
|------|---------|------|
| `ref receipt.pdf` | Reference receipt document | 477KB |
| `logo.png` | Logo file | 73KB |
| `Cognizant.html` | Cognizant webpage reference | 563KB |

### 11. Testing & Development

| File | Purpose | Lines |
|------|---------|-------|
| `test_contract.html` | Contract testing interface | 156 |

---

## 🗄️ Data Models & Database Schema

### Core Models (donations/models.py)

#### 1. DonorProfile
**Purpose**: Extended user profile for donors
- **Fields**: phone_number, address, city, state, pincode, pan_number, date_of_birth, preferred_donation_causes, is_verified
- **Relationships**: OneToOne with Django User model
- **Features**: PAN validation, phone validation, donation statistics

#### 2. DonationTransaction
**Purpose**: Records all donation transactions with blockchain integration
- **Primary Key**: UUID field for unique identification
- **Key Fields**: 
  - donor (optional User link), donor_name, donor_email, donor_phone
  - amount, purpose, upi_ref_id, timestamp
  - blockchain_status (pending/recorded/failed)
  - blockchain_tx_hash, attempted_tx_hash
  - receipt_generated, receipt_number, tax_exemption_claimed
- **Features**: Auto-receipt generation, blockchain status tracking

#### 3. DonationSpending
**Purpose**: Tracks welfare spending with categorization
- **Primary Key**: UUID field
- **Categories**: Education, Healthcare, Food Distribution, Shelter, Disaster Relief, Elderly Care, Child Welfare, Skill Development, Sanitation, Other
- **Key Fields**:
  - title, description, category, amount
  - beneficiaries, location, spent_date
  - blockchain_status, blockchain_tx_hash
  - receipt_reference
- **Features**: Blockchain recording, category-based tracking

#### 4. AutoRecordingSettings (Singleton)
**Purpose**: Configuration for automatic blockchain recording
- **Recording Modes**: Manual (MetaMask) / Automatic (Server-side)
- **Security Features**:
  - credentials_configured flag
  - session_timeout_minutes (default: 60)
  - max_auto_amount (default: ₹50,000)
  - auto_recording_enabled master switch
  - security_audit_date tracking
- **Features**: Singleton pattern, security status monitoring

---

## 🔧 Key Features & Components

### 1. User Management
- User registration and authentication
- User profiles and dashboards
- Admin interface with comprehensive controls

### 2. Donation System
- Donation processing and tracking
- PDF receipt generation
- Social spending transparency
- Public audit capabilities

### 3. Blockchain Integration
- **Ethereum Smart Contracts**: Two specialized contracts for donations and spending
- **Web3.py Integration**: Complete ABI definitions and contract interaction
- **Automated Recording**: Dual-mode operation (MetaMask manual/Server-side automatic)
- **Transaction Verification**: Hash-based verification and status tracking
- **Gas Optimization**: Ultra-minimal data structures for cost efficiency
- **Event Monitoring**: Comprehensive blockchain event logging

### 4. Transparency Features
- Verified spending displays
- Public audit interfaces
- Social spending tracking
- Automated scanning and verification

### 5. Security & Encryption
- **SecureCredentialManager**: Military-grade AES-128 encryption with PBKDF2 key derivation
- **Encrypted Storage**: Wallet credentials stored in `.credentials.enc` with salt-based key derivation
- **Security Configuration**: Comprehensive security settings in `security_config.py`
- **Web3 Integration**: Secure blockchain connectivity with encrypted private key management
- **Session Management**: Configurable auto-recording timeouts and amount limits

### 6. Automation Systems

#### Background Processing
- **Auto-Scan Background** (`auto_scan_background.py`): Continuous scanning service for pending transactions
- **Auto-Record Pending** (`auto_record_pending.py`): Batch processing of pending blockchain recordings
- **Verify Pending Transactions** (`verify_pending_transactions.py`): Transaction verification and status updates

#### Blockchain Automation
- **AutoBlockchainRecorder**: Server-side private key signing for seamless automation
- **Session Management**: Password caching with configurable timeouts
- **Automatic Initialization**: Self-healing system with credential validation
- **Batch Processing**: Efficient bulk transaction recording

#### Smart Scanning
- **Age-based Filtering**: Only processes transactions within specified time windows
- **Security Validation**: Multi-layer security checks before processing
- **Error Handling**: Comprehensive error tracking and recovery
- **Status Monitoring**: Real-time status updates and logging

---

## 📊 File Statistics

### By Category
- **Total Files**: ~45 core files
- **Python Files**: 25+
- **HTML Templates**: 15
- **Smart Contracts**: 2
- **Documentation**: 8
- **Configuration**: 5+

### By Size (Major Components)
- **Largest View File**: `donations/views.py` (70KB, 1,628 lines)
- **Largest Template**: `base.html` (67KB, 1,791 lines)
- **Largest Component**: `admin_dashboard.html` (86KB, 1,950 lines)
- **Database**: `db.sqlite3` (216KB)

---

## 🔗 Dependencies & Technologies

### Core Dependencies (from requirements.txt)
- **Django==4.2.7** - Web framework
- **web3==6.11.3** - Ethereum blockchain integration
- **python-dotenv==1.0.0** - Environment variable management
- **django-cors-headers==4.3.1** - CORS handling
- **cryptography==41.0.7** - Cryptographic operations
- **eth-account==0.13.7** - Ethereum account management
- **reportlab==4.4.3** - PDF generation
- **Pillow==11.3.0** - Image processing

### Frontend Technologies
- HTML5/CSS3
- Bootstrap framework
- JavaScript for interactive features

### Blockchain Technologies
- Ethereum smart contracts (Solidity)
- Web3 integration
- MetaMask wallet integration

---

## 🎯 Key Use Cases

1. **Donation Management**: Complete donation lifecycle from collection to verification
2. **Transparency Reporting**: Public audit trails and spending verification
3. **Social Impact Tracking**: Social spending transparency and community engagement
4. **Administrative Control**: Comprehensive admin dashboard for system management
5. **Blockchain Verification**: Automated recording and verification on Ethereum

---

## 📈 Development & Maintenance

### Management Commands
- Background scanning automation
- Pending transaction processing
- Verification workflows

### Testing & Quality Assurance
- Contract testing interfaces
- Sample data generation
- Verification systems

---

## 🚀 Deployment & Configuration

### Environment Setup
- **Development Mode**: DEBUG=True in settings.py
- **Database**: SQLite3 for development (216KB current size)
- **Static Files**: Bootstrap CDN + local assets
- **Secret Management**: Django secret key in settings (should be externalized for production)

### Production Considerations
- **Database Migration**: Recommended PostgreSQL for production
- **Environment Variables**: Use python-dotenv for configuration
- **Static Files**: Configure proper static file serving
- **Security**: Update secret key, disable debug mode
- **CORS**: Already configured with django-cors-headers

### Blockchain Configuration
- **Network**: Ethereum mainnet/testnet support
- **Gas Optimization**: Ultra-minimal contract design for cost efficiency
- **Wallet Integration**: MetaMask and server-side signing support

---

## 🔗 API & Integration Points

### Web3 Integration
- **Contract Interaction**: Full ABI support for both contracts
- **Transaction Monitoring**: Event-based blockchain monitoring
- **Automatic Recording**: Server-side transaction signing
- **MetaMask Integration**: Frontend wallet connectivity

### Data Export/Import
- **PDF Generation**: ReportLab-based receipt generation
- **CSV Export**: Built-in Django admin export capabilities
- **Blockchain Export**: Transaction hash and verification data

### Management Interface
- **Django Admin**: Enhanced admin interface for all models
- **Custom Commands**: Multiple management commands for automation
- **API Endpoints**: RESTful endpoints for transaction management

---

## 📋 Development Workflow

### File Organization
- **Modular Structure**: Separate apps for donations, blockchain, web3 integration
- **Template Inheritance**: Centralized base template with feature-specific templates
- **Static Assets**: Organized image and asset management
- **Documentation**: Comprehensive documentation for all major features

### Code Quality
- **Django Best Practices**: Proper model relationships and validation
- **Security**: Encrypted credential storage and CSRF protection
- **Performance**: Optimized database queries and blockchain interactions
- **Maintainability**: Clear separation of concerns and comprehensive logging

This comprehensive index provides a complete overview of the Cognizant Trust project structure, components, and functionality. 