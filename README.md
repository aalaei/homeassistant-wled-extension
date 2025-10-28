# **WLED Extension Integration for Home Assistant**

This custom integration extends the official [WLED integration](https://www.home-assistant.io/integrations/wled/) by adding **missing or advanced WLED features** not yet available in the core component.  
Currently, it provides support for controlling **Audio Reactive Sync** functionality in WLED — including simple entities to toggle between **Send**, **Receive**, and **Off** modes, and a switch to enable or disable the Audio Reactive feature entirely.

Future updates will continue to expand support for additional WLED extensions and advanced features.

---

## **🚀 Features**

- Adds a **Select Entity** to control Audio Reactive Sync mode:
  - `Send`
  - `Receive`
  - `Off`
- Adds a **Switch Entity** to enable or disable Audio Reactive mode.
- Automatically discovers and extends all configured WLED devices.
- Fully integrates with Home Assistant UI and WLED devices over the network.
- Designed as an **extension** — works seamlessly alongside the official WLED integration.

---

## **🧰 Installation**

### **Option 1: Install via HACS (Recommended)**

If you have [HACS](https://hacs.xyz/) installed, click the button below to add this repository directly:

[![Add Repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=aalaei&repository=homeassistant-wled-extension&category=integration)

After installation, restart Home Assistant.  
Then click below to set it up instantly:

[![Add Integration to Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=wled_extension)

Once added, the integration will automatically discover all of your existing WLED devices and attach extended entities (like Audio Reactive controls).  
It also automatically manages devices added or removed later, keeping everything in sync.

---

#### **Manual Steps (If You Prefer to Add the Repo Yourself)**

1. **Add the Repository**
   - Open **Home Assistant** → **HACS** → **Integrations**.
   - Click the three dots (**⋮**) in the top-right corner → **Custom repositories**.
   - Add your GitLab repository URL (for example):  
     `https://gitlab.com/aalaei/homeassistant-wled-extension`
   - Choose **Integration** as the category.
   - Click **Add**.

2. **Install the Integration**
   - Search for **WLED Extension Integration** in HACS.
   - Click **Download**.
   - Restart Home Assistant.

3. **Set Up (Blue Button Experience)**
   - Go to **Settings** → **Devices & Services**.
   - Click **“Add Integration”** (the blue button).
   - Search for **WLED Extension Integration**.
   - Complete setup — it will auto-discover your WLED devices.

---

### **Option 2: Manual Installation**

1. **Download the Files**
   ```bash
   git clone https://gitlab.com/aalaei/homeassistant-wled-extension.git
