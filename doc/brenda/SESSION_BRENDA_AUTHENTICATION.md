# BRENDA Authentication Research Session
**Date:** October 24, 2025  
**Session Focus:** BRENDA API authentication requirements and implementation planning

---

## Summary

Confirmed that BRENDA SOAP API requires **free registration with email/password authentication**. Registration process includes manual approval by BRENDA administrators, which can take 1-2 business days.

---

## Authentication Requirements

### Registration Process
1. **Register:** https://www.brenda-enzymes.org/register.php
2. **Email Confirmation:** User receives confirmation email (minutes)
3. **BRENDA Database Refresh:** Administrative approval (1-2 business days)
4. **Credentials Active:** Can use SOAP API

### API Authentication Method
- **Method:** Email + SHA256-hashed password
- **Format:** `"email,password,<parameters>"`
- **Library:** Python Zeep for SOAP client
- **License:** Free under CC BY 4.0 license

### Example Authentication Code
```python
import hashlib
from zeep import Client, Settings

wsdl = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
password = hashlib.sha256("myPassword".encode("utf-8")).hexdigest()
settings = Settings(strict=False)
client = Client(wsdl, settings=settings)

parameters = (
    "j.doe@example.edu",
    password,
    "ecNumber*1.1.1.1",
    "organism*Homo sapiens",
    "kmValue*",
    "kmValueMaximum*",
    "substrate*",
    "commentary*",
    "ligandStructureId*",
    "literature*"
)
resultString = client.service.getKmValue(*parameters)
```

---

## Available SOAP Methods

BRENDA provides 159+ SOAP methods for querying enzyme data:

### Key Methods for Auto-Enrichment
- `getKmValue()` - Michaelis constant (substrate affinity)
- `getTurnoverNumber()` - kcat (catalytic rate)
- `getKiValue()` - Inhibition constant
- `getEnzymeNames()` - Systematic and recommended names
- `getRecommendedName()` - Preferred enzyme name
- `getSynonyms()` - Alternative names
- `getReference()` - Literature citations (PubMed IDs)
- `getOrganism()` - Organism-specific data
- `getSubstrate()` - Substrate information
- `getProduct()` - Product information
- `getActivatingCompound()` - Activators
- `getInhibitors()` - Inhibitors

### Data Categories Available
1. EC Numbers (enzyme classification)
2. Enzyme Names (systematic, recommended, synonyms)
3. Kinetic Parameters (Km, kcat, Vmax, Ki) ⭐ **MVP Priority**
4. Substrates & Products
5. Organism-Specific Data
6. Reaction Information
7. Regulatory Information (activators, inhibitors)
8. pH/Temperature Stability
9. Localization & Expression
10. Literature References ⭐ **MVP Priority**

---

## Implementation Architecture

### Module Structure
```
src/shypn/
├── credentials/
│   ├── credentials_manager.py    # Encrypt/store email+password
│   ├── user_profile.py           # UserProfile with BRENDA credentials
│   └── authenticators.py         # SHA256 password hashing
│
├── data/brenda/
│   ├── base_connector.py         # Abstract base with auth
│   ├── soap_client.py            # SOAP client (Zeep)
│   ├── brenda_connector.py       # Main connector
│   ├── cache_manager.py          # Local caching
│   ├── rate_limiter.py           # API throttling
│   └── models.py                 # Data models
│
└── enrichment/
    ├── auto_enrichment_engine.py # Main enrichment pipeline
    ├── gap_analyzer.py           # Identify missing data
    └── enrichment_wizard.py      # UI for gap resolution

doc/brenda/
├── BRENDA_DATA_REFERENCE.md      # (to be moved from doc/external_data/)
├── AUTO_ENRICHMENT_PIPELINE.md   # (to be moved from doc/external_data/)
└── SESSION_BRENDA_AUTHENTICATION.md  # This file
```

---

## User Experience Design

### Registration Timeline
- ✅ **Immediate:** User registration form
- ✅ **Minutes:** Email confirmation received
- ⏳ **1-2 Business Days:** BRENDA admin approval
- ✅ **Ready:** Credentials active for API access

### UI Flow

#### User Profile Dialog
```
┌─────────────────────────────────────────┐
│ BRENDA Integration (Optional)           │
├─────────────────────────────────────────┤
│ Email: [j.doe@example.edu            ] │
│ Password: [********************      ] │
│                                         │
│ Status: ⏳ Pending BRENDA approval      │
│                                         │
│ [ Test Connection ]  [ Register ]      │
│                                         │
│ ℹ️ BRENDA registration can take 1-2     │
│   business days for approval. You can   │
│   continue using SHYpn and add data     │
│   manually in the meantime.             │
└─────────────────────────────────────────┘
```

#### Connection Status States
- ❌ **Not configured:** "No BRENDA credentials entered"
- ⏳ **Pending approval:** "Credentials not yet activated (check email)"
- ✅ **Active:** "Successfully connected to BRENDA"
- ❌ **Invalid:** "Authentication failed - check credentials"

### Credential Testing
```python
class BrendaConnector:
    def test_connection(self, email, password):
        """Test if credentials are active."""
        try:
            # Simple query to test authentication
            result = self.query_ec_number("1.1.1.1")
            return {
                'status': 'success',
                'message': 'Successfully connected to BRENDA'
            }
        except AuthenticationError:
            return {
                'status': 'pending',
                'message': 'Credentials not yet activated. BRENDA approval can take 1-2 business days.'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection failed: {str(e)}'
            }
```

---

## Implementation Strategy

### Phased Approach (Recommended)

**Phase 1 (Week 1): Core Functionality WITHOUT BRENDA**
- Manual data entry for kinetic parameters
- Model metadata management
- Report generation (without auto-enrichment)
- User profile infrastructure
- **Benefit:** Users can start immediately

