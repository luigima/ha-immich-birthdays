# 🎂 Immich Birthdays for Home Assistant

A lightweight Home Assistant custom integration that retrieves birthdays and face avatars from your self-hosted [Immich](https://immich.app/) photo library.

---

## ✨ Features

- **Automated Sync**: Automatically syncs recognized people with `birthDate` set in Immich.
- **Face Avatars**: Exposes each person's cropped face thumbnail as `entity_picture` (via an authenticated local proxy view), without exposing your Immich API key to browser clients.
- **Dedicated Sensor per Person**:
  - State: `Today`, `in 1 day`, `in 5 days`, etc.
  - Attributes: `age`, `next_age`, `birth_date`, `next_birthday`, `days_until`, `is_today`, `is_favorite`.
- **Aggregate Sensor** (`sensor.immich_next_birthdays`):
  - Returns a sorted list of all upcoming birthdays and who is celebrating today.
- **Calendar Entity** (`calendar.immich_birthdays`):
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
   - **Immich Server URL**: e.g., `http://192.168.1.100:2283` or `https://your-immich.example.com`
   - **API Key**: Generated in Immich (*Account Settings → API Keys*)
4. Click **Submit**. All people with birthdays will automatically populate as entities!

---

## 🎴 Bubble Card Examples

### Next Birthday Button with Avatar & Today's Highlight

Display an individual person's birthday using a Bubble Card button. When it's their birthday today, the card pulses with a celebratory golden border:

```yaml
type: custom:bubble-card
card_type: button
entity: sensor.immich_birthday_jane_doe
button_type: state
show_state: true
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

### Horizontal Stack of Upcoming Birthdays

```yaml
type: horizontal-stack
cards:
  - type: custom:bubble-card
    card_type: button
    entity: sensor.immich_birthday_jane_doe
    button_type: state
  - type: custom:bubble-card
    card_type: button
    entity: sensor.immich_birthday_john_doe
    button_type: state
```
