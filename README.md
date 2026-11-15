# RoomControl

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/docs/faq/custom_repositories)

Home Assistant integration for controlling your rooms. RoomControl creates a light for every area in Home Assistant. You configure each room in the RoomControl panel in the sidebar.

## Installation

### HACS (recommended)

1. In Home Assistant, open **HACS**.
2. Open the menu (⋮) in the top right and choose **Custom repositories**.
3. Enter `https://github.com/wizzard722/RoomControl` as the repository and choose **Integration** as the type, then click **Add**.
4. Search for **RoomControl** in HACS, open it and click **Download**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration** and choose **RoomControl**.

### Manual

1. Copy the `custom_components/roomcontrol` folder into the `custom_components` folder of your Home Assistant configuration.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and choose **RoomControl**.

## Usage

After setup, open the **RoomControl** panel in the sidebar to configure each room.

## Issues

Report bugs and feature requests on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).