**Phase 2 (Week 2): BRENDA Integration Prep**
- Credentials manager with encryption
- User profile dialog with BRENDA fields
- Connection testing infrastructure
- Help documentation for registration
- **Benefit:** Infrastructure ready when credentials activate

**Phase 3 (Week 3): BRENDA Connector**
- SOAP client implementation using Zeep
- Auto-enrichment engine
- Gap analyzer
- Enrichment wizard UI
- **Benefit:** Full automation once credentials approved

### Graceful Degradation Design
- SHYpn works **fully functional** without BRENDA
- Auto-enrichment is an **optional enhancement**
- Manual data entry always available
- Users add BRENDA credentials when ready

---

## Security Considerations

### Password Storage
```python
# src/shypn/credentials/credentials_manager.py

class CredentialsManager:
    def store_brenda_credentials(self, email, password):
        """Store BRENDA credentials securely."""
        # Encrypt password before storage
        encrypted = self._encrypt(password)
        self.user_profile.brenda_email = email
        self.user_profile.brenda_password_encrypted = encrypted
        
    def get_brenda_auth(self):
        """Retrieve credentials for API call."""
        email = self.user_profile.brenda_email
        password = self._decrypt(self.user_profile.brenda_password_encrypted)
        # Hash password for SOAP API
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return email, password_hash
```

### Best Practices
1. **Never log passwords** - Only log email addresses
2. **Encrypt stored passwords** - Use system keyring or encryption
3. **Hash before sending** - SHA256 as per BRENDA API spec
4. **Local caching** - Minimize API calls, respect usage
5. **Rate limiting** - Implement delays between queries

---

## Testing Strategy

### Connection Testing
```python
# Test cases for BRENDA connector
def test_authentication():
    # Test valid credentials
    # Test invalid credentials
    # Test pending credentials
    # Test network errors
    pass

def test_query_by_ec():
    # Test EC number query
    # Test organism filtering
    # Test data parsing
    pass

def test_cache():
    # Test local caching
    # Test cache invalidation
    # Test cache performance
    pass
```

### User Testing Checklist
- ✅ Register at BRENDA website
- ✅ Receive confirmation email
- ⏳ Wait for admin approval (1-2 days)
- ✅ Test connection in SHYpn
- ✅ Query single enzyme
- ✅ Run auto-enrichment on imported model
- ✅ Verify gap analysis
- ✅ Generate enriched report

---

## Alternative: SPARQL Endpoint

BRENDA launched a new SPARQL endpoint in September 2025:
- **URL:** https://sparql.dsmz.de/brenda
- **Status:** Prototype/Beta
- **Authentication:** Unknown (not documented yet)

### Potential Benefits
- Modern query language
- Possibly no authentication required
- Standard semantic web interface

### Investigation Needed
- Check if authentication required
- Compare data availability vs SOAP
- Evaluate query complexity
- Assess stability/reliability

**Recommendation:** Start with SOAP (documented, stable), evaluate SPARQL as future enhancement.

---

## Next Steps

### Immediate Actions
1. ✅ Move `doc/external_data/BRENDA_DATA_REFERENCE.md` → `doc/brenda/`
2. ✅ Move `doc/external_data/AUTO_ENRICHMENT_PIPELINE.md` → `doc/brenda/`
3. ⏳ Wait for BRENDA credentials activation (user's account pending)
4. 🔨 Implement Phase 1 (core without BRENDA)

### Week 1 Deliverables
- Manual metadata entry UI
- UserProfile class structure
- Report generation (basic)
- Model metadata storage

### Week 2 Deliverables
- CredentialsManager with encryption
- User Profile dialog with BRENDA fields
- Connection testing
- Help documentation

### Week 3 Deliverables
- SOAP client using Zeep
- Auto-enrichment engine
- Gap analyzer
- Enrichment wizard

---

## Resources

### BRENDA Links
- **Homepage:** https://www.brenda-enzymes.org/
- **Registration:** https://www.brenda-enzymes.org/register.php
- **SOAP Documentation:** https://www.brenda-enzymes.org/soap.php
- **SPARQL Endpoint:** https://sparql.dsmz.de/brenda
- **License:** CC BY 4.0 (free for academic use)

### Python Libraries
- **Zeep:** SOAP client for Python 3 - https://python-zeep.readthedocs.io/
- **hashlib:** Built-in SHA256 hashing
- **keyring:** Secure credential storage (optional)
- **cryptography:** Encryption library (if not using keyring)

### Documentation to Complete
- User guide for BRENDA registration
- Developer guide for connector architecture
- API troubleshooting guide
- Examples of enriched reports

---

## Lessons Learned

1. **Registration Delays Are Real:** Manual approval process requires patience
2. **Graceful Degradation Essential:** System must work without external dependencies
3. **User Communication Critical:** Clear status messages prevent frustration
4. **Security First:** Proper credential storage from the start
5. **Phase Implementation:** Deliver value incrementally while waiting for access

---

## Status Summary

- ✅ Authentication requirements confirmed
- ✅ SOAP API documentation reviewed
- ✅ Architecture designed
- ✅ User registered at BRENDA
- ⏳ Awaiting credential activation (1-2 days)
- 📋 Implementation plan defined
- 🚀 Ready to begin Phase 1 development

---

**End of Session Notes**

This session established that BRENDA integration requires authenticated access with email/password, but registration takes time. The phased implementation approach allows users to start using SHYpn immediately while BRENDA credentials are being activated, with auto-enrichment added as an optional enhancement later.

The key insight: **Make BRENDA integration optional and additive, not a blocking dependency.**
