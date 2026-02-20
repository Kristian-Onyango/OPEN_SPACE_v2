# Open Space - Peer-to-Peer Local Network Protocol

## Quick Start

pip install -r requirements.txt

python main.py

## <u>What This Is</u>
```
A decentralized network protocol that enables device discovery, secure messaging, and service
sharing prioritizing devices connected to and the services offered in the network and offers 
fallback to the internet incase the recipient device or required service is not in the network.
```
# 1.  <U> 🚀 Quick Start</u>


## Clone and run in 30 seconds
git clone https://github.com/yourusername/localmesh

cd localmesh
python main.py

Your device will automatically:

- Discover other LocalMesh devices on your network

- Appear in their network tables

- Be ready to send/receive messages

# 2. <u>WHY THIS EXISTS</u>
### The Problem:
- Expensive and the common issue of unreliable internet
- Privacy concerns with cloud services
- Need for fast connection during internet outages

### Our Solution
OpenSpace creates resilient local networks that:
- Work WITHOUT internet
- Reduce bandwidth costs
- Keep data within your community
- Scale from 2+ devices

# 3. <u> KEY FEATURES</u>
## Working Features
✅ **Automatic Discovery** - Devices find each other instantly  
✅ **Reliable Messaging** - ACK-based delivery with retries  
✅ **Role-Based Routing** - Send to "game", "chat", or "storage" nodes  
✅ **Persistent Identity** - Devices remembered across restarts  
✅ **Health Monitoring** - Automatic node reliability scoring  

# 4. <b><u>ARCHITECTURE</u></b>
## 🏗️ How It Works (Simplified)

| Layer               | Function                               |
|---------------------|----------------------------------------|
| **3->Applications** | Chat, games, file sharing             |
| **2->Messaging**    | Reliable device-to-device communications |
| **1->Discovery**    | Find devices automatically             |

1. **Discovery Layer**: Devices broadcast their presence
2. **Messaging Layer**: Secure, reliable communication  
3. **Application Layer**: Build anything on top!

### Layer 1: DISCOVERY & NETWORK TABLE

Purpose: Devices find each other on same network

Supports: Games find players, chats find users,websites find visitors

### Layer 2: DNS PROTOCOL

Purpose: Resolve *.localnet addresses to local services

Supports: Websites,apps,service with local domain names

### Layer 3: SERVICE PROTOCOL

Purpose: Advertise what services/apps are available locally

Supports: "I host chat server" , "I host game lobby server" , "I host website"

### Layer 4: MESSAGING PROTOCOL

Purpose: Direct device to device communication

Supports: Chat apps , game multiplayer , file transfers

### Layer 5: STORAGE PROTOCOL

Purpose: Share storage across local network

Supports: File sharing , cached websites , game saves

### Layer 6: INTERNET FALLBACK PROTOCOL

Purpose: When local fails, use internet intelligently

Supports: Hybrid apps that work both in the network and on the internet

# 5. <u>VISION</u>
## 🌟 Vision: The Local Internet

We're building towards a complete **local internet stack**:

**Short-term (2026):**
- [ ] Human-readable names (`chat.localnet`)
- [ ] Local service directory
- [ ] Basic file sharing

**Medium-term (2026):**
- [ ] Distributed storage system
- [ ] Web server with .localnet sites
- [ ] Internet fallback gateway

**Long-term (2027+):**
- [ ] Africa-wide mesh network
- [ ] Bandwidth-sharing economy
- [ ] Alternative to expensive mobile data

# 6. 👥 Get Involved

### For Users
```
1. Run `python main.py` on your device
2. Try our demo chat app: `python examples/chat.py`
3. Report issues or suggest features
```
### For Developers
```bash
# Development setup
git clone https://github.com/yourusername/localmesh
cd localmesh
pip install -r requirements-dev.txt
python -m pytest tests/
```
### For Researchers/Investors

Contact us about:

Deployment in African communities

Integration with local ISPs

Grant opportunities

# 7. <u>FAQ</u>
```markdown
## ❓ FAQ

Q: Does this need internet to start?**  
A: No! Works completely offline on local networks.

Q: Is this secure?
A: Currently basic trust model. Encryption planned for v0.5.

Q: How many devices can connect?
A: Tested with 50+ devices. Theoretically thousands.

Q: Can I run this on Raspberry Pi? 
A: Yes! Perfect for low-cost community hubs.
```

# 8. <u>LICENSE & CONTACT</u>

## 📄 License
MIT License - see [LICENSE](LICENSE) file.

## 📞 Contact
- GitHub Issues: [Report bugs](https://github.com/yourusername/localmesh/issues)
- Email: your-galacticaconsolidated@gmail.com
- Twitter: [@LocalMeshNet](https://twitter.com/LocalMeshNet)

---

**Made with ❤️ & 💪 in Kenya, for the world.**

Project Structure
/network_table.py - Node registry with health tracking
/discovery.py - Device discovery via UDP broadcast
/message.py - Reliable messaging with ACK system
/role_routing.py - Send messages to nodes by role
/main.py - Entry point, starts all services









