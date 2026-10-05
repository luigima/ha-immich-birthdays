# 🎂 Immich Birthdays for Home Assistant

A lightweight Home Assistant custom integration that retrieves birthdays and face avatars from your self-hosted [Immich](https://immich.app/) photo library.

---

## ✨ Features

- **Automated Sync**: Automatically syncs recognized people with `birthDate` set in Immich.
- **Face Avatars**: Exposes each person's cropped face thumbnail as `entity_picture` (via an authenticated local proxy view), without exposing your Immich API key to browser clients.
- **Dynamic Rank Sensors** (`sensor.upcoming_birthday_1` to `sensor.upcoming_birthday_10`):
  - Chronological slots that automatically represent whoever has the 1st, 2nd, 3rd... upcoming birthday.
  - Dynamically updates name, avatar, age, and countdown — **no need to explicitly list or hardcode individual people** in your dashboards!
- **Aggregate Sensor** (`sensor.next_birthdays`):
  - Returns a sorted list of all upcoming birthdays and who is celebrating today in sensor attributes.
- **Dedicated Sensor per Person**:
  - Individual sensors for each person (`sensor.<name>_birthday`) if you prefer pinning specific individuals.
- **Calendar Entity** (`calendar.birthdays`):
  - Full-day annual recurring events with turning age in the summary.
- **Bubble Card Friendly**: Designed specifically to look stunning on [Bubble Card](https://github.com/Clooos/Bubble-Card) buttons with conditional highlights for birthdays happening today!

---

## 🚀 Installation

### Option 1: Via HACS (Custom Repository)

1. In Home Assistant, open **HACS** → **Integrations**.
2. Click the top-right menu (⋮) → **Custom repositories**.
3. Add your repository URL:
   - Category: **Integration**
4. Click **Download**, then restart Home Assistant.

### Option 2: Manual Installation

1. Copy the `custom_components/immich_birthdays/` directory into your Home Assistant `<config>/custom_components/` folder:
   ```
   config/
   └── custom_components/
       └── immich_birthdays/
           ├── __init__.py
           ├── calendar.py
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── manifest.json
           ├── sensor.py
           ├── strings.json
           ├── view.py
           └── translations/
   ```
2. Restart Home Assistant.

---

## ⚙️ Configuration

1. In Home Assistant, navigate to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **Immich Birthdays**.
3. Fill in your connection details:
   - **Immich Server URL**: e.g., `https://your-immich.example.com` or `http://192.168.1.100:2283`
   - **API Key**: Generated in Immich (*Account Settings → API Keys*)
4. Click **Submit**. All people with birthdays will automatically populate as entities!

### 🔧 Options & Reconfigure
You can update your Immich server URL, API key, and SSL settings at any time:
- Click **Configure** on the integration card to adjust your options.
- Or use Home Assistant's native **Reconfigure** flow if your server URL changes or connection fails.

---

## 🎴 Bubble Card Examples

### Next Upcoming Birthday Button (Dynamic Rank 1)

Display whoever has the next upcoming birthday dynamically. When it's their birthday today, the card pulses with a celebratory golden border:

```yaml
type: custom:bubble-card
card_type: button
entity: sensor.upcoming_birthday_1
button_type: state
show_state: true
show_name: true
show_attribute: false
styles: |
  ${state === 'Today' ? `
    .bubble-button-card {
      background: rgba(255, 193, 7, 0.2) !important;
      border: 2px solid #ffc107 !important;
      animation: pulse 2s infinite;
    }
    .bubble-icon {
      color: #ffc107 !important;
    }
  ` : ''}
```

### Horizontal Stack of Next Upcoming Birthdays

With dynamic rank sensors, you never have to hardcode entity names or reconfigure dashboard cards when birthdays pass:

```yaml
type: horizontal-stack
cards:
  - type: custom:bubble-card
    card_type: button
    entity: sensor.upcoming_birthday_1
    button_type: state
    show_state: true
    show_name: true
  - type: custom:bubble-card
    card_type: button
    entity: sensor.upcoming_birthday_2
    button_type: state
    show_state: true
    show_name: true
  - type: custom:bubble-card
    card_type: button
    entity: sensor.upcoming_birthday_3
    button_type: state
    show_state: true
    show_name: true
```

### Dynamic List with Auto-Entities (Optional)

If you use `auto-entities`, you can automatically list all individual birthdays sorted chronologically:

```yaml
type: custom:auto-entities
card:
  type: entities
  title: 🎂 All Upcoming Birthdays
filter:
  include:
    - entity_id: "sensor.*_birthday"
  exclude:
    - entity_id: "sensor.upcoming_birthday_*"
sort:
  method: attribute
  attribute: days_until
  numeric: true
```
